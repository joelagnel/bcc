#!/usr/bin/env python
#
# syscount   Summarize syscall counts and latencies.
#
# USAGE: syscount [-p PID] [-i INTERVAL] [-T TOP] [-x] [-L] [-m] [-P] [-l]
#
# Copyright 2017, Sasha Goldshtein.
# Licensed under the Apache License, Version 2.0 (the "License")
#
# 15-Feb-2017   Sasha Goldshtein    Created this.

from bcc import BPF
from bcc.utils import printb
from time import sleep, strftime
import argparse
import errno
import itertools
import subprocess
import sys
import platform

if sys.version_info.major < 3:
    izip_longest = itertools.izip_longest
else:
    izip_longest = itertools.zip_longest

#
# Syscall table for Linux x86_64, not very recent.
# Automatically generated from strace/linux/x86_64/syscallent.h using the
# following command:
#
#  cat syscallent.h | awk -F, '{ gsub(/[ \t"}]/, "", $4);
#                                gsub(/[ \t/*]/, "", $5);
#                                print "    "$5": \""$4"\","; }
#                              BEGIN { print "syscalls = {" }
#                              END { print "}" }'
#
syscalls = {
    0: b"read",
    1: b"write",
    2: b"open",
    3: b"close",
    4: b"stat",
    5: b"fstat",
    6: b"lstat",
    7: b"poll",
    8: b"lseek",
    9: b"mmap",
    10: b"mprotect",
    11: b"munmap",
    12: b"brk",
    13: b"rt_sigaction",
    14: b"rt_sigprocmask",
    15: b"rt_sigreturn",
    16: b"ioctl",
    17: b"pread",
    18: b"pwrite",
    19: b"readv",
    20: b"writev",
    21: b"access",
    22: b"pipe",
    23: b"select",
    24: b"sched_yield",
    25: b"mremap",
    26: b"msync",
    27: b"mincore",
    28: b"madvise",
    29: b"shmget",
    30: b"shmat",
    31: b"shmctl",
    32: b"dup",
    33: b"dup2",
    34: b"pause",
    35: b"nanosleep",
    36: b"getitimer",
    37: b"alarm",
    38: b"setitimer",
    39: b"getpid",
    40: b"sendfile",
    41: b"socket",
    42: b"connect",
    43: b"accept",
    44: b"sendto",
    45: b"recvfrom",
    46: b"sendmsg",
    47: b"recvmsg",
    48: b"shutdown",
    49: b"bind",
    50: b"listen",
    51: b"getsockname",
    52: b"getpeername",
    53: b"socketpair",
    54: b"setsockopt",
    55: b"getsockopt",
    56: b"clone",
    57: b"fork",
    58: b"vfork",
    59: b"execve",
    60: b"_exit",
    61: b"wait4",
    62: b"kill",
    63: b"uname",
    64: b"semget",
    65: b"semop",
    66: b"semctl",
    67: b"shmdt",
    68: b"msgget",
    69: b"msgsnd",
    70: b"msgrcv",
    71: b"msgctl",
    72: b"fcntl",
    73: b"flock",
    74: b"fsync",
    75: b"fdatasync",
    76: b"truncate",
    77: b"ftruncate",
    78: b"getdents",
    79: b"getcwd",
    80: b"chdir",
    81: b"fchdir",
    82: b"rename",
    83: b"mkdir",
    84: b"rmdir",
    85: b"creat",
    86: b"link",
    87: b"unlink",
    88: b"symlink",
    89: b"readlink",
    90: b"chmod",
    91: b"fchmod",
    92: b"chown",
    93: b"fchown",
    94: b"lchown",
    95: b"umask",
    96: b"gettimeofday",
    97: b"getrlimit",
    98: b"getrusage",
    99: b"sysinfo",
    100: b"times",
    101: b"ptrace",
    102: b"getuid",
    103: b"syslog",
    104: b"getgid",
    105: b"setuid",
    106: b"setgid",
    107: b"geteuid",
    108: b"getegid",
    109: b"setpgid",
    110: b"getppid",
    111: b"getpgrp",
    112: b"setsid",
    113: b"setreuid",
    114: b"setregid",
    115: b"getgroups",
    116: b"setgroups",
    117: b"setresuid",
    118: b"getresuid",
    119: b"setresgid",
    120: b"getresgid",
    121: b"getpgid",
    122: b"setfsuid",
    123: b"setfsgid",
    124: b"getsid",
    125: b"capget",
    126: b"capset",
    127: b"rt_sigpending",
    128: b"rt_sigtimedwait",
    129: b"rt_sigqueueinfo",
    130: b"rt_sigsuspend",
    131: b"sigaltstack",
    132: b"utime",
    133: b"mknod",
    134: b"uselib",
    135: b"personality",
    136: b"ustat",
    137: b"statfs",
    138: b"fstatfs",
    139: b"sysfs",
    140: b"getpriority",
    141: b"setpriority",
    142: b"sched_setparam",
    143: b"sched_getparam",
    144: b"sched_setscheduler",
    145: b"sched_getscheduler",
    146: b"sched_get_priority_max",
    147: b"sched_get_priority_min",
    148: b"sched_rr_get_interval",
    149: b"mlock",
    150: b"munlock",
    151: b"mlockall",
    152: b"munlockall",
    153: b"vhangup",
    154: b"modify_ldt",
    155: b"pivot_root",
    156: b"_sysctl",
    157: b"prctl",
    158: b"arch_prctl",
    159: b"adjtimex",
    160: b"setrlimit",
    161: b"chroot",
    162: b"sync",
    163: b"acct",
    164: b"settimeofday",
    165: b"mount",
    166: b"umount",
    167: b"swapon",
    168: b"swapoff",
    169: b"reboot",
    170: b"sethostname",
    171: b"setdomainname",
    172: b"iopl",
    173: b"ioperm",
    174: b"create_module",
    175: b"init_module",
    176: b"delete_module",
    177: b"get_kernel_syms",
    178: b"query_module",
    179: b"quotactl",
    180: b"nfsservctl",
    181: b"getpmsg",
    182: b"putpmsg",
    183: b"afs_syscall",
    184: b"tuxcall",
    185: b"security",
    186: b"gettid",
    187: b"readahead",
    188: b"setxattr",
    189: b"lsetxattr",
    190: b"fsetxattr",
    191: b"getxattr",
    192: b"lgetxattr",
    193: b"fgetxattr",
    194: b"listxattr",
    195: b"llistxattr",
    196: b"flistxattr",
    197: b"removexattr",
    198: b"lremovexattr",
    199: b"fremovexattr",
    200: b"tkill",
    201: b"time",
    202: b"futex",
    203: b"sched_setaffinity",
    204: b"sched_getaffinity",
    205: b"set_thread_area",
    206: b"io_setup",
    207: b"io_destroy",
    208: b"io_getevents",
    209: b"io_submit",
    210: b"io_cancel",
    211: b"get_thread_area",
    212: b"lookup_dcookie",
    213: b"epoll_create",
    214: b"epoll_ctl_old",
    215: b"epoll_wait_old",
    216: b"remap_file_pages",
    217: b"getdents64",
    218: b"set_tid_address",
    219: b"restart_syscall",
    220: b"semtimedop",
    221: b"fadvise64",
    222: b"timer_create",
    223: b"timer_settime",
    224: b"timer_gettime",
    225: b"timer_getoverrun",
    226: b"timer_delete",
    227: b"clock_settime",
    228: b"clock_gettime",
    229: b"clock_getres",
    230: b"clock_nanosleep",
    231: b"exit_group",
    232: b"epoll_wait",
    233: b"epoll_ctl",
    234: b"tgkill",
    235: b"utimes",
    236: b"vserver",
    237: b"mbind",
    238: b"set_mempolicy",
    239: b"get_mempolicy",
    240: b"mq_open",
    241: b"mq_unlink",
    242: b"mq_timedsend",
    243: b"mq_timedreceive",
    244: b"mq_notify",
    245: b"mq_getsetattr",
    246: b"kexec_load",
    247: b"waitid",
    248: b"add_key",
    249: b"request_key",
    250: b"keyctl",
    251: b"ioprio_set",
    252: b"ioprio_get",
    253: b"inotify_init",
    254: b"inotify_add_watch",
    255: b"inotify_rm_watch",
    256: b"migrate_pages",
    257: b"openat",
    258: b"mkdirat",
    259: b"mknodat",
    260: b"fchownat",
    261: b"futimesat",
    262: b"newfstatat",
    263: b"unlinkat",
    264: b"renameat",
    265: b"linkat",
    266: b"symlinkat",
    267: b"readlinkat",
    268: b"fchmodat",
    269: b"faccessat",
    270: b"pselect6",
    271: b"ppoll",
    272: b"unshare",
    273: b"set_robust_list",
    274: b"get_robust_list",
    275: b"splice",
    276: b"tee",
    277: b"sync_file_range",
    278: b"vmsplice",
    279: b"move_pages",
    280: b"utimensat",
    281: b"epoll_pwait",
    282: b"signalfd",
    283: b"timerfd_create",
    284: b"eventfd",
    285: b"fallocate",
    286: b"timerfd_settime",
    287: b"timerfd_gettime",
    288: b"accept4",
    289: b"signalfd4",
    290: b"eventfd2",
    291: b"epoll_create1",
    292: b"dup3",
    293: b"pipe2",
    294: b"inotify_init1",
    295: b"preadv",
    296: b"pwritev",
    297: b"rt_tgsigqueueinfo",
    298: b"perf_event_open",
    299: b"recvmmsg",
    300: b"fanotify_init",
    301: b"fanotify_mark",
    302: b"prlimit64",
    303: b"name_to_handle_at",
    304: b"open_by_handle_at",
    305: b"clock_adjtime",
    306: b"syncfs",
    307: b"sendmmsg",
    308: b"setns",
    309: b"getcpu",
    310: b"process_vm_readv",
    311: b"process_vm_writev",
    312: b"kcmp",
    313: b"finit_module",
}

