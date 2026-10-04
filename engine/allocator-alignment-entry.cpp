// SPDX-License-Identifier: GPL-3.0-or-later
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <climits>
#include <initializer_list>
#include "PreRTS.h"
#include "Common/CriticalSection.h"
#if defined(__arm__)
static_assert(sizeof(void*) == 4 && sizeof(long) == 4, "Vita ILP32 prerequisite");
static_assert(alignof(std::max_align_t) == 8, "Reviewed SDK allocator alignment");
#endif
static void require(bool value) { if (!value) std::abort(); }
int main() {
    initMemoryManager();
    {
        CriticalSection lock;
        ScopedCriticalSection outer(&lock);
        ScopedCriticalSection inner(&lock);
    }
    const size_t oversized[] = {static_cast<size_t>(INT_MAX) + 1,
                               static_cast<size_t>(-1)};
    for (size_t bytes : oversized) {
        for (unsigned route = 0; route < 5; ++route) {
            bool rejected = false;
            try {
                void* unexpected = nullptr;
                if (route == 0) unexpected = ::operator new(bytes);
                if (route == 1) unexpected = ::operator new[](bytes);
                if (route == 2) unexpected = ::operator new(bytes, "size-check", 1);
                if (route == 3) unexpected = ::operator new[](bytes, "size-check", 1);
                if (route == 4) unexpected = STLSpecialAlloc::allocate(bytes);
                TheDynamicMemoryAllocator->freeBytes(unexpected);
            } catch (...) { rejected = true; }
            require(rejected);
        }
    }
    bool rejectedNegative = false;
    try { TheDynamicMemoryAllocator->allocateBytesDoNotZero(-1, "negative-check"); }
    catch (...) { rejectedNegative = true; }
    require(rejectedNegative);
    // Preserve the original zero-size route: a nonnull small-pool block.
    void* zero = ::operator new(0);
    require(zero != nullptr);
    ::operator delete(zero);
    for (int size : {INT_MAX, INT_MAX - 1, INT_MAX - 3, INT_MAX - 15}) {
        bool rejected = false;
        try {
            void* unexpected = TheDynamicMemoryAllocator->allocateBytesDoNotZero(size, "overflow-check");
            TheDynamicMemoryAllocator->freeBytes(unexpected);
        } catch (...) { rejected = true; }
        require(rejected);
    }
    MemoryPool* small = TheMemoryPoolFactory->createMemoryPool("AlignmentFourBytePool", 4, 4, 4);
    require(small->getAllocationSize() == 4);
    void* blocks[8];
    for (unsigned i = 0; i < 8; ++i) {
        blocks[i] = small->allocateBlock("alignment");
        require(reinterpret_cast<std::uintptr_t>(blocks[i]) % alignof(std::max_align_t) == 0);
        std::memset(blocks[i], i + 1, 4);
    }
    for (void* block : blocks) small->freeBlock(block);
    TheMemoryPoolFactory->destroyMemoryPool(small);
    // Adjacent live allocations exercise each pool's stride, not just backing
    // malloc alignment. Requests above1024 exercise raw large-block recovery.
    const unsigned sizes[] = {1, 4, 8, 15, 16, 17, 31, 32, 33, 63, 64, 65,
                              127, 128, 129, 255, 256, 257, 511, 512, 513,
                              1023, 1024, 1025, 2048};
    for (unsigned size : sizes) {
        unsigned char* pointers[17];
        for (unsigned i = 0; i < 17; ++i) {
            pointers[i] = new unsigned char[size];
            require(reinterpret_cast<std::uintptr_t>(pointers[i]) % alignof(std::max_align_t) == 0);
            std::memset(pointers[i], i + 1, size);
        }
        for (unsigned i = 0; i < 17; ++i) {
            for (unsigned j = 0; j < size; ++j) require(pointers[i][j] == i + 1);
            delete[] pointers[i];
        }
        // Exercise recovered free-list reuse after all adjacent blocks return.
        auto* again = new unsigned char[size];
        require(reinterpret_cast<std::uintptr_t>(again) % alignof(std::max_align_t) == 0);
        delete[] again;
    }
    return 0;
}
