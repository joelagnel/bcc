#!/usr/bin/env python
# Copyright (c) Jazel Canseco, 2018
# Licensed under the Apache License, Version 2.0 (the "License")

import os
import subprocess

from unittest import main, skipUnless, TestCase
from test_tools_smoke import ToolTestRunner

class RemoteTests(TestCase, ToolTestRunner):

    def setUp(self):
        self.set_up_env_to_run_tools_on_remote()

    def set_up_env_to_run_tools_on_remote(self):
        bpfd_dir = "../../build/src/cc/bpfd"
        os.environ["PATH"] += os.pathsep + bpfd_dir

        os.environ["ARCH"] = "x86"
        os.environ["BCC_REMOTE"] = "shell"

    def test_biolatency(self):
        self.run_with_duration("biolatency.py 1 1")

    def test_cachestat(self):
        self.run_with_duration("cachestat.py 1 1")

    def test_filetop(self):
        self.run_with_duration("filetop.py 1 1")

    def test_hardirqs(self):
        self.run_with_duration("hardirqs.py 1 1")

    def test_offcputime(self):
        self.run_with_duration("offcputime.py 1")

    def test_opensnoop(self):
        self.run_with_int("opensnoop.py")

    def test_stackcount(self):
        self.run_with_int("stackcount.py __kmalloc -i 1")

if __name__ == "__main__":
    main()