# Try to use ausyscall if it is available, because it can give us an up-to-date
# list of syscalls for various architectures, rather than the x86-64 hardcoded
# list above.
def parse_syscall(line):
    parts = line.split()
    return (int(parts[0]), parts[1].strip())

try:
    # Skip the first line, which is a header. The rest of the lines are simply
    # SYSCALL_NUM\tSYSCALL_NAME pairs.
    out = subprocess.check_output('ausyscall --dump | tail -n +2', shell=True)
    syscalls = dict(map(parse_syscall, out.strip().split(b'\n')))
except Exception as e:
    if platform.machine() == "x86_64":
        pass
    else:
        raise Exception("ausyscall: command not found")


def handle_errno(errstr):
    try:
        return abs(int(errstr))
    except ValueError:
        pass

    try:
        return getattr(errno, errstr)
    except AttributeError:
        raise argparse.ArgumentTypeError("couldn't map %s to an errno" % errstr)


parser = argparse.ArgumentParser(
    description="Summarize syscall counts and latencies.")
parser.add_argument("-p", "--pid", type=int, help="trace only this pid")
parser.add_argument("-i", "--interval", type=int,
    help="print summary at this interval (seconds)")
parser.add_argument("-T", "--top", type=int, default=10,
    help="print only the top syscalls by count or latency")
