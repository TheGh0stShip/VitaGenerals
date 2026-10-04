# Native engine dependency clusters

The `engine` build retains original allocator, WWMath and selected WWLib and
WWSaveLoad providers. These are diagnostic targets on the path to the complete
engine. They do not start the game or establish physical Vita correctness.
The source manifest pins pristine inputs, zero-fuzz patches and resulting bytes.
Configuration verifies the complete staged Code tree against those pins.

Reproduce the checks from freshly downloaded, pinned sources:

```sh
python3 tools/run_engine_clusters.py --mode host --build-dir build-clusters-host
python3 tools/run_engine_clusters.py --mode host --build-dir build-clusters-cp932 --legacy-encoding CP932
python3 tools/run_engine_clusters.py --mode vita --build-dir build-clusters-arm --vita-sdk "$VITASDK"
```

The runner builds the pinned conversion library, retains per-step logs and
hashes the output archives, executables and maps. Both builds run in CI and
in the exact Git-tree publication check. Host execution and native linking
remain separate evidence classes.

Stage the official pinned source with `tools/stage_engine_tree.py`. Configure
`engine` with `GENERALS_STAGED_CODE` pointing to its staged `Code` directory,
`GENERALS_MEMORY_POOL_CONFIG_PATH=Data/INI/MemoryPools.ini` and
`GENERALS_ICONV_PREFIX` pointing to the appropriate pinned libiconv build. Set
`GENERALS_LEGACY_ENCODING` to the installation ANSI encoding; the diagnostic
default is CP1252 and the DBCS gate also builds CP932.
Use the Vita toolchain for native builds. Host builds enable ASan and UBSan and
register seven tests with CTest. Native builds check each archive member and
diagnostic executable for ARM hard-float ABI consistency.

The full 35-source math archive and 24-source provider archive are retained
in the native link probe. Retaining their symbols does not prove initialization,
registration execution, numerical parity or complete save/load behavior.
The allocator and file probes are separate components, not an integrated game.

Open integration requirements include remaining UTF-16 consumers, installation
selection and Windows best-fit conversion parity, filename case resolution,
named mutex behavior, matrix inverse failure handling,
serialization bounds and transactional failure paths, and physical
RTC/filesystem validation. The diagnostic encoding is explicitly CP1252.
The native filesystem adapter preserves the SDK's descriptor ownership and
uses 64-bit RTC conversion; its private descriptor interface requires SDK pinning.

The unmodified MIT-licensed descriptor declaration is retained at
`engine/port/include/thirdparty/newlib-vitadescriptor.h`, from vita-newlib commit
`2e428297c0b6aefd830c5a75a7daa7e774562a42`,
`newlib/libc/sys/vita/vitadescriptor.h`. Its copyright and permission notice
remain intact. Derived EA declarations retain the original license notices;
the repository license and additional terms apply. GNU libiconv distribution
requirements are described in [ENCODING_DEPENDENCY.md](ENCODING_DEPENDENCY.md).

ASCII copy-on-write strings retain the original packed 16-bit count and capacity.
Saturated counts use a separate buffer rather than carrying into capacity.
Final destruction uses the successful atomic decrement's result; other owners
never reread the shared header after releasing it. Assignment acquires its new
ownership before releasing the old buffer. The reference probe covers saturation,
aliased assignment and continued use after releasing many owners. Host tests
also exercise concurrent release and copying on distinct string objects;
the host probe installs DMA and pool locks as the original startup does and
clears those pointers after joining its workers.
Concurrent mutation of the same string object is unsupported. Native compilation
does not establish hardware thread behavior.

The Unicode string cluster uses explicit 16-bit UTF-16 code units on LP64 hosts
and ILP32 Vita builds. It retains original copy-on-write ownership, handles a
saturated 16-bit reference count with a separate buffer, and replaces host
`wchar_t` routines with byte-width-independent operations. Its formatter keeps
Windows 32-bit `long` output semantics on LP64 hosts, preserves actual pointer
width, and converts narrow `%S`/`%hs` arguments through the pinned conversion
library. CP1252 and CP932 sanitizer tests include precision-bounded source
buffers without a terminating NUL. Numeric, pointer and whitespace reference
comparisons are compatibility evidence only; native execution remains open.
