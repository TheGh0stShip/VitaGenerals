/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "big_header.h"
#include <limits.h>
_Static_assert(CHAR_BIT == 8, "8-bit bytes required");
_Static_assert(sizeof(uint32_t) == 4, "32-bit archive fields required");
_Static_assert(sizeof(vg_big_header) == 12, "decoded field layout changed");
_Static_assert(offsetof(vg_big_header, directory_end) == 8, "field layout changed");
static uint32_t be32(const unsigned char *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16)
         | ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}
static uint32_t le32(const unsigned char *p) {
    return ((uint32_t)p[3] << 24) | ((uint32_t)p[2] << 16)
         | ((uint32_t)p[1] << 8) | (uint32_t)p[0];
}
int vg_big_header_read(const unsigned char *p, size_t n,
                       uint64_t file_size, vg_big_header *out) {
    vg_big_header h;
    if (!p || !out || n < 16) return 0;
    if (p[0] != 'B' || p[1] != 'I' || p[2] != 'G' || p[3] != 'F') return 0;
    h.archive_size = le32(p + 4);
    h.entry_count = be32(p + 8);
    h.directory_end = be32(p + 12);
    if (file_size != h.archive_size || h.directory_end < 16
        || h.directory_end > h.archive_size) return 0;
    /* Each directory entry needs two 32-bit fields and a name terminator. */
    if (h.entry_count > (h.directory_end - 16) / 9) return 0;
    *out = h;
    return 1;
}
int vg_big_directory_validate(const unsigned char *p, size_t n,
                              uint64_t file_size, vg_big_header *out) {
    vg_big_header h;
    size_t cursor = 16;
    if (!out || !vg_big_header_read(p, n, file_size, &h)
        || n < h.directory_end) return 0;
    for (uint32_t i = 0; i < h.entry_count; ++i) {
        uint32_t offset, size;
        /* Subtraction avoids cursor + record-size overflow on ILP32. */
        if (h.directory_end - cursor < 9) return 0;
        offset = be32(p + cursor);
        size = be32(p + cursor + 4);
        cursor += 8;
        while (cursor < h.directory_end && p[cursor] != 0) ++cursor;
        if (cursor == h.directory_end) return 0;
        ++cursor;
        if (offset > h.archive_size || size > h.archive_size - offset
            || (size != 0 && offset < h.directory_end)) return 0;
    }
    *out = h;
    return 1;
}
