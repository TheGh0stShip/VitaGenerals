// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef GENERALS_WWSTRING_PLATFORM_H
#define GENERALS_WWSTRING_PLATFORM_H
#include <cstddef>
#include <cwchar>
#include <cstdint>
#include <strings.h>
using TCHAR = char;
using WCHAR = char16_t;
static_assert(sizeof(WCHAR)==2, "Windows wide string units are UTF-16");
#ifndef _cdecl
#define _cdecl
#endif
namespace wwstring_detail {
inline size_t utf16_length(const char16_t *text) { const char16_t *end=text; while(*end)++end; return size_t(end-text); }
}
namespace wwstring_detail {
int utf16_to_ansi(const char16_t *source, char *output, int capacity, bool *unmapped);
}
#endif
