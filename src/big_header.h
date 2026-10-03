/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef VITA_GENERALS_BIG_HEADER_H
#define VITA_GENERALS_BIG_HEADER_H
#include <stddef.h>
#include <stdint.h>
typedef struct {
    uint32_t archive_size;
    uint32_t entry_count;
    uint32_t directory_end;
} vg_big_header;
/* BIGF mixes a little-endian file size with big-endian directory fields.
 * Input may be unaligned. Returns zero for invalid or truncated headers.
 * This validates the header only, not the directory or its entries. */
int vg_big_header_read(const unsigned char *bytes, size_t length,
                       uint64_t actual_file_size, vg_big_header *out);
/* Validate all entry records using a buffer containing the complete directory.
 * Payload bytes need not be loaded. Names are bounded NUL-terminated bytes;
 * this does not interpret paths, duplicates, wildcard or mount semantics.
 * Empty entries may have offset zero. Nonempty payloads must follow the
 * directory and fit in the archive. Directory padding is permitted.
 * Failure leaves out unchanged. */
int vg_big_directory_validate(const unsigned char *bytes, size_t length,
                              uint64_t actual_file_size, vg_big_header *out);
#endif
