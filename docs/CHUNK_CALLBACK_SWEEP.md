# Chunk callback and read candidates

The pinned source is scanned for `registerParser`, `openDataChunk`,
`closeDataChunk`, `readDict`, `readAsciiString` and `readUnicodeString` calls.
The source-only report, `reports/generated/chunk-routes.json.gz`, records
source hashes, line spans, raw arguments, callable owners, conditional syntax
and all parser recovery nodes. Names are candidates: receivers, overloads,
preprocessor reachability and callback execution remain unresolved.

| Route | Sites |
| --- | ---: |
| registerParser | 36 |
| openDataChunk / closeDataChunk | 26 each |
| readAsciiString | 22 |
| readDict | 11 |
| readUnicodeString | 4 |

Across 2,961 files, 125 call candidates have no own parser errors. All 14,677
parser recovery nodes remain recorded; that count is shared source evidence,
not an additional set of defects or proof of a complete call denominator.

Original `DataChunkInput::parse` selects callbacks by both chunk label and
parent label. Registration order and dynamic parent arguments matter. Bodies
cannot all be interpreted recursively as chunk lists: callbacks also read
scalars, strings and dictionaries. Closing a chunk skips unread body bytes.

The actual serialized header reads a 32-bit identifier, 16-bit version and
signed 32-bit body size, totaling ten bytes. The historical header-size constant
must not substitute for those field reads. ASCII strings have a 16-bit byte
count; dictionary entries have a packed signed 32-bit key/type followed by a
typed value. Preserve arithmetic key shifting and the original 32-bit lookup.

`WorldHeightMap` registers ObjectsList at the root, then Object under its parent
label. Its object callback reads coordinates, angle, flags, template name and
an optional dictionary. Object versions 1 and 2 reset height to zero; subsequent
height validation and template lookup affect runtime ownership. The preview
reader in MapUtil is a separate route and cannot establish runtime completeness.

Unicode serialization requires explicit review: the original Windows WideChar
is two bytes, while default target wchar_t may differ. Diagnostic UTF-16 reads
do not fix UnicodeString ownership, library ABI or engine serialization.
Vita remains little-endian ARMv7-A ILP32 with checked floating-point ABI;
host parsing does not establish physical hardware correctness.

This sweep does not enumerate every asset loader or resolve retail map resources.
Retail-derived reports remain private. Synthetic tests cover dynamic arguments,
guards, comments/strings, lambda owners, independent route selection, parser
recovery and refusal of unpinned source. CI regenerates the report from the
pinned tree and compares typed JSON content.
