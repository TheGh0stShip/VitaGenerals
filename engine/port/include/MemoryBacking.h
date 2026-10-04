// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstddef>
namespace memory_backing {
// Called beneath the original global new override. Providers must allocate
// directly from the platform heap, without entering the engine allocator.
void* allocate(std::size_t bytes) noexcept;
void release(void* pointer) noexcept;
}
