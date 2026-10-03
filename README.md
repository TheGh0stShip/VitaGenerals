# VitaGenerals

Early development of a PS Vita / PSTV source port of EA's released Zero Hour
engine. No playable game or hardware-tested build is available yet.

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
These builds produce libraries and an ABI probe, not a game executable or VPK.
See [port constraints and next milestones](docs/PORTING.md).

## Upstream baseline

EA main commit: `0a05454d8574207440a5fb15241b98ad0b435590`.
Keep the original source in the ignored `upstream/` directory until an audited
source import is ready. The available source was released for Win32 and omits
several required SDKs; a modern cross-platform build requires substantial work.
