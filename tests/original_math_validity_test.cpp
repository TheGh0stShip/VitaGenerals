// SPDX-License-Identifier: GPL-3.0-or-later
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <new>
#include <initializer_list>
#ifdef __fastcall
#undef __fastcall
#endif
#include "wwmath.h"
static void require(bool value) { if (!value) std::abort(); }
int main() {
    // Exercise both signs and every exponent, with zero and nonzero fraction.
    // Build values from bytes instead of violating float/integer aliasing.
    for (std::uint32_t sign = 0; sign < 2; ++sign) {
        for (std::uint32_t exponent = 0; exponent < 256; ++exponent) {
            for (std::uint32_t fraction : {0U, 1U, 0x7fffffU}) {
                std::uint32_t bits = (sign << 31) | (exponent << 23) | fraction;
                float value;
                std::memcpy(&value, &bits, sizeof(value));
                require(WWMath::Is_Valid_Float(value) == (exponent != 255));
            }
        }
        for (std::uint64_t exponent = 0; exponent < 2048; ++exponent) {
            for (std::uint64_t fraction : {UINT64_C(0), UINT64_C(1), UINT64_C(0xfffffffffffff)}) {
                std::uint64_t bits = (std::uint64_t(sign) << 63) | (exponent << 52) | fraction;
                double value;
                std::memcpy(&value, &bits, sizeof(value));
                require(WWMath::Is_Valid_Double(value) == (exponent != 2047));
            }
        }
    }
    return 0;
}
