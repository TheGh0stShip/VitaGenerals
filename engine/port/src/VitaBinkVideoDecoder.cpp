// SPDX-License-Identifier: GPL-3.0-or-later
#include "VitaBinkVideoDecoder.h"

#include <algorithm>
#include <climits>
#include <limits>
#include <new>

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/imgutils.h>
#include <libavutil/pixfmt.h>
#include <libswscale/swscale.h>
}

struct VitaBinkVideoDecoder::State
{
    AVFormatContext *format;
    AVCodecContext *decoder;
    AVFrame *frame;
    AVPacket *packet;
    SwsContext *scaler;
    int stream;
    std::int64_t index;
    std::int64_t count;
    std::int64_t clockOrigin;
    std::int64_t ptsOrigin;
    std::int64_t presentation;
    bool draining;
    bool finished;
    bool hasFrame;

    State() : format(NULL), decoder(NULL), frame(NULL), packet(NULL), scaler(NULL),
        stream(-1), index(-1), count(0), clockOrigin(0), ptsOrigin(AV_NOPTS_VALUE),
        presentation(0), draining(false), finished(false), hasFrame(false) {}
};

namespace {

std::int64_t RescaleTimestamp(std::int64_t timestamp, AVRational timeBase)
{
    if (timestamp == AV_NOPTS_VALUE) return AV_NOPTS_VALUE;
    return av_rescale_q(timestamp, timeBase, AVRational{1, 1000000});
}

template <typename StateType>
bool FinishStream(StateType *state)
{
    state->finished = true;
    if (state->index < 0) {
        state->hasFrame = false;
        return false;
    }
    state->count = state->index + 1;
    state->hasFrame = true;
    return false;
}

AVPixelFormat OutputFormat(VitaBinkVideoDecoder::PixelFormat format)
{
    switch (format) {
        case VitaBinkVideoDecoder::PixelB8G8R8X8: return AV_PIX_FMT_BGRA;
        case VitaBinkVideoDecoder::PixelR8G8B8: return AV_PIX_FMT_RGB24;
        case VitaBinkVideoDecoder::PixelR5G6B5: return AV_PIX_FMT_RGB565LE;
        case VitaBinkVideoDecoder::PixelX1R5G5B5: return AV_PIX_FMT_RGB555LE;
    }
    return AV_PIX_FMT_NONE;
}

} // namespace

VitaBinkVideoDecoder::VitaBinkVideoDecoder() : m_state(new (std::nothrow) State) {}

VitaBinkVideoDecoder::~VitaBinkVideoDecoder()
{
    close();
    delete m_state;
}

bool VitaBinkVideoDecoder::open(const char *path, std::int64_t clockMicroseconds)
{
    close();
    if (m_state == NULL || path == NULL || path[0] == '\0') return false;
    if (avformat_open_input(&m_state->format, path, NULL, NULL) < 0 ||
        avformat_find_stream_info(m_state->format, NULL) < 0) {
        close();
        return false;
    }
    const int stream = av_find_best_stream(m_state->format, AVMEDIA_TYPE_VIDEO,
                                            -1, -1, NULL, 0);
    if (stream < 0) {
        close();
        return false;
    }
    AVStream *video = m_state->format->streams[stream];
    const AVCodec *codec = avcodec_find_decoder(video->codecpar->codec_id);
    m_state->decoder = codec == NULL ? NULL : avcodec_alloc_context3(codec);
    if (m_state->decoder == NULL ||
        avcodec_parameters_to_context(m_state->decoder, video->codecpar) < 0 ||
        avcodec_open2(m_state->decoder, codec, NULL) < 0 ||
        m_state->decoder->width <= 0 || m_state->decoder->height <= 0) {
        close();
        return false;
    }
    m_state->frame = av_frame_alloc();
    m_state->packet = av_packet_alloc();
    if (m_state->frame == NULL || m_state->packet == NULL) {
        close();
        return false;
    }
    m_state->stream = stream;
    m_state->clockOrigin = clockMicroseconds;
    m_state->count = video->nb_frames;
    if (m_state->count <= 0 && video->duration > 0 && video->avg_frame_rate.num > 0) {
        m_state->count = av_rescale_q_rnd(video->duration, video->time_base,
            av_inv_q(video->avg_frame_rate), static_cast<AVRounding>(
                AV_ROUND_UP | AV_ROUND_PASS_MINMAX));
    }
    return decodeNextFrame();
}

void VitaBinkVideoDecoder::close()
{
    if (m_state == NULL) return;
    sws_freeContext(m_state->scaler);
    m_state->scaler = NULL;
    av_packet_free(&m_state->packet);
    av_frame_free(&m_state->frame);
    avcodec_free_context(&m_state->decoder);
    avformat_close_input(&m_state->format);
    const State empty;
    *m_state = empty;
}

