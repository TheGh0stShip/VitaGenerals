// SPDX-License-Identifier: GPL-3.0-or-later
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <new>
#include <initializer_list>
#include <cmath>
#include <limits>
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
    static_assert(sizeof(int) == 4 && sizeof(float) == 4, "32-bit math boundary");
    static_assert(std::numeric_limits<float>::is_iec559, "IEEE binary32 required");
    // Golden results from original expressions with x86 masked shifts/wrap.
    // Signed zero, subnormals, range endpoints, infinities and NaN payloads.
    struct Conversion { std::uint32_t bits; long long chop, floor; };
    const Conversion golden[] = {
        {0x00000000U, 0LL, 0LL},
        {0x80000000U, 0LL, 0LL},
        {0x00000001U, 0LL, 0LL},
        {0x80000001U, 0LL, -1LL},
        {0x3f000000U, 0LL, 0LL},
        {0xbf000000U, 0LL, -1LL},
        {0x4effffffU, 2147483520LL, 2147483520LL},
        {0xceffffffU, -2147483520LL, -2147483520LL},
        {0x4f000000U, -2147483648LL, -2147483648LL},
        {0xcf000000U, -2147483648LL, -2147483648LL},
        {0x4f000001U, -2147483392LL, -2147483392LL},
        {0xcf000001U, 2147483392LL, 2147483392LL},
        {0x4f7fffffU, -256LL, -256LL},
        {0xcf7fffffU, 256LL, 256LL},
        {0x7f800000U, 1LL, 1LL},
        {0xff800000U, -1LL, -1LL},
        {0x7fc00000U, 1LL, 1LL},
        {0xffc00000U, -1LL, -2LL},
        {0x7f800001U, 1LL, 1LL},
        {0xff800001U, -1LL, -2LL}
    };
    for (const auto &row : golden) {
        float value; std::memcpy(&value, &row.bits, sizeof(value));
        require(WWMath::Float_To_Int_Chop(value) == row.chop);
        require(WWMath::Float_To_Int_Floor(value) == row.floor);
    }
    // Independent mathematical oracle for representable inputs. Every sign
    // and exponent includes edge fractions and deterministic fraction samples.
    std::uint32_t state = 1;
    for (std::uint32_t sign = 0; sign < 2; ++sign) {
        for (std::uint32_t exponent = 0; exponent < 256; ++exponent) {
            for (unsigned sample = 0; sample < 4096; ++sample) {
                state = state * 1664525U + 1013904223U;
                const std::uint32_t fraction = sample == 0 ? 0U : sample == 1 ? 1U :
                    sample == 2 ? 0x7fffffU : state & 0x7fffffU;
                const std::uint32_t bits = (sign << 31) | (exponent << 23) | fraction;
                float value; std::memcpy(&value, &bits, sizeof(value));
                const double exact = value;
                if (exact >= -2147483648.0 && exact < 2147483648.0) {
                    require(WWMath::Float_To_Int_Chop(value) == static_cast<int>(std::trunc(exact)));
                    require(WWMath::Float_To_Int_Floor(value) == static_cast<int>(std::floor(exact)));
                }
            }
        }
    }
    return 0;
}
