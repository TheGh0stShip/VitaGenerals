# Callback registry candidates

`tools/audit_function_lexicon.py` inventories initializer candidates using the
exact original `FunctionLexicon::TableEntry` type spelling. The ledger is
`reports/generated/function-lexicon.json.gz`. Every original Code input is
hashed against the source pin. Of 2,961 C/C++ inputs, four contain the raw
`TableEntry` token and are parsed for this sweep. Aliases and macros can escape
that selection; this is not a complete callback registrar census.

The baseline contains nine tables, 289 named entries and nine sentinels. One
parser recovery remains attached. Entries preserve source hashes, line numbers,
raw initializer arguments, duplicates and order. Escaped or prefixed strings
remain unresolved. Conditional initializer nodes remain unsupported records,
with no claim that preprocessing or registration has executed.

Seven tables belong to the base lexicon. W3D initialization calls base
initialization, then loads separate device draw and layout-init tables.
`loadTable` generates name keys and stores the table at its index. The draw and
layout-init wrappers implement their default `TABLE_ANY` lookup by searching
the device table first, then the corresponding base table. Their default lookup
does not use the generic all-table search.

Original registry validation compares non-null function addresses and reports
different entries sharing an address. It does not verify callback signatures,
registration execution or correct target calling conventions. Table entries
store function addresses as `void*`; the original typed lookup casts need review
at the platform boundary. Never truncate actual host pointers or globally pack
structures. Vita is little-endian ARMv7-A, ARM/Thumb, ILP32; floating-point ABI,
alignment and calling conventions require target evidence.

Original callbacks include empty bodies and immediate returns. These are
baseline behavior, not automatically port defects. Keyboard processing passes
`MSG_IGNORED` up the window hierarchy, so return semantics must be preserved.
Function-body candidates, original build inclusion, callback reachability,
window structure, images, fonts, text and complete modal/input routing remain
open. Retail joins stay local. This sweep contributes evidence to existing
content/platform gaps without counting the same gaps twice.

CI regenerates the report from fresh pinned source and compares decoded JSON.
Focused contracts cover ordering, duplicate names, sentinels, comments, other
types, unresolved strings, raw function expressions, conditional initializers,
parser errors and rejected source inputs. These checks do not establish a full
engine build or physical Vita/PSTV behavior.
