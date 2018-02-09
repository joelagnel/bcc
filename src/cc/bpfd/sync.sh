#!/bin/bash

# This script synchronizes the BPFd source files with the BPFd repository by
# copying over the relevant files. 

git clone https://github.com/joelagnel/bpfd.git

cp bpfd/src/* .

rm -rf bpfd
