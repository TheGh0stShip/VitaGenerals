/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "big_header.h"
#include <stdio.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "failed at line %d\n", __LINE__); return 1; } } while (0)
static int directory_tests(void) {
    /* Two records: a two-byte payload and an empty wildcard; one padding byte.
     * The directory is supplied without any payload bytes, at each alignment. */
    const unsigned char fixture[] = {
        'B','I','G','F', 44,0,0,0, 0,0,0,2, 0,0,0,42,
        0,0,0,42, 0,0,0,2, 'a',0,
        0,0,0,0, 0,0,0,0, 'D','a','t','a','\\','*',0,0
    };
    unsigned char storage[sizeof(fixture)+3];
    vg_big_header h;
    for (size_t alignment=0; alignment<4; ++alignment) {
        unsigned char *p = storage+alignment;
        memcpy(p,fixture,sizeof(fixture));
        CHECK(vg_big_directory_validate(p,sizeof(fixture),44,&h));
        CHECK(h.entry_count==2 && h.directory_end==42);
        for (size_t n=0; n<sizeof(fixture); ++n) {
            h.archive_size=99;
            CHECK(!vg_big_directory_validate(p,n,44,&h));
            CHECK(h.archive_size==99);
        }
        p[23]=3; CHECK(!vg_big_directory_validate(p,42,44,&h)); p[23]=2;
        p[19]=41; CHECK(!vg_big_directory_validate(p,42,44,&h)); p[19]=42;
        p[19]=45; CHECK(!vg_big_directory_validate(p,42,44,&h)); p[19]=42;
        memset(p+20,255,4); CHECK(!vg_big_directory_validate(p,42,44,&h));
        memcpy(p,fixture,42);
        memset(p+34,'x',8); CHECK(!vg_big_directory_validate(p,42,44,&h));
        memcpy(p,fixture,42);
        p[11]=3; CHECK(!vg_big_directory_validate(p,42,44,&h));
        memcpy(p,fixture,42);
        p[33]=1; CHECK(!vg_big_directory_validate(p,42,44,&h));
        CHECK(!vg_big_directory_validate(p,42,44,NULL));
    }
    /* The range subtraction must reject wraparound, even at UINT32_MAX. */
    unsigned char large[] = {'B','I','G','F',255,255,255,255,
        0,0,0,1,0,0,0,25,255,255,255,254,0,0,0,2,0};
    CHECK(!vg_big_directory_validate(large,sizeof(large),UINT32_MAX,&h));
    large[23]=1;
    CHECK(vg_big_directory_validate(large,sizeof(large),UINT32_MAX,&h));
    CHECK(!vg_big_directory_validate(large,sizeof(large),UINT64_C(0x1ffffffff),&h));
    return 0;
}
int main(void) {
    CHECK(directory_tests()==0);
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