parser.add_argument("-x", "--failures", action="store_true",
    help="trace only failed syscalls (return < 0)")
parser.add_argument("-e", "--errno", type=handle_errno,
    help="trace only syscalls that return this error (numeric or EPERM, etc.)")
parser.add_argument("-L", "--latency", action="store_true",
    help="collect syscall latency")
parser.add_argument("-m", "--milliseconds", action="store_true",
    help="display latency in milliseconds (default: microseconds)")
parser.add_argument("-P", "--process", action="store_true",
    help="count by process and not by syscall")
parser.add_argument("-l", "--list", action="store_true",
    help="print list of recognized syscalls and exit")
parser.add_argument("--ebpf", action="store_true",
    help=argparse.SUPPRESS)
args = parser.parse_args()

if args.list:
    for grp in izip_longest(*(iter(sorted(syscalls.values())),) * 4):
        print("   ".join(["%-20s" % s for s in grp if s is not None]))
    sys.exit(0)

text = """
#ifdef LATENCY
struct data_t {
    u64 count;
    u64 total_ns;
};

BPF_HASH(start, u64, u64);
BPF_HASH(data, u32, struct data_t);
#else
BPF_HASH(data, u32, u64);
#endif

#ifdef LATENCY
TRACEPOINT_PROBE(raw_syscalls, sys_enter) {
    u64 pid_tgid = bpf_get_current_pid_tgid();

#ifdef FILTER_PID
    if (pid_tgid >> 32 != FILTER_PID)
        return 0;
#endif

    u64 t = bpf_ktime_get_ns();
    start.update(&pid_tgid, &t);
    return 0;
}
#endif

TRACEPOINT_PROBE(raw_syscalls, sys_exit) {
    u64 pid_tgid = bpf_get_current_pid_tgid();

#ifdef FILTER_PID
    if (pid_tgid >> 32 != FILTER_PID)
        return 0;
#endif

#ifdef FILTER_FAILED
    if (args->ret >= 0)
        return 0;
#endif

#ifdef FILTER_ERRNO
    if (args->ret != -FILTER_ERRNO)
        return 0;
#endif

#ifdef BY_PROCESS
    u32 key = pid_tgid >> 32;
#else
    u32 key = args->id;
#endif

#ifdef LATENCY
    struct data_t *val, zero = {};
    u64 *start_ns = start.lookup(&pid_tgid);
    if (!start_ns)
        return 0;

    val = data.lookup_or_init(&key, &zero);
    val->count++;
    val->total_ns = bpf_ktime_get_ns() - *start_ns;
#else
    u64 *val, zero = 0;
    val = data.lookup_or_init(&key, &zero);
    ++(*val);
#endif
    return 0;
}
"""

