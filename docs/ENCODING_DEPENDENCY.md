# Encoding library build

WWLib's Windows wide-to-narrow boundary requires UTF-16 code units and the
installation's ANSI code page. The inspected SDK provides conversion entry
points but an empty built-in encoding alias registry. Linking those entry
points alone does not establish working conversion.

`tools/libiconv-lock.json` pins GNU libiconv 1.18 to the SHA-256 published in
the [GNU release announcement](https://lists.gnu.org/archive/html/info-gnu/2024-12/msg00004.html).
The build recipe verifies the archive before executing configure, builds only
the conversion libraries, and retains the release source and license files.
Use a fresh output directory for each build:

```sh
python3 tools/build_libiconv.py --mode host --output build-codecs-host
python3 tools/build_libiconv.py --mode vita --vita-sdk "$VITASDK" --output build-codecs-arm
```

Vita builds require `arm-vita-eabi`, Cortex-A9 Thumb code and hard-float calling
conventions. Every object in both output archives passes the ELF attribute
gate. Host libiconv builds use address/undefined-behavior instrumentation.
The receipt records commands, compiler identity, source checksum, archive and
license hashes. Logs, downloaded source and binaries remain in ignored build
directories. `--archive` can reuse a downloaded archive; its checksum is still
required to match the lock.

Consumers must include the generated `library/include/iconv.h` and link
`library/lib/.libs/libiconv.a`. Its header routes calls to `libiconv_*`, avoiding
the SDK's incomplete registry. Verify the selected symbols in the final link
map. Do not infer an installation code page from the development host locale.

The libraries and headers retain LGPL-2.1-or-later notices. Distribution must
include the applicable notices and license, corresponding library source and
changes, and the materials needed to satisfy static-link relinking obligations.
The recipe's retained files support this work; they are not a finished release
compliance package. The GPL command-line utility is not a target build input.

Development probes exercised the original string class and mapped characters
for CP1252, CP1251, CP932, CP936, CP949 and CP950 against independent expected
bytes using the same pinned host library. ARM probes linked against the native
library. These are component checks, not complete code-page coverage, Windows
best-fit parity, full engine integration or physical Vita/PSTV validation.
