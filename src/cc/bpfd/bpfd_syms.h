/*
 * BPFd (Berkeley Packet Filter daemon)
 * This header is only supposed to be used by bpfd.c
 *
 * Copyright (C) 2018 Jazel Canseco <jcanseco@google.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "bcc_syms.h"

#ifdef __cplusplus
extern "C" {
#endif

void *bpfd_syms_create_symresolver();
int bpfd_syms_resolve_addr(void *sym_resolver, int pid, uint64_t addr,
                           struct bcc_symbol *sym);
int bpfd_syms_resolve_addr_no_demangle(void *sym_resolver, int pid,
                                       uint64_t addr, struct bcc_symbol *sym);
int bpfd_syms_resolve_name(void *sym_resolver, int pid, const char *module,
                           const char *name, uint64_t *addr);

#ifdef __cplusplus
}
#endif
