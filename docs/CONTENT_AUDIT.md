# Content and source audit

The inventory follows four separate evidence stages: source enumeration,
selected/retained build symbols, authored retail references, and runtime route
verification. Presence at one stage does not close the others. The complete
port remains the objective; an inventory is an intermediate tool.

The initial scanner enumerates and hashes every supplied source file, records
translation units, lexical function/pointer-width/script-dispatch candidates,
and file-valued source string literals. It reads supplied BIGF directories with
bounded member-name and payload-range checks, records loose-file metadata,
and associates exact normalized source paths with retail member candidates.
It retains unresolved literals and multiple candidates explicitly.

```sh
python3 tools/inventory_content.py --source /path/to/GeneralsMD/Code \
  --data /path/to/zero-hour --data /path/to/generals \
  --output .local/content-inventory.json
build-parser/bin/python -m unittest discover -s tests -p 'test_*.py'
```

Set up the pinned parser environment described in the README before running
the complete Python contracts. Detailed retail output is restricted to ignored
`.local/`. No assets are extracted,
no payloads are copied, and no absolute input roots are written to the receipt.
Archive hashes cover the header/directory only, not payload identity.

This is preliminary static discovery. Lexical function candidates are not a
complete C++ function index; pointer-width candidates are not a pointer graph.
The scanner does not resolve computed names, preprocessor reachability, INI
inheritance, script actions/conditions, map triggers, WND menu callbacks,
MappedImage sprites, sound events, CSF localization or nested W3D materials.
Exact path absence is unresolved evidence, not proof that an asset is missing.
Retail mount order and overrides remain unknown. Parser failures cause a
nonzero exit and remain in the receipt.

Next steps: implement typed INI/WND/MAP reference discovery and source handler
registration inventories; preserve file/line or member/offset provenance;
join those records to target compile commands, linker map and defined symbols.
Runtime load/callback observations must close routes on physical Vita/PSTV.

The C boundary probe now validates complete BIGF directories with bytewise
mixed-endian reads, bounded name scans and subtraction-based payload range
checks. It accepts empty offset-zero records and directory padding without
interpreting wildcard, duplicate or override semantics. Payloads need not be
resident. Malformed input leaves the decoded output unchanged.

The original integration owner is `Win32BIGFileSystem::openArchiveFile` in
`GameEngineDevice/Source/Win32Device/Common/Win32BIGFileSystem.cpp`. Integration
into its replacement platform boundary remains open; the validator is currently
a standalone probe. Host sanitizer cases cover truncated directories, missing
terminators, invalid counts, payload overlap with the directory, end-of-file
ranges, 32-bit wraparound and four input alignments. Both boundary probes compile
and link for ARM with ELF attribute gates and matching artifact identities.
These checks do not prove original engine loading or physical device behavior.

`tools/map_chunks.py` provides bounded host diagnostics for raw CkMp maps,
EAR/RefPack and ZL/zlib wrappers. It reads fixed-width little-endian map fields
and big-endian RefPack size fields independently of host integer layout.
Duplicate table identifiers retain every label candidate. Top-level framing
skips bodies; it does not assume every body is another chunk list or establish
object, script, terrain or mode coverage.

The diagnostic caps decoded maps at 16 MiB and table/top-level chunk counts at
65,536. It requires exact compressed termination and decoded size. These are
explicit diagnostic policies, not claims about the original loader's rejection
behavior. RefPack overlap copies preserve the original forward-copy semantics.
Synthetic contracts cover all command forms, high distance/length bits, optional
and wide size headers, terminal literals, wrapper validation, duplicate labels
and truncated or oversized structures. Retail-derived results stay private.
The module is an inventory aid; original engine integration and physical
Vita/PSTV validation remain separate requirements.

`tools/map_values.py` reads counted ASCII byte strings and typed dictionaries
with explicit scalar widths. Entries preserve order and duplicates, signed
packed-key shifting, ambiguous table labels, raw float32 bits and UTF-16 code
units. Embedded NULs and unpaired surrogates remain visible for review. The
module refuses native-layout unpack formats and does not use host wchar_t.
These wire-value records do not establish runtime string behavior, dictionary
capacity, property interpretation or serialization ABI compatibility.

`tools/script_leaf_values.py` decodes raw action/false-action versions 1–2 and
condition versions 1–4 using the original fixed-width parameter layout. It
preserves numeric IDs, packed name-key candidates, signed integer values,
float32 bits, coordinate bits and counted byte strings. Counts outside the
original 12-slot parameter capacity, truncation, unsupported labels/versions
and trailing bytes are diagnostic errors. Unknown parameter enum values retain
the original non-coordinate wire layout without implying semantic support.

The decoder leaves runtime name-key generation, template rematching, legacy
parameter insertion/rewriting and template validation unresolved. Synthetic
contracts cover both action routes, every known version, parameter capacity,
all truncation points and raw value preservation. No original script objects
are instantiated, and decoding does not prove referenced resources load.
