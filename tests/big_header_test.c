/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "big_header.h"
#include <stdio.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "failed at line %d\n", __LINE__); return 1; } } while (0)
int main(void) {
    /* Deliberately unaligned; independent literal mixed-endian fixture. */
    unsigned char b[] = {0, 'B','I','G','F', 0x78,0x56,0x34,0x12,
                        0,0,0,1, 0,0,0,26};
    vg_big_header h = {7,8,9};
    CHECK(vg_big_header_read(b+1,16,UINT32_C(0x12345678),&h));
    CHECK(h.archive_size == UINT32_C(0x12345678) && h.entry_count == 1 && h.directory_end == 26);
    for (size_t n=0;n<16;++n) CHECK(!vg_big_header_read(b+1,n,UINT32_C(0x12345678),&h));
    CHECK(!vg_big_header_read(NULL,16,0,&h));
    CHECK(!vg_big_header_read(b+1,16,UINT32_C(0x12345678),NULL));
    CHECK(!vg_big_header_read(b+1,16,UINT64_C(0x112345678),&h));
    b[1]='X'; CHECK(!vg_big_header_read(b+1,16,UINT32_C(0x12345678),&h)); b[1]='B';
    b[12]=2; CHECK(!vg_big_header_read(b+1,16,UINT32_C(0x12345678),&h)); b[12]=1;
    b[16]=15; CHECK(!vg_big_header_read(b+1,16,UINT32_C(0x12345678),&h));
    b[16]=26; b[13]=0x7f; CHECK(!vg_big_header_read(b+1,16,UINT32_C(0x12345678),&h));
    CHECK(h.directory_end == 26); /* Failure leaves output intact. */
    puts("BIGF boundary tests passed (host validation only)");
    return 0;
}
