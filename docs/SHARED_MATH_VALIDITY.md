# Shared WWMath validity checks

Zero Hour's original `WWMath::Is_Valid_Float` and `Is_Valid_Double` inspect
floating-point exponents through `unsigned long*`. On LP64 hosts the float
read exceeds its storage and the double word offset is wrong. The pointer
casts also violate C++ aliasing rules on the 32-bit target.

The patch copies the representation into explicit 32-bit and 64-bit integers
and tests the original exponent masks. Finite values, including signed zero
and subnormals, remain valid; both infinities and all NaNs remain invalid.
The original source stays unchanged in the vendor directory.

This adapts the same repair from [Renegade Vita](https://github.com/TheGh0stShip/RenegadeVita),
`wwmath-a35-valid-float-layout.patch`. Upstream EA notices and GPLv3 additional
terms remain intact. Shared ancestry alone does not establish engine or ABI
compatibility.

The CMake probe includes the complete staged Zero Hour header and checks both
signs, every exponent, and three fraction patterns: 1,536 float and 12,288
double representations. Host sanitizer execution and ARM compile/link are
separate gates. Its allocation declaration guard selects actual standard
operators from `<new>`; it does not validate the engine allocator. Physical
Vita execution and full WWMath integration remain unverified.
