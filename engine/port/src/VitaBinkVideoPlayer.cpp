// SPDX-License-Identifier: GPL-3.0-or-later
#include "VideoDevice/Bink/BinkVideoPlayer.h"

#include "Common/GlobalData.h"
#include "Common/Registry.h"
#include "GeneralsRetailPath.h"
#include "VitaBinkVideoDecoder.h"

#include <limits>
#include <new>
#include <stdio.h>
#include <string>

#if defined(GENERALS_PLATFORM_VITA)
#include <psp2/kernel/processmgr.h>
#else
#include <chrono>
#endif

namespace {

std::int64_t MovieClockMicroseconds()
{
#if defined(GENERALS_PLATFORM_VITA)
    return static_cast<std::int64_t>(sceKernelGetProcessTimeWide());
#else
    return std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
#endif
}

bool BufferFormat(VideoBuffer::Type format, VitaBinkVideoDecoder::PixelFormat *result)
{
    switch (format) {
        case VideoBuffer::TYPE_X8R8G8B8: *result = VitaBinkVideoDecoder::PixelB8G8R8X8; return true;
        case VideoBuffer::TYPE_R8G8B8: *result = VitaBinkVideoDecoder::PixelR8G8B8; return true;
        case VideoBuffer::TYPE_R5G6B5: *result = VitaBinkVideoDecoder::PixelR5G6B5; return true;
        case VideoBuffer::TYPE_X1R5G5B5: *result = VitaBinkVideoDecoder::PixelX1R5G5B5; return true;
        default: return false;
    }
}

bool OpenRelative(VitaBinkVideoDecoder *decoder, const char *relative)
{
    std::string path;
    return BuildGeneralsRetailPath(relative, &path) &&
           decoder->open(path.c_str(), MovieClockMicroseconds());
}

} // namespace

BinkVideoPlayer::BinkVideoPlayer() {}
BinkVideoPlayer::~BinkVideoPlayer() { deinit(); }
void BinkVideoPlayer::init() { VideoPlayer::init(); }
void BinkVideoPlayer::deinit()
{
    closeAllStreams();
    VideoPlayer::deinit();
}
void BinkVideoPlayer::reset() { VideoPlayer::reset(); }
void BinkVideoPlayer::update() { VideoPlayer::update(); }
void BinkVideoPlayer::loseFocus() { VideoPlayer::loseFocus(); }
void BinkVideoPlayer::regainFocus() { VideoPlayer::regainFocus(); }
void BinkVideoPlayer::notifyVideoPlayerOfNewProvider(Bool) {}
void BinkVideoPlayer::initializeBinkWithMiles() {}

VideoStreamInterface *BinkVideoPlayer::createStream(VitaBinkVideoDecoder *decoder)
{
    if (decoder == NULL || !decoder->isOpen()) return NULL;
    BinkVideoStream *stream = NEW BinkVideoStream;
    if (stream == NULL) return NULL;
    stream->m_decoder = decoder;
    stream->m_next = m_firstStream;
    stream->m_player = this;
    m_firstStream = stream;
    return stream;
}

VideoStreamInterface *BinkVideoPlayer::open(AsciiString movieTitle)
{
    const Video *video = getVideo(movieTitle);
    if (video == NULL) return NULL;
    VitaBinkVideoDecoder *decoder = new (std::nothrow) VitaBinkVideoDecoder;
    if (decoder == NULL) return NULL;

    char relative[512];
    bool opened = false;
    if (TheGlobalData != NULL && TheGlobalData->m_modDir.isNotEmpty()) {
        const int count = snprintf(relative, sizeof(relative), "%sData/Movies/%s.bik",
            TheGlobalData->m_modDir.str(), video->m_filename.str());
        opened = count > 0 && static_cast<std::size_t>(count) < sizeof(relative) &&
                 OpenRelative(decoder, relative);
    }
    if (!opened) {
        const int count = snprintf(relative, sizeof(relative), "Data/%s/Movies/%s.bik",
            GetRegistryLanguage().str(), video->m_filename.str());
        opened = count > 0 && static_cast<std::size_t>(count) < sizeof(relative) &&
                 OpenRelative(decoder, relative);
    }
    if (!opened) {
        const int count = snprintf(relative, sizeof(relative), "Data/Movies/%s.bik",
            video->m_filename.str());
        opened = count > 0 && static_cast<std::size_t>(count) < sizeof(relative) &&
                 OpenRelative(decoder, relative);
    }
    if (!opened) {
        delete decoder;
        return NULL;
    }
    VideoStreamInterface *stream = createStream(decoder);
    if (stream == NULL) delete decoder;
    return stream;
}

VideoStreamInterface *BinkVideoPlayer::load(AsciiString movieTitle) { return open(movieTitle); }

BinkVideoStream::BinkVideoStream() : m_decoder(NULL) {}
BinkVideoStream::~BinkVideoStream() { delete m_decoder; }
void BinkVideoStream::update() {}
Bool BinkVideoStream::isFrameReady()
{
    return m_decoder != NULL && m_decoder->isFrameReady(MovieClockMicroseconds());
}
void BinkVideoStream::frameDecompress() {}
void BinkVideoStream::frameRender(VideoBuffer *buffer)
{
    if (m_decoder == NULL || buffer == NULL) return;
    VitaBinkVideoDecoder::PixelFormat format;
    if (!BufferFormat(buffer->format(), &format)) return;
    void *memory = buffer->lock();
    if (memory == NULL) return;
    m_decoder->copyFrame(memory, buffer->pitch(), buffer->height(),
                         buffer->xPos(), buffer->yPos(), format);
    buffer->unlock();
}
void BinkVideoStream::frameNext() { if (m_decoder != NULL) m_decoder->decodeNextFrame(); }
Int BinkVideoStream::frameIndex()
{
    const std::int64_t value = m_decoder == NULL ? -1 : m_decoder->frameIndex();
    return value > std::numeric_limits<Int>::max() ? std::numeric_limits<Int>::max() :
           static_cast<Int>(value);
}
Int BinkVideoStream::frameCount()
{
    const std::int64_t value = m_decoder == NULL ? 0 : m_decoder->frameCount();
    return value > std::numeric_limits<Int>::max() ? std::numeric_limits<Int>::max() :
           static_cast<Int>(value);
}
void BinkVideoStream::frameGoto(Int index)
{
    if (m_decoder != NULL) m_decoder->seekFrame(index, MovieClockMicroseconds());
}
Int BinkVideoStream::height() { return m_decoder == NULL ? 0 : m_decoder->height(); }
Int BinkVideoStream::width() { return m_decoder == NULL ? 0 : m_decoder->width(); }
