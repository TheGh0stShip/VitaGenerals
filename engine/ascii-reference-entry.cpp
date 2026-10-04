// SPDX-License-Identifier: GPL-3.0-or-later
#include "PreRTS.h"
#include "Common/AsciiString.h"
#include "Common/CriticalSection.h"
#include <vector>
#include <cstring>
#include <cstdlib>
#if !defined(__vita__)
#include <thread>
#include <atomic>
#endif
static void check(bool value) { if (!value) std::abort(); }
int main() {
    initMemoryManager();
    AsciiString source("shared payload");
    std::vector<AsciiString> owners;
    owners.reserve(65534);
    for (unsigned i=0; i<65534; ++i) owners.emplace_back(source);
    AsciiString overflow(source), second(source);
    second.clear();
    check(std::strcmp(source.str(),"shared payload")==0);
    overflow.concat(" extra");
    check(std::strcmp(source.str(),"shared payload")==0);
    owners.front().set(source);
    owners.front().concat(" changed");
    check(std::strcmp(source.str(),"shared payload")==0);
    owners.clear();
    source.concat(" retained");
    check(std::strcmp(source.str(),"shared payload retained")==0);
#if !defined(__vita__)
    CriticalSection dmaMutex, poolMutex;
    TheDmaCriticalSection=&dmaMutex;
    TheMemoryPoolCriticalSection=&poolMutex;
    for (unsigned cycle=0; cycle<512; ++cycle) {
        AsciiString seed("final owners");
        AsciiString first(seed), last(seed);
        seed.clear();
        std::atomic<bool> ready(false);
        std::thread worker([&]{while (!ready.load(std::memory_order_acquire)) {} first.clear();});
        ready.store(true,std::memory_order_release);
        last.clear();
        worker.join();
    }
    AsciiString stable("thread shared");
    std::vector<std::thread> workers;
    for (unsigned i=0;i<4;++i) workers.emplace_back([&]{
        for (unsigned n=0;n<10000;++n) {
            AsciiString copy(stable);
            AsciiString assigned("old");
            assigned=copy;
            check(std::strcmp(assigned.str(),"thread shared")==0);
        }
    });
    for(auto& worker:workers) worker.join();
    check(std::strcmp(stable.str(),"thread shared")==0);
    TheDmaCriticalSection=nullptr;
    TheMemoryPoolCriticalSection=nullptr;
#endif
}
