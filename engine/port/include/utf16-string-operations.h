#pragma once
#include <cstddef>
#include <cstring>
#include <cstdarg>

namespace legacy_text {
inline std::size_t length(const char16_t* text) noexcept {
    const char16_t* end = text;
    while (*end) ++end;
    return static_cast<std::size_t>(end - text);
}
inline char16_t* copy(char16_t* target, const char16_t* source) noexcept {
    std::memmove(target, source, (length(source) + 1) * sizeof(char16_t));
    return target;
}
inline char16_t* append(char16_t* target, const char16_t* source) noexcept {
    const std::size_t end = length(target);
    const std::size_t count = length(source) + 1;
    std::memmove(target + end, source, count * sizeof(char16_t));
    return target;
}
inline int compare(const char16_t* left, const char16_t* right) noexcept {
    while (*left && *left == *right) { ++left; ++right; }
    return *left < *right ? -1 : (*left > *right ? 1 : 0);
}
inline bool contains(const char16_t* set, char16_t value) noexcept {
    while (*set) { if (*set++ == value) return true; }
    return false;
}
inline std::size_t span(const char16_t* text, const char16_t* set) noexcept {
    std::size_t count = 0;
    while (text[count] && contains(set, text[count])) ++count;
    return count;
}
inline std::size_t complement_span(const char16_t* text, const char16_t* set) noexcept {
    std::size_t count = 0;
    while (text[count] && !contains(set, text[count])) ++count;
    return count;
}
// Providers use explicit original UTF-16 units and a selected legacy locale.
bool is_space(char16_t);
int compare_no_case(const char16_t*, const char16_t*);
int format(char16_t*, std::size_t, const char16_t*, va_list);
static_assert(sizeof(char16_t) == 2, "Original Windows code-unit storage");
}
