#!/bin/bash

# BPFd (Berkeley Packet Filter daemon)
#
# Copyright (C) 2018 Jazel Canseco <jcanseco@google.com>
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

# This script pulls the most up-to-date version of the BPFd source files
# from the BPFd repository at https://github.com/joelagnel/bpfd

SCRIPT_DIR=$(cd $(dirname ${BASH_SOURCE[0]}) && pwd) # Gets the script's source dir no matter where the script is called from
BCC_DIR=$(cd $SCRIPT_DIR && git rev-parse --show-toplevel) # Gets the BCC root directory no matter where the script is placed within the BCC tree
BPFD_DIR="${BCC_DIR}/src/cc/bpfd"

git clone https://github.com/joelagnel/bpfd bpfd_temp
printf "\n"

cp -rv bpfd_temp/src/* $BPFD_DIR/

rm -rf bpfd_temp
