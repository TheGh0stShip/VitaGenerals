# Intro movies and main-menu shell map

This milestone follows the original Zero Hour startup owners. `GameClient`
sequences `EALogoMovie` and the optional `Sizzle` movie, `Display` advances the
fullscreen video stream, and `Shell::showShellMap(TRUE)` starts the authored
shell map before `MainMenu.wnd` becomes interactive. The main-menu battlefield
is a live engine map and simulation, not a replacement video.

`MainMenuInit` hides the default menu group. `MainMenuInput` reveals it after a
character event or meaningful pointer movement. With no input, the menu remains
hidden and the shell-map battle continues. The Vita controller adapter must
preserve this first-input edge and must not synthesize input from an unchanged
stick, touch sample or held button.

Retail movies remain user supplied and unchanged. The Vita movie provider will
decode their Bink container, video and audio streams through a hash-pinned
minimal FFmpeg build. `tools/build_ffmpeg_bink.py` enables only the Bink demuxer,
Bink video/audio decoders, file protocol, scaling and resampling libraries. It
retains source, license and artifact hashes and checks every archive member for
32-bit little-endian ARM and hard-float argument attributes. Compilation and
ELF inspection do not establish playback, synchronization or hardware quality.
Release packages that statically link these libraries must accompany the FFmpeg
license and corresponding pinned source and provide the material needed to
relink the application, as required by the LGPL.

The Renegade Vita provider is a reviewed implementation reference for FFmpeg
decode scheduling, Vita audio output and texture upload. Zero Hour retains its
own `VideoPlayer`, `VideoStreamInterface`, `VideoBuffer`, `Display`, shell and
main-menu state machines. Integration must preserve localized movie lookup,
skip policy, logo hold timing, end-of-stream transition, focus loss, audio
volume ownership and failure cleanup.
