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

The original W3D texture, surface and indexed `Render2D` route requires a native
graphics provider. `tools/build_vitagl.py` builds a checksum-pinned LGPLv3
vitaGL revision with ARMv7 hard-float flags and retains its complete source and
license texts. The local patches preserve compact unlit vertices, indexed
immediate submission, complete replacement uploads and transactional DDS chains.
They extend the platform boundary beneath W3D; they do not replace W3D traversal,
format selection, texture ownership or render state. Packaging has the same
source, relinkable-object and license obligations as the other static LGPL
dependency. A successful archive build is not renderer or hardware evidence.

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
destroyed. Two aligned output blocks alternate so the device-retained block
remains unchanged while the worker fills its successor. The decoded ring is
bounded and applies backpressure rather than silently discarding samples. If
no audio port can be opened, video remains
usable and further audio is discarded without blocking the movie owner. ARM
archive inspection and a final link against `SceAudio_stub` cover this boundary;
audible output, clock synchronization and starvation behavior still require
physical Vita/PSTV validation.

Opening a stream decodes the first video frame, then performs bounded demux
prefetch until the audio reserve is ready while retaining intervening video
packets in order. The first frame remains available for `Display` to copy into
its original video buffer while the audio worker stays gated. A successful
buffer unlock then arms the shared presentation origin. FFmpeg send backpressure
keeps the current packet referenced until the decoder accepts it. Packet-count and
byte ceilings bound startup work; if those ceilings prevent a safe reserve,
audio is disabled for that movie instead of starting late or losing samples.
This establishes the scheduling contract in host decode and ARM link evidence,
but only device measurements can establish audible synchronization.

The stream adapter also performs bounded catch-up inside Zero Hour's existing
one-frame `Display::update` contract. It may discard at most four overdue frames
while looking for the frame appropriate to the current presentation clock and
yields after a 2 ms catch-up budget. It always preserves the first frame and
forces another visible frame after two authored frame intervals, preventing a
slow decoder from dropping forever. A low audio reserve can request catch-up,
but never permits dropping a frame before its presentation timestamp. The
thresholds require physical timing evidence before they can be accepted as
final Vita settings.

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

Audio packets now keep an independent FFmpeg reference until the decoder accepts
them, including send-side backpressure. End-of-stream handling records acceptance
of the decoder drain packet and does not flush the resampler until decoder EOF.
An audio decode failure releases the retained packet and disables that stream
without ending otherwise usable video playback.

Those requirements came from retained physical failures as well as successful
builds: early Renegade candidates showed sub-5-FPS movies, frame-drop starvation,
large per-frame upload cost and audio starvation despite correct ARM links. Its
WWUI dialogs, splash handling, menu music, campaign mode lifetime and outer
session loop are title-specific. They do not replace Zero Hour's `Display`,
`Shell`, `MainMenu.wnd`, shell-map simulation or first-input reveal behavior.
