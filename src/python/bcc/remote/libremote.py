# Copyright 2017 Joel Fernandes <joelaf@google.com>
# Module to establish and maintain a remote connection
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import base64
import re
import ctypes as ct
from shell import ShellRemote
from adb import AdbRemote

def get_remote_cls(cls_name):
    cls_name = cls_name.capitalize() + 'Remote'
    cls = globals()[cls_name]
    return cls

class LibRemote(object):
    def __init__(self, remote_name, remote_arg=None):
        # Get the <class>Remote class object
        cls = get_remote_cls(remote_name)

        # Cache of maps, format: map_cache[map_fd] = { 'key1': 'value1', .. }
        self.nkey_cache = {}
        self.map_cache = {}
        # Has the map been fully dumped once before the last delete/clear ?
        # format: { map_fd: [True|False] }
        self.map_dumped = {}

        # Create the remote connection
        self.remote = cls(remote_arg)

    def _remote_send_command(self, cmd):
        """
        Return: a tuple containing return code and output list.
        """
        ret = self.remote.send_command(cmd)
        if not ret:
            return (-1, [])

        if ret[0].startswith('Command not recognized'):
            print('Command not recognized! cmd: {}'.format(cmd))
            return (-1, [])

        # Assume success if first list element doesn't have ret=
        if not 'ret=' in ret[0]:
            return (0, ret)

        m = re.search("ret=(\-?\d+)", ret[0])
        if m == None:
            print('Bad return string for cmd {}'.format(cmd))
            return (-1, [])

        return (int(m.group(1)), ret)

    def _invalidate_map_cache(self, map_fd):
        self.map_cache[map_fd] = {}
        self.nkey_cache[map_fd] = {}
        self.map_dumped[map_fd] = {}

    def available_filter_functions(self, tracefs):
        cmd = "GET_AVAIL_FILTER_FUNCS {}".format(tracefs)
        ret = self._remote_send_command(cmd)
        return ret[0] if ret[0] < 0 else ret[1]

    def kprobes_blacklist(self, tracefs):
        cmd = "GET_KPROBES_BLACKLIST {}".format(tracefs)
        ret = self._remote_send_command(cmd)
        return ret[0] if ret[0] < 0 else ret[1]

    def get_trace_events(self, tracefs, cat):
        cmd = "GET_TRACE_EVENTS {} {}".format(tracefs, cat)
        ret = self._remote_send_command(cmd)
        return ret[0] if ret[0] < 0 else ret[1]

    def get_trace_events_categories(self, tracefs):
        cmd = "GET_TRACE_EVENTS_CATEGORIES {}".format(tracefs)
        ret = self._remote_send_command(cmd)
        return ret[0] if ret[0] < 0 else ret[1]

    def bpf_attach_tracepoint(self, fd, cat, tpname):
        cmd = "BPF_ATTACH_TRACEPOINT {} {} {}".format(fd, cat, tpname)
        ret = self._remote_send_command(cmd)
        return ret[0]

    def bpf_attach_kprobe(self, fd, t, evname, fnname):
        cmd = "BPF_ATTACH_KPROBE {} {} {} {}".format(fd, t, evname, fnname)
        ret = self._remote_send_command(cmd)
        return ret[0]

    def bpf_detach_kprobe(self, evname):
        # this is hard to do since a signal needs to be delivered if
        # bpfd is sleeping. For now do nothing
        return 0

        # At this point just restart the connection
        # to kill bpfd which may be sleeping
        self.remote.close_connection()
        self.__init__(self.remote_name, self.remote_arg)
        cmd = "BPF_DETACH_KPROBE {} 0".format(evname)
        ret = self._remote_send_command(cmd)
        return 0

    def bpf_attach_uprobe(self, fd, t, evname, binpath, offset, pid):
        cmd = "BPF_ATTACH_UPROBE {} {} {} {} {} {}".format(fd, t, evname, binpath, offset, pid)
        ret = self._remote_send_command(cmd)
        return ret[0]

    def bpf_detach_uprobe(self, evname):
        # this is hard to do since a signal needs to be delivered if
        # bpfd is sleeping. For now do nothing
        return 0

        # At this point just restart the connection
        # to kill bpfd which may be sleeping
        self.remote.close_connection()
        self.__init__(self.remote_name, self.remote_arg)
        cmd = "BPF_DETACH_UPROBE {} 0".format(evname)
        ret = self._remote_send_command(cmd)
        return 0

    def bpf_prog_load(self, prog_type, name, func_str, license_str, kern_version):
        cmd = "BPF_PROG_LOAD {} {} {} {} {} {}".format(prog_type, name, len(func_str),
              license_str, kern_version, base64.b64encode(func_str))
        ret = self._remote_send_command(cmd)
        return ret[0]

    def bpf_create_map(self, map_type, name, key_size, leaf_size, max_entries,
                       flags):
        cmd = "BPF_CREATE_MAP {} {} {} {} {} {}".format(map_type, name, key_size,
                                    leaf_size, max_entries, flags)
        ret = self._remote_send_command(cmd)

        if ret[0] > 0:
            self.map_cache[ret[0]] = {}
            self.nkey_cache[ret[0]] = {}
        return ret[0]

    def bpf_update_elem(self, map_fd, kstr, klen, lstr, llen, flags):
        cmd = "BPF_UPDATE_ELEM {} {} {} {} {} {}".format(map_fd, kstr, klen,
                                                         lstr, llen, flags)
        ret = self._remote_send_command(cmd)
        return ret[0]

    def bpf_lookup_elem(self, map_fd, kstr, klen, llen):
        if map_fd in self.map_cache:
            if kstr in self.map_cache[map_fd]:
                return (0, [self.map_cache[map_fd][kstr]])

        # Some maps like StackTrace may not trigger a get_first_key before lookup
        # since the keys can be obtained through other maps (like counts in offcputime)
        # Force a get_first_key so that the entire map is cached.
        if map_fd not in self.map_dumped or self.map_dumped[map_fd] == False:
            self.bpf_get_first_key(map_fd, klen, llen, dump_all=True)

        cmd = "BPF_LOOKUP_ELEM {} {} {} {}".format(map_fd, kstr, klen, llen)
        ret = self._remote_send_command(cmd)
        return ret

    def bpf_open_perf_buffer(self, pid, cpu, page_cnt):
        cmd = "BPF_OPEN_PERF_BUFFER {} {} {}".format(pid, cpu, page_cnt)
        ret = self._remote_send_command(cmd)
        return ret[0]

    def bpf_get_first_key(self, map_fd, klen, vlen, dump_all=True):
        cmd = "BPF_GET_FIRST_KEY {} {} {} {}".format(map_fd, klen, vlen, 1 if dump_all else 0)
        ret = self._remote_send_command(cmd)

        if not dump_all or ret[0] < 0:
            return ret

        # bpfd will dump the entire map on first get key so it can be
        # cached for future use
        key_values = ret[1]
        first_key = key_values[0]

        it = iter(key_values)
        prev_key = None
        for i in it:
            key = i
            if not key:
                continue
            value = next(it)
            self.map_cache[map_fd][key] = value
            if prev_key:
                self.nkey_cache[map_fd][prev_key] = key
            prev_key = key

        self.map_dumped[map_fd] = True

        return (0, [first_key])

    def bpf_get_next_key(self, map_fd, kstr, klen):
        if map_fd in self.nkey_cache:
            if kstr in self.nkey_cache[map_fd]:
                return (0, [self.nkey_cache[map_fd][kstr]])

        cmd = "BPF_GET_NEXT_KEY {} {} {}".format(map_fd, kstr, klen)
        ret = self._remote_send_command(cmd)
        return ret

    def bpf_delete_elem(self, map_fd, kstr, klen):
        cmd = "BPF_DELETE_ELEM {} {} {}".format(map_fd, kstr, klen)
        ret = self._remote_send_command(cmd)
        self._invalidate_map_cache(map_fd)
        return ret[0]

    def bpf_clear_map(self, map_fd, klen):
        cmd = "BPF_CLEAR_MAP {} {}".format(map_fd, klen)
        ret = self._remote_send_command(cmd)
        self._invalidate_map_cache(map_fd)
        return ret[0]

    def perf_reader_poll(self, fd_callbacks, timeout):
        cmd = ""
        fd_cb_dict = {}
        for f in fd_callbacks:
            cmd += " {}".format(f[0])
            fd_cb_dict[f[0]] = f[1]
        cmd = "PERF_READER_POLL {} {}".format(timeout, len(fd_callbacks)) + cmd
        ret = self._remote_send_command(cmd)
        if ret[0] < 0:
            return ret[0]

        for out in ret[1]:
            # Format: <fd> <len> <base64 data>
            (fd, size, data_str) = out.split(" ")
            fd = int(fd)
            size = int(size)

            data_bin = ct.c_char_p(base64.b64decode(data_str))
            data_bin = ct.cast(data_bin, ct.c_void_p)
            cbs = fd_cb_dict[fd]

            raw_cb = cbs[0]
            lost_cb = cbs[1]

            # TODO: implement lost cbs too
            raw_cb(ct.cast(id(self), ct.py_object), data_bin, ct.c_int(size))

    def ksym(self, addr):
        cmd = "GET_KSYM_NAME {} 0".format(addr)
        ret = self._remote_send_command(cmd)

        ret_code = ret[0]
        if ret_code < 0:
            return None, addr, None
        else:
            name, offset, module = ret[1][1].split(";")
            return name, offset, module

    def close_connection(self):
        self.remote.close_connection()

# Test
# libremote = LibRemote('shell')

