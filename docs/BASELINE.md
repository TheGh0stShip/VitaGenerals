# Original-source baseline ledger

The complete native Vita/PSTV port remains the objective. Phase 0 is incomplete:
original dependency clusters link; the game engine, remaining platform replacements,
package and physical acceptance remain open.

## Provenance and deterministic staging

EA baseline: `0a05454d8574207440a5fb15241b98ad0b435590`. The supplied archive
matched all 6,076 tracked upstream files byte-for-byte. Two WWLib checksum
files and the additional cluster inputs are retained verbatim in `vendor/ea`, with their original notices and
per-file hashes. No retail files or implementation from another port were copied.

The build stages declared originals in a temporary tree, verifies copied input
hashes, applies hash-pinned patches with zero fuzz, and verifies result hashes
before updating build sources. Failure is fatal. Originals are not modified.
The 32-bit checksum API corrects LP64 host widening; Vita's original ILP32 width
is unchanged. Unsigned byte conversion makes `toupper` input defined. Runtime
locale behavior outside the C-locale probe remains unverified. This WWLib CRC
must not be confused with the game's separate snapshot checksum.

## Reproduction and evidence

```sh
python3.12 -m venv build-parser
build-parser/bin/python -m pip install --only-binary=:all: --require-hashes -r tools/parser-requirements.txt
build-parser/bin/python tools/run_host_probes.py --build-dir build-host-probes --sanitizer asan-ubsan
python3 tools/install_ci_sdk.py --directory build-sdk-ci
export VITASDK="$PWD/build-sdk-ci/vitasdk"
cmake -S . -B build-arm-ci -DCMAKE_TOOLCHAIN_FILE="$VITASDK/share/vita.toolchain.cmake" -DCMAKE_BUILD_TYPE=Debug
cmake --build build-arm-ci
python3 tools/record_build_identity.py --build-dir build-arm-ci
```

The SDK release and archive hash are pinned in `tools/vitasdk-lock.json`.
The SDK host is x86-64 Linux; its target is 32-bit ARM Vita, not AArch64.
Original source, patch and output hashes live in `vendor/ea/manifest.json`.
Host logs and receipts, ARM ELF/map/attributes/symbols and artifact hashes stay
in ignored build directories. No package is produced; the identity receipt
records that explicitly. These checks execute no upstream project build hooks.

Host probes cover BIGF header bounds and original CRC known vectors, all four
input alignments, incremental updates, empty inputs, carry-heavy seeds and
high-bit bytes. ASan/UBSan pass on the host. ARM source/archive/final ELF gates
verify ILP32, ARMv7-A, little endian, AAPCS alignment and hard-float attributes.
The linked ELF retains CRC_Memory, CRC_String and CRC_Stringi. Retention does
not prove gameplay use or correct runtime registration.

SDK archives can contain assembly members without VFP argument attributes.
Artifact receipts count those separately and retain `individual_review_required`;
final ELF attributes are not proof for every linked dependency. Host results,
ARM linkage and eventual physical evidence remain separate classes.

## Remaining baseline and acceptance gaps

- Full engine host and ARM build/link; unavailable original middleware.
- Complete translation-unit/registrar, port-guard and implementation inventories.
- Typed asset/config/map/script/UI and renderer coverage, across all game modes.
- Dependency ABI review for linked SDK members lacking attributes.
- Native lifecycle/diagnostics packaging and matching-artifact crash tooling.
- Gameplay and deliberate handheld/PSTV input mapping.
- Physical memory/performance feasibility against the 60 FPS target; campaign,
  challenges, skirmish, multiplayer, saves, transitions, movies/audio and soak.