if args.pid:
    text = ("#define FILTER_PID %d\n" % args.pid) + text
if args.failures:
    text = "#define FILTER_FAILED\n" + text
if args.errno:
    text = "#define FILTER_ERRNO %d\n" % abs(args.errno) + text
if args.latency:
    text = "#define LATENCY\n" + text
if args.process:
    text = "#define BY_PROCESS\n" + text
if args.ebpf:
    print(text)
    exit()

bpf = BPF(text=text)

def print_stats():
    if args.latency:
        print_latency_stats()
    else:
        print_count_stats()

agg_colname = "PID    COMM" if args.process else "SYSCALL"
time_colname = "TIME (ms)" if args.milliseconds else "TIME (us)"

def agg_colval(key):
    if args.process:
        return b"%-6d %-15s" % (key.value, bpf.comm_for_pid(key.value))
    else:
        return syscalls.get(key.value, b"[unknown: %d]" % key.value)

def print_count_stats():
    data = bpf["data"]
    print("[%s]" % strftime("%H:%M:%S"))
    print("%-22s %8s" % (agg_colname, "COUNT"))
    for k, v in sorted(data.items(), key=lambda kv: -kv[1].value)[:args.top]:
        if k.value == 0xFFFFFFFF:
            continue    # happens occasionally, we don't need it
        printb(b"%-22s %8d" % (agg_colval(k), v.value))
    print("")
    data.clear()

def print_latency_stats():
    data = bpf["data"]
    print("[%s]" % strftime("%H:%M:%S"))
    print("%-22s %8s %16s" % (agg_colname, "COUNT", time_colname))
    for k, v in sorted(data.items(),
                       key=lambda kv: -kv[1].total_ns)[:args.top]:
        if k.value == 0xFFFFFFFF:
            continue    # happens occasionally, we don't need it
        printb((b"%-22s %8d " + (b"%16.6f" if args.milliseconds else b"%16.3f")) %
               (agg_colval(k), v.count,
                v.total_ns / (1e6 if args.milliseconds else 1e3)))
    print("")
    data.clear()

print("Tracing %ssyscalls, printing top %d... Ctrl+C to quit." %
      ("failed " if args.failures else "", args.top))
while True:
    try:
        sleep(args.interval or 999999999)
        print_stats()
    except KeyboardInterrupt:
        if not args.interval:
            print_stats()
        break
