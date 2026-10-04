// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
#include <cstring>
namespace allocator_detail {
inline std::int32_t read_wall_word(const void* source) noexcept {
    std::int32_t word;
    std::memcpy(&word, source, sizeof(word));
    return word;
}
inline void write_wall_word(void* target, std::int32_t word) noexcept {
    std::memcpy(target, &word, sizeof(word));
}
}
