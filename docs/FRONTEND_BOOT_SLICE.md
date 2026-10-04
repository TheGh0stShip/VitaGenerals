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

The Vita adapter uses an explicit retail-data root and retains Zero Hour's lookup
order: active mod, localized `Data/<language>/Movies`, then `Data/Movies`.
Relative paths are normalized without permitting absolute paths or parent
traversal. When container metadata lacks an exact frame count, the decoder uses
duration and authored frame rate, then corrects the count at end of stream while
retaining the final decoded frame. This lets the original `Display` owner enter
its copyright hold or movie-complete branch instead of waiting for another frame.

The stream now decodes Bink audio through FFmpeg, resamples it to the Vita's
48 kHz stereo signed-16-bit format and feeds a dedicated Vita audio port. The
output worker waits for six 1,024-frame buffers before starting, drains a short
final buffer with hardware-required padding and stops before its decoder is
destroyed. The decoded ring is bounded and applies backpressure rather than
silently discarding samples. If no audio port can be opened, video remains
usable and further audio is discarded without blocking the movie owner. ARM
archive inspection and a final link against `SceAudio_stub` cover this boundary;
audible output, clock synchronization and starvation behavior still require
physical Vita/PSTV validation.

The Renegade Vita frontend history establishes several reusable requirements,
not runtime proof for this title. Decoder packets must survive FFmpeg
backpressure; presentation time starts only when decoded output can actually be
presented; audio output starts with a bounded reserve of decoded samples; update
work has a time budget; sustained lateness must still make visible progress; and
movie upload/render code must restore graphics state and invalidate renderer
texture caches. Skip input is edge-triggered and primed so a button held while a
movie opens does not immediately dismiss it. Failures must release decoder,
audio, texture and stream-list ownership while allowing the original startup
state machine to continue.

Those requirements came from retained physical failures as well as successful
builds: early Renegade candidates showed sub-5-FPS movies, frame-drop starvation,
large per-frame upload cost and audio starvation despite correct ARM links. Its
WWUI dialogs, splash handling, menu music, campaign mode lifetime and outer
session loop are title-specific. They do not replace Zero Hour's `Display`,
`Shell`, `MainMenu.wnd`, shell-map simulation or first-input reveal behavior.
