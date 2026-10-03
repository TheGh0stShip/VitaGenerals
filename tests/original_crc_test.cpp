/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "realcrc.h"
#include <cstdint>
#include <cstdio>
#include <clocale>
#include <type_traits>
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"CRC failure at line %d\n",__LINE__); return 1; } } while (0)
static_assert(std::is_same<decltype(CRC_Memory(nullptr,0)),uint32_t>::value,
              "Original 32-bit checksum API must not widen on LP64 hosts");
static uint32_t oracle(const unsigned char *bytes, unsigned length, uint32_t prior=0) {
    uint32_t crc=prior^UINT32_C(0xffffffff);
    for (unsigned i=0;i<length;++i) {
        crc^=bytes[i];
        for (unsigned bit=0;bit<8;++bit)
            crc=(crc>>1)^((crc&1)?UINT32_C(0xedb88320):0);
    }
    return crc^UINT32_C(0xffffffff);
}
int main() {
    CHECK(std::setlocale(LC_CTYPE,"C") != nullptr);
    CHECK(CRC_String("")==0);
    CHECK(CRC_Stringi("")==0);
    const unsigned char known[]="123456789";
    CHECK(CRC_Memory(known,9)==UINT32_C(0xcbf43926));
    CHECK(CRC_String("123456789")==UINT32_C(0xcbf43926));
    CHECK(CRC_Memory(nullptr,0,UINT32_C(0xfedcba98))==UINT32_C(0xfedcba98));
    CHECK(CRC_Stringi("aBcZ_09")==CRC_String("ABCZ_09"));
    alignas(4) unsigned char bytes[1028];
    for (unsigned i=0;i<sizeof(bytes);++i) bytes[i]=static_cast<unsigned char>((i*73+191)&255);
    /* Unaligned input and every length, with carry-heavy prior accumulator. */
    for (unsigned alignment=0;alignment<4;++alignment)
    for (unsigned n=0;n<1024;++n) {
        uint32_t expected=oracle(bytes+alignment,n,UINT32_C(0xfedcba98));
        CHECK(CRC_Memory(bytes+alignment,n,UINT32_C(0xfedcba98))==expected);
        unsigned split=n/2;
        CHECK(CRC_Memory(bytes+alignment+split,n-split,CRC_Memory(bytes+alignment,split,UINT32_C(0xfedcba98)))==expected);
    }
    const char signed_bytes[]={static_cast<char>(0x80),static_cast<char>(0xff),0};
    CHECK(CRC_String(signed_bytes)==oracle(reinterpret_cast<const unsigned char*>(signed_bytes),2));
    CHECK(CRC_Stringi(signed_bytes)==CRC_String(signed_bytes));
    std::puts("Original WWLib CRC tests passed");
    return 0;
}
