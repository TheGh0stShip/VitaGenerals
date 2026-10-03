# VitaGenerals

A native PS Vita / PSTV source port of EA's released Zero Hour engine, in early
development. The objective is the complete game: campaigns, challenges and skirmish,
original gameplay and presentation, usable handheld/controller controls,
save/load, audio/video, stable lifecycle behavior and multiplayer through
compatible service providers. Inventory tools and prototype builds are
intermediate milestones toward that objective.

Preserve the original engine and user-supplied retail data. Replace platform
and unavailable middleware boundaries while retaining game rules, asset
semantics and original subsystem ownership. The target is 60 FPS; feasibility remains unproven. Performance and memory
decisions must follow measurements on the target hardware.

No playable game or hardware-tested build is available yet. The current build
covers BIGF header parsing, a staged original WWLib checksum module,
source/retail inventory tooling and target ABI checks. There is no full engine build, renderer, launcher or game package.

The portable archive boundary module is new GPL-3.0-or-later code. EA's upstream
license and additional terms are preserved in [LICENSE.md](LICENSE.md). This
project is independently modified work, not an original EA release or an
endorsed product. Electronic Arts Inc. holds the original source copyright;
no trademark rights are granted. Retail art, audio, maps, executables and game
data are not distributed. A legitimate game installation is required.

## Host boundary checks

```sh
cmake -S . -B build-host
cmake --build build-host
ctest --test-dir build-host --output-on-failure
```

## Vita compile checks

Set VITASDK to the installed SDK root, then run:

```sh
cmake -S . -B build-vita -DCMAKE_TOOLCHAIN_FILE="$VITASDK/share/vita.toolchain.cmake"
cmake --build build-vita
python3 tools/check_vita_abi.py build-vita/CMakeFiles/vg_vita_abi.dir/src/vita_abi.c.obj build-vita/libvg_archive.a
```

Use the ELF checker on every dependency selected for linking. Members without
ABI attributes require individual review; they are not silently approved.
These builds produce libraries, an ABI probe and a linked checksum test ELF.
They do not produce a game executable or VPK.
See [port constraints and next milestones](docs/PORTING.md) and the
[source and content audit](docs/CONTENT_AUDIT.md).

## Upstream baseline

EA main commit: `0a05454d8574207440a5fb15241b98ad0b435590`.
Keep the original source in the ignored `upstream/` directory until an audited
source import is ready. The available source was released for Win32 and omits
several required SDKs; a modern cross-platform build requires substantial work.

## Development and acceptance

Use small commits with checks appropriate to the change. The CI workflow runs ordinary and ASan/UBSan host probes, Python contracts,
and an ARM compile/link baseline using a hash-pinned isolated SDK. Vita builds also
check the emitted object/archive ABI; every new linked dependency requires
matching ELF inspection. CI success does not establish a playable Vita build.

Source presence, build/link inclusion, authored resource bindings and runtime
behavior are separate evidence stages. Keep unresolved dependencies explicit.
Physical acceptance requires PS Vita and PSTV checks for gameplay, controls,
rendering, audio, saves, memory use, sustained performance, suspend/resume and
clean exit. Host and emulator results remain separate from hardware evidence.

Local continuity records, source references, build outputs, credentials, saves
and retail-derived inventories stay outside version control. Public commits
contain source, reproducible tooling and accurate engineering documentation.

See the [original-source baseline ledger](docs/BASELINE.md) for provenance,
retained artifact identity and remaining baseline gaps.
