// SPDX-License-Identifier: GPL-3.0-or-later
#include "MemoryBacking.h"
#include <cstdlib>
#if defined(GENERALS_PLATFORM_VITA)
#include <reent.h>
#endif
namespace memory_backing {
void* allocate(std::size_t bytes) noexcept {
#if defined(GENERALS_PLATFORM_VITA)
    return _malloc_r(_REENT, bytes);
#else
    return std::malloc(bytes);
#endif
}
void release(void* pointer) noexcept {
#if defined(GENERALS_PLATFORM_VITA)
    _free_r(_REENT, pointer);
#else
    std::free(pointer);
#endif
}
}
