#!/usr/bin/python
#
# By Joel Fernandes <joel@linuxinternals.org>
#

from __future__ import print_function
from bcc import BPF
import argparse
import ctypes as ct

bpf_text = """
#include <uapi/linux/ptrace.h>
#include <uapi/linux/limits.h>
#include <linux/sched.h>

struct data_t {
    u64 time;
    u64 stack_id;
    u32 cpu;
    u64 id;
    char comm[TASK_COMM_LEN];
};

BPF_STACK_TRACE(stack_traces, 1024);
BPF_PERCPU_ARRAY(sts, u64, 1);
BPF_PERF_OUTPUT(events);

TRACEPOINT_PROBE(preemptirq, irq_disable)
{
    int idx = 0;
    u64 ts = bpf_ktime_get_ns();

    sts.update(&idx, &ts);
    return 0;
}

TRACEPOINT_PROBE(preemptirq, irq_enable)
{
    int idx = 0;
    u64 *s, start_ts, end_ts, diff;

    end_ts = bpf_ktime_get_ns();

    s = sts.lookup(&idx);
    bpf_probe_read(&start_ts, sizeof(u64), s);

    if (start_ts > end_ts) {
        bpf_trace_printk("ERROR: start < end\\n");
        return 0;
    }

    diff = end_ts - start_ts;
    if (diff < 1000000)
        return 0;

    u64 id = bpf_get_current_pid_tgid();
    struct data_t data = {};

    if (bpf_get_current_comm(&data.comm, sizeof(data.comm)) == 0) {
        data.id = id;
        data.stack_id = stack_traces.get_stackid(args, BPF_F_REUSE_STACKID);
        data.time = diff;
        data.cpu = bpf_get_smp_processor_id();
        events.perf_submit(args, &data, sizeof(data));
    } else {
        bpf_trace_printk("ERROR: Couldn't get process name\\n");
    }

    return 0;
}
"""

b = BPF(text=bpf_text)

TASK_COMM_LEN = 16    # linux/sched.h

class Data(ct.Structure):
    _fields_ = [
        ("time", ct.c_ulonglong),
        ("stack_id", ct.c_ulonglong),
        ("cpu", ct.c_int),
        ("id", ct.c_ulonglong),
        ("comm", ct.c_char * TASK_COMM_LEN),
    ]

def filter_idle_frames(kstack):
    syms = []
    for addr in kstack:
        s = b.ksym(addr, show_offset=True)
        if 'cpuidle' in s:
            return []
        syms.append(s)
    return syms

# process event
def print_event(cpu, data, size):
    global b
    event = ct.cast(data, ct.POINTER(Data)).contents
    stack_traces = b["stack_traces"]

    if event.stack_id < 0:
        print("Empty kernel stack received\n")
        return

    kstack = stack_traces.walk(event.stack_id)

    syms = filter_idle_frames(kstack)
    if not syms:
        return

    print("===================================")
    print("TASK: %s (pid %5d tid %5d) Total Time: %-9.3fus\n\n" % (event.comm.decode(), (event.id >> 32), (event.id & 0xffffffff), float(event.time) / 1000), end="")
    print("Stack Dump on exit from Critical Section:")
    for s in syms:
        print("  ", end="")
        print("%s" % s)
    print("===================================")
    print("")

b["events"].open_perf_buffer(print_event, page_cnt=256)
while 1:
    b.perf_buffer_poll();

