# Movie route candidates

`tools/audit_movie_routes.py` scans every C/C++ input in the pinned original
Code tree for selected movie methods, video definition access and Bink calls.
The machine-readable ledger is `reports/generated/movie-routes.json.gz`.
Source hashes, raw arguments, callable owners, preprocessing guards and parser
recoveries remain attached to the evidence. CI reproduces the report from a
fresh pinned source tree and compares decoded JSON content.

The baseline contains 197 selected calls across 2,961 C/C++ inputs, including
nine `playMovie`, two `playLogoMovie`, one `PlayMovieAndBlock`, one
`playCameoMovie` and sixteen `stopMovie` calls. All 61 `open` and 87 `load`
calls remain in the report, including unrelated receivers. These are reference
counts, not unique movie routes or defects. No selected call has its own parser
error; 14,677 source parser recoveries remain recorded and can conceal calls.

Original caller evidence includes campaign mission load screens, challenge
portraits, score-screen victory playback, startup logos, script actions and
command translation. `CampaignManager.cpp` binds `IntroMovie` to a mission
label and `FinalVictoryMovie` to a campaign string. Challenge persona fields
supply the left/right portrait movie getters. The score-screen wrapper applies
original memory and LOD conditions before playing the final victory movie.

`VideoPlayer::init` loads default video definitions before ordinary definitions;
`addVideo` replaces an equal internal name. The Bink implementation gets the
named definition, then attempts mod, localized and generic paths. Its `load`
implementation delegates to `open`. This establishes source behavior for that
implementation; mounted provider selection, actual codec I/O and runtime
execution remain unresolved.

The original display chooses a video buffer format through Direct3D8 caps and
four format fallbacks. Bink frame rendering copies into the locked buffer.
Video-buffer allocation, surface ownership, timing, audio-provider changes and
stream destruction must remain part of the platform replacement cluster.
No decoder or replacement renderer is implemented by this sweep.

Receiver types, overloads, preprocessing reachability, aliases, macros and
other backend methods are unresolved. Selected names do not establish a full
video interface or caller census. Retail reference joins remain local. This
ledger contributes to the existing content and platform evidence gaps; it does
not create a second count of those gaps.

Vita remains little-endian ARMv7-A, 32-bit ARM/Thumb with ILP32. Movie backend
interfaces need verified floating-point ABI, alignment and calling conventions;
Windows binaries are not target ABI evidence. Host pointer widths must remain
intact, with explicit widths at disk and wire boundaries. Neither this inventory
nor host/ARM baseline checks prove physical Vita/PSTV playback or performance.
