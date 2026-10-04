# Font platform and ownership review

`reports/generated/font-boundary-review.json` records a partial review of the
pinned original font implementation. Source hashes accompany nine ownership
contracts, nine glyph contracts and 18 selected Windows API call sites. These
are reviewed source observations, not a complete caller census or runtime proof.

The original `FontCharsClass` obtains metrics and individual character bitmaps
through GDI. It uses fixed 96 DPI for point conversion, substitutes Arial for
the name `Generals`, adjusts that font's width and overhang, and clamps pixel
overlap to zero through four. Character spacing subtracts overlap and overhang
from stored width. Rasterized 24-bit bitmap intensity becomes the high alpha
nibble of the original 16-bit white glyph pixels. A native font boundary must
preserve these layout and pixel contracts alongside the original cache,
sentence renderer and surface ownership.

The asset manager retains a font-list reference and returns a counted caller
reference. Sentence renderers retain and release their font independently.
The font library releases both the alternate Unicode font and the primary
font. The alternate pointer belongs to a shared cached font object; aliasing,
overwrites and complete teardown order still need route-level verification.

Glyph buffers contain 32,768 16-bit pixels. Allocation checks use character
width and font height, while rasterization uses GDI character width and height.
The replacement must establish metric bounds before writing. A cursor advance
that includes overlap, or an exact-fit comparison using `>`, does not by itself
prove an out-of-bounds write. Fresh-buffer capacity and arithmetic limits remain
explicit verification requirements.

The source allocates each glyph buffer with scalar `W3DNEW`, but destroys it
with `delete[]`. `W3DMPO_GLUE` supplies scalar pool allocation and deletion;
the selected configuration, pool integration and correction need focused
validation before a production patch. This review supplies no replacement
allocator and makes no target failure claim.

`WideChar` is a `wchar_t` typedef, whereas rendering receives Windows `WCHAR`
through Windows headers. Original Windows UTF-16 units must remain explicit at
content and rendering boundaries. Vita is little-endian ARMv7-A/Cortex-A9 with
32-bit ARM/Thumb and ILP32; its SDK's four-byte `wchar_t` cannot silently replace
two-byte units. Do not globally change `wchar_t` size, pack structures or truncate
host pointers. Verify alignment, calling conventions and floating-point ABI
against actual target objects and dependencies.

Font availability, licensing, native rasterizer metrics, texture upload and
physical Vita/PSTV results remain unresolved. Host and ARM baseline checks do
not demonstrate font rendering or complete engine execution.