bool VitaBinkVideoDecoder::decodeNextFrame()
{
    if (!isOpen() || m_state->finished) return false;
    m_state->hasFrame = false;
    for (;;) {
        int result = avcodec_receive_frame(m_state->decoder, m_state->frame);
        if (result == 0) {
            ++m_state->index;
            AVStream *video = m_state->format->streams[m_state->stream];
            std::int64_t pts = RescaleTimestamp(m_state->frame->best_effort_timestamp,
                                                video->time_base);
            if (pts == AV_NOPTS_VALUE) pts = m_state->index * 33333;
            if (m_state->ptsOrigin == AV_NOPTS_VALUE) m_state->ptsOrigin = pts;
            m_state->presentation = m_state->clockOrigin + pts - m_state->ptsOrigin;
            m_state->hasFrame = true;
            return true;
        }
        if (result == AVERROR_EOF) {
            return FinishStream(m_state);
        }
        if (result != AVERROR(EAGAIN)) {
            return FinishStream(m_state);
        }
        if (m_state->draining) {
            return FinishStream(m_state);
        }
        av_packet_unref(m_state->packet);
        result = av_read_frame(m_state->format, m_state->packet);
        if (result < 0) {
            m_state->draining = true;
            if (avcodec_send_packet(m_state->decoder, NULL) < 0) {
                return FinishStream(m_state);
            }
        } else if (m_state->packet->stream_index == m_state->stream) {
            result = avcodec_send_packet(m_state->decoder, m_state->packet);
            av_packet_unref(m_state->packet);
            if (result < 0) {
                return FinishStream(m_state);
            }
        }
    }
}

bool VitaBinkVideoDecoder::isFrameReady(std::int64_t clockMicroseconds) const
{
    return m_state != NULL && m_state->hasFrame &&
           clockMicroseconds >= m_state->presentation;
}

bool VitaBinkVideoDecoder::copyFrame(void *destination, std::size_t pitch,
                                    unsigned targetHeight, unsigned x, unsigned y,
                                    PixelFormat format)
{
    if (!isOpen() || !m_state->hasFrame || destination == NULL) return false;
    const AVPixelFormat output = OutputFormat(format);
    const int bytes = av_image_get_linesize(output, width(), 0);
    if (output == AV_PIX_FMT_NONE || bytes < 0 || pitch > INT_MAX ||
        y > targetHeight || static_cast<unsigned>(height()) > targetHeight - y) return false;
    const unsigned pixelBytes = format == PixelB8G8R8X8 ? 4U :
                                format == PixelR8G8B8 ? 3U : 2U;
    if (x > (std::numeric_limits<std::size_t>::max() / pixelBytes)) return false;
    const std::size_t offset = static_cast<std::size_t>(x) * pixelBytes;
    if (offset > pitch || static_cast<std::size_t>(bytes) > pitch - offset) return false;
    if (y != 0 && pitch > std::numeric_limits<std::size_t>::max() / y) return false;
    std::uint8_t *row = static_cast<std::uint8_t *>(destination) +
                        static_cast<std::size_t>(y) * pitch + offset;
    std::uint8_t *planes[4] = {row, NULL, NULL, NULL};
    int strides[4] = {static_cast<int>(pitch), 0, 0, 0};
    m_state->scaler = sws_getCachedContext(m_state->scaler, width(), height(),
        static_cast<AVPixelFormat>(m_state->frame->format), width(), height(), output,
        SWS_FAST_BILINEAR,
        NULL, NULL, NULL);
    return m_state->scaler != NULL &&
           sws_scale(m_state->scaler, m_state->frame->data, m_state->frame->linesize,
                     0, height(), planes, strides) == height();
}

bool VitaBinkVideoDecoder::seekFrame(std::int64_t target, std::int64_t clockMicroseconds)
{
    if (!isOpen() || target < 0) return false;
    AVStream *video = m_state->format->streams[m_state->stream];
    AVRational rate = video->avg_frame_rate.num > 0 ? video->avg_frame_rate :
                                                     AVRational{30, 1};
    const std::int64_t timestamp = av_rescale_q(target, av_inv_q(rate), video->time_base);
    if (av_seek_frame(m_state->format, m_state->stream, timestamp, AVSEEK_FLAG_BACKWARD) < 0)
        return false;
    avcodec_flush_buffers(m_state->decoder);
    m_state->index = target - 1;
    m_state->clockOrigin = clockMicroseconds;
    m_state->ptsOrigin = AV_NOPTS_VALUE;
    m_state->draining = false;
    m_state->finished = false;
    return decodeNextFrame();
}

bool VitaBinkVideoDecoder::isOpen() const
{
    return m_state != NULL && m_state->format != NULL && m_state->decoder != NULL;
}

bool VitaBinkVideoDecoder::isFinished() const { return m_state == NULL || m_state->finished; }
int VitaBinkVideoDecoder::width() const { return isOpen() ? m_state->decoder->width : 0; }
int VitaBinkVideoDecoder::height() const { return isOpen() ? m_state->decoder->height : 0; }
std::int64_t VitaBinkVideoDecoder::frameIndex() const { return m_state == NULL ? -1 : m_state->index; }
std::int64_t VitaBinkVideoDecoder::frameCount() const { return m_state == NULL ? 0 : m_state->count; }
