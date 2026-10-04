# Text formatting sweep

The pinned source contains 2,971 named formatting-call candidates across 2,961
C/C++ source and header files, including tools and middleware. Of these, 2,537
have a directly extractable literal at the candidate format argument position;
434 retain dynamic or unresolved expressions. Literal candidates contain 3,418
format directives. Three calls have their own parser errors. The scan retains
14,677 parser recoveries across the input files.

[The generated inventory](../reports/generated/text-formats.json.gz) preserves
source hashes, line coordinates, enclosing callables, guards, raw arguments,
literal candidates and directive fields. Named calls do not resolve receiver
types: the 988 `format` sites include unresolved ASCII and Unicode bindings.
Legacy API spellings supply candidate argument positions; overloads require
signature review. Adjacent literals and supported C escapes are decoded;
macros, raw literals, casts and unsupported escapes remain unresolved.

Observed literal directives include `%s`, `%S`, `%hs`, `%ls`, `%ws`, `%I64d`,
`%I64i`, `%I64X`, `%p`, and integer/floating conversions. No literal candidate
contains `%n`, `%Z`, or an `L` length modifier. This does not establish that
these are unused: dynamic expressions, localized retail strings, aliases,
custom wrappers, preprocessing and parser recovery remain coverage gaps.

Before publishing a UTF-16 formatter, bind the original Unicode callers and
argument types, then reconcile localized format strings, codepages and locale
state. Windows uses 16-bit wide characters; Linux/WSL `wchar_t` is normally
32-bit. Vita is little-endian ARMv7-A with ILP32 and requires separately checked
floating-point ABI evidence. These source observations establish neither
format ABI parity nor complete-game behavior on Vita/PSTV.

Reproduce using the hash-pinned parser environment:

```sh
build-parser/bin/python tools/audit_text_formats.py \
  --source build-source/GeneralsMD/Code --output build-formats/text-formats.json.gz
python3 tools/compare_report.py reports/generated/text-formats.json.gz \
  build-formats/text-formats.json.gz
```
