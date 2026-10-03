# Port status and engineering constraints

The first milestone builds an archive-header boundary module and a Vita ABI
probe. It does not build or launch the game. Physical Vita and PSTV validation
is pending; host tests and ELF inspection cannot establish hardware correctness.

The target is little-endian ARMv7-A Cortex-A9, ARM/Thumb, ILP32: int, long,
pointers and size_t are 32-bit. Never substitute AArch64. Verify floating-point
calling conventions against the installed compiler and every selected library.
The initial build uses explicitly selected hard-float, Thumb-2 and NEON options.
The ABI probe enforces widths, endian, EABI, VFP argument passing and 8-byte
alignment for double and uint64_t. Inspect emitted ELF attributes before linking.

Linux x86-64 typically uses LP64; Windows x64 uses LLP64. Preserve original
32-bit disk, network, checksum and pointer-token semantics using fixed widths,
explicit byte access and layout assertions. Do not globally pack structures or
truncate host pointers. Serialized pointer tokens need a mapping to real host
pointers. Review ARM alignment and calling conventions before trusting host
results. Label defects specific to host builds accordingly.

BIGF header decoding follows the original GeneralsMD Win32BIGFileSystem.cpp:
the total size is little-endian, while the entry count and directory fields are
big-endian. Header validation does not validate entry names, payload ranges,
compression, path safety or complete archive contents. Those are the next data
layer milestone, along with INI loading and case-insensitive asset lookup.

## Roadmap

1. Pin and verify the EA baseline; inventory Zero Hour engine build units and
   identify portable subsystems. Review candidate reuse licenses file by file.
2. Implement bounded archive directory iteration and file access; compile the
   real INI/parser dependencies with isolated platform replacements.
3. Establish a native Vita launcher, diagnostics and memory budgets; run on
   Vita and PSTV before bringing up engine simulation.
4. Replace Win32 platform services, DirectX renderer, Miles audio, Bink video
   and unavailable GameSpy services with reviewed, compatible implementations.
5. Validate campaign startup, skirmish, controls, save/load, audio, sustained
   performance and memory use on both hardware variants.

No performance or compatibility claim is established yet. Gameplay networking,
rendering strategy and resource budgets remain open engineering decisions.

## Reuse research

EA's source is the authoritative baseline:
https://github.com/electronicarts/CnC_Generals_Zero_Hour

GeneralsX is a candidate source of platform separation and dependency replacement
work: https://github.com/Hamschta/GeneralsX . Its desktop platform support does
not establish Vita compatibility. Review licenses and pin a commit before reuse;
no code from that project has been imported in this milestone.
