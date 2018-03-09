# Copyright (c) Jazel Canseco, 2018
# Licensed under the Apache License, Version 2.0 (the "License")

add_executable(bpfd bpfd.c base64.c remote_perf_reader.c utils.c bpfd_syms.cc)
target_link_libraries(bpfd bpf-static)
target_link_libraries(bpfd bcc-static)
