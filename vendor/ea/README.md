# Original source provenance

The files listed in `manifest.json` are verbatim files from EA's official
source release at the recorded commit, with original notices intact.
[LICENSE.md](../../LICENSE.md) preserves the GPLv3 license and additional terms.

The build verifies input hashes, copies only these declared files to a build
staging directory, applies declared patches with zero fuzz, and verifies every
result hash. The originals are never edited by the build. Staged versions are
independently modified work, not original EA binaries.

`realcrc-width.patch` keeps the original Win32 32-bit checksum ABI on LP64 hosts
by replacing `unsigned long` with `uint32_t`. On Vita ILP32 the original width
was already 32-bit; this is a host portability correction. The patch also casts
bytes to unsigned char before `toupper` to satisfy the C character API's input
contract. The original CRC algorithm and table remain the owners. This module
is the WWLib CRC, not the separate game snapshot checksum.
