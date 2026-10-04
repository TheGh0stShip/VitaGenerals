# INI dispatch ownership sweep

`reports/generated/ini-dispatch.json` enumerates all 62 tokens in the original
`theTypeTable`, with handler names, dispatch lines and source definition
candidates. Every token has one lexical definition candidate in the pinned
Zero Hour Code tree. The scanner checks the complete tree fingerprint and
records source hashes; unsupported table syntax or sentinel structure fails.
No retail configuration is published.

`INI.cpp::findBlockParse` uses case-sensitive `strcmp` and returns the matching
callback, or null when no token matches. `findFieldParse` also compares with
`strcmp`, but supports a null-token sentinel with a nonnull parser as a fallback;
its user-data argument becomes the unmatched token. Top-level and field-table
sentinels therefore have different behavior. `INI::load` calls `setFPMode` before
parsing, explicitly for consistent simulation real values.

The top-level table covers object/reskin, campaign/challenge, command interfaces,
audio/video, terrain/weather/water, weapons/upgrades/science, player templates,
script action/condition configuration and other engine data. Counts establish
source dispatch sites, not complete content coverage or operational parsers.

| Gap | Priority | Dependency / evidence needed |
| --- | --- | --- |
| Original INI subsystem absent from target engine build | Blocking | Original file/string/system dependencies and platform boundaries |
| Nested field tables and fallback callbacks not enumerated | Required | All FieldParse tables, offsets and inherited module parse ownership |
| Host/ARM field offsets unverified | Required | Original Int widths, actual object layouts and callback argument checks |
| Retail bindings and load precedence unresolved | Required | All supplied INI blocks/fields, includes, inheritance and overrides |
| Deterministic numeric parsing unverified | Required | Floating-point setup, numeric parser and simulation checksum evidence |
| Runtime load and save compatibility unverified | Required | Full progression and load traces on Vita/PSTV |

Definition matching is lexical: comments and ordinary literals are masked, but
raw strings, preprocessing, generated definitions and full C++ name resolution
remain outside its scope. A unique source candidate proves neither target
selection nor link retention, callback execution or valid field layout. Offsets
must follow the actual build's object layout; host pointer sizes must not be
forced to the target width by truncation or global packing.

```sh
python3 tools/audit_ini_dispatch.py --source build-source-ci/GeneralsMD/Code \
  --output build-arm-ci/ini-dispatch.json
cmp reports/generated/ini-dispatch.json build-arm-ci/ini-dispatch.json
```
