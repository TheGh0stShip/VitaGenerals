/* SPDX-License-Identifier: GPL-3.0-or-later */
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#if !defined(__arm__) || !defined(__ARM_ARCH_7A__) || !defined(__ARM_EABI__)
#error Vita requires ARMv7-A with ARM EABI
#endif
#if __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error Vita requires little endian
#endif
#ifndef __ARM_PCS_VFP
#error This build requires the verified hard-float calling ABI
#endif
_Static_assert(CHAR_BIT == 8, "byte width");
_Static_assert(sizeof(int)==4 && sizeof(long)==4 && sizeof(void*)==4 && sizeof(size_t)==4, "Vita ILP32 required");
_Static_assert(_Alignof(uint64_t)==8 && _Alignof(double)==8, "AAPCS alignment required");
float vg_abi_float_probe(float x, double y) { return x + (float)y; }
