/*
 * BPFd (Berkeley Packet Filter daemon)
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

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <unordered_map>

#include "syms.h"
#include "bpfd_syms.h"

class SymbolResolver {
  std::unordered_map<int, void *> sym_caches;

public:
  int resolve_addr(int pid, uint64_t addr, struct bcc_symbol *sym,
                   bool demangle = true);
  int resolve_name(int pid, const char *module, const char *name,
                   uint64_t *addr);
};

int SymbolResolver::resolve_addr(int pid, uint64_t addr, struct bcc_symbol *sym,
                                 bool demangle) {
  if (sym_caches.find(pid) == sym_caches.end())
    sym_caches[pid] = bcc_symcache_new(pid, NULL);

  if (demangle)
    return bcc_symcache_resolve(sym_caches[pid], addr, sym);
  else
    return bcc_symcache_resolve_no_demangle(sym_caches[pid], addr, sym);
}

int SymbolResolver::resolve_name(int pid, const char *module, const char *name,
                                uint64_t *addr) {
  if (sym_caches.find(pid) == sym_caches.end())
    sym_caches[pid] = bcc_symcache_new(pid, NULL);

  return bcc_symcache_resolve_name(sym_caches[pid], module, name, addr);
}

extern "C" {

void *bpfd_syms_create_symresolver() {
  return static_cast<void *>(new SymbolResolver());
}

int bpfd_syms_resolve_addr(void *sym_resolver, int pid, uint64_t addr,
                           struct bcc_symbol *sym) {
  SymbolResolver *resolver = static_cast<SymbolResolver *>(sym_resolver);
  return resolver->resolve_addr(pid, addr, sym);
}

int bpfd_syms_resolve_addr_no_demangle(void *sym_resolver, int pid,
                                       uint64_t addr, struct bcc_symbol *sym) {
  SymbolResolver *resolver = static_cast<SymbolResolver *>(sym_resolver);
  return resolver->resolve_addr(pid, addr, sym, false);
}

int bpfd_syms_resolve_name(void *sym_resolver, int pid, const char *module,
                           const char *name, uint64_t *addr) {
  SymbolResolver *resolver = static_cast<SymbolResolver *>(sym_resolver);
  return resolver->resolve_name(pid, module, name, addr);
}

}
