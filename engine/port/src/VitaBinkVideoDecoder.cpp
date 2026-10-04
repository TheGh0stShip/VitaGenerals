// SPDX-License-Identifier: GPL-3.0-or-later
#include "VitaBinkVideoDecoder.h"

#include <algorithm>
#include <atomic>
#include <climits>
#include <deque>
#include <limits>
#include <new>
#include <pthread.h>
#include <vector>

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/imgutils.h>
#include <libavutil/pixfmt.h>
#include <libswresample/swresample.h>
#include <libswscale/swscale.h>
}

namespace {
const int AudioRate = 48000;
const int AudioChannels = 2;
const std::size_t AudioRingSamples = 2U * AudioRate * AudioChannels;
const std::size_t AudioStartupFrames = 6U * 1024U;
const std::size_t PrefetchPacketLimit = 16U;
const std::size_t PrefetchTriggerBytes = 8U * 1024U * 1024U;
const std::size_t PrefetchAbsoluteBytes = 16U * 1024U * 1024U;
const std::size_t PrefetchReadLimit = 64U;
}

struct VitaBinkVideoDecoder::State
{
    AVFormatContext *format;
    AVCodecContext *decoder;
    AVFrame *frame;
    AVPacket *packet;
    SwsContext *scaler;
    AVCodecContext *audioDecoder;
    AVFrame *audioFrame;
    AVPacket *audioPacket;
    SwrContext *resampler;
    int stream;
    int audioStream;
    std::int64_t index;
    std::int64_t count;
    std::int64_t clockOrigin;
    std::int64_t ptsOrigin;
    std::int64_t presentation;
    std::int64_t frameDuration;
    std::int64_t lastPresentation;
    std::atomic<bool> clockArmed;
    bool draining;
    bool finished;
    bool hasFrame;
    bool hasPresented;
    bool packetPending;
    bool audioPacketPending;
    bool audioDrainSent;
    std::atomic<bool> audioFailed;
    std::atomic<bool> audioFlushed;
    std::atomic<bool> demuxEnded;
    std::vector<std::int16_t> audioRing;
    std::vector<std::int16_t> audioConversion;
    std::size_t audioRead;
    std::size_t audioWrite;
    std::size_t audioCount;
    bool audioConsumerActive;
    bool audioDiscard;
    std::deque<AVPacket *> pendingVideo;
    std::size_t pendingVideoBytes;
    mutable pthread_mutex_t audioMutex;
    pthread_cond_t audioCondition;

    State() : format(NULL), decoder(NULL), frame(NULL), packet(NULL), scaler(NULL),
        audioDecoder(NULL), audioFrame(NULL), audioPacket(NULL), resampler(NULL), stream(-1),
        audioStream(-1), index(-1), count(0), clockOrigin(0),
        ptsOrigin(AV_NOPTS_VALUE), presentation(0), frameDuration(33333),
        lastPresentation(0), clockArmed(false), draining(false), finished(false),
        hasFrame(false), hasPresented(false), packetPending(false),
        audioPacketPending(false), audioDrainSent(false), audioFailed(false),
        audioFlushed(false), demuxEnded(false),
        audioRead(0), audioWrite(0), audioCount(0), audioConsumerActive(false),
        audioDiscard(false), pendingVideoBytes(0)
    {
        pthread_mutex_init(&audioMutex, NULL);
        pthread_cond_init(&audioCondition, NULL);
    }

    ~State()
    {
        pthread_cond_destroy(&audioCondition);
        pthread_mutex_destroy(&audioMutex);
    }
};

namespace {

template <typename StateType>
void MarkAudioFailed(StateType *state)
{
    if (state->audioPacket != NULL) av_packet_unref(state->audioPacket);
    state->audioPacketPending = false;
    pthread_mutex_lock(&state->audioMutex);
    state->audioDiscard = true;
    state->audioRead = state->audioWrite = state->audioCount = 0;
    pthread_cond_broadcast(&state->audioCondition);
    pthread_mutex_unlock(&state->audioMutex);
    state->audioFailed.store(true, std::memory_order_release);
    state->audioFlushed.store(true, std::memory_order_release);
}

std::int64_t RescaleTimestamp(std::int64_t timestamp, AVRational timeBase)
{
    if (timestamp == AV_NOPTS_VALUE) return AV_NOPTS_VALUE;
    return av_rescale_q(timestamp, timeBase, AVRational{1, 1000000});
}

template <typename StateType>
void ClearPendingVideo(StateType *state)
{
    while (!state->pendingVideo.empty()) {
        AVPacket *packet = state->pendingVideo.front();
        state->pendingVideo.pop_front();
        av_packet_free(&packet);
    }
    state->pendingVideoBytes = 0;
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
        case VitaBinkVideoDecoder::PixelR8G8B8: return AV_PIX_FMT_BGR24;
        case VitaBinkVideoDecoder::PixelR5G6B5: return AV_PIX_FMT_RGB565LE;
        case VitaBinkVideoDecoder::PixelX1R5G5B5: return AV_PIX_FMT_RGB555LE;
    }
    return AV_PIX_FMT_NONE;
}

template <typename StateType>
bool QueueAudio(StateType *state, const std::int16_t *samples, std::size_t count)
{
    if (samples == NULL || count == 0) return true;
    if (state->audioRing.empty() || count > state->audioRing.size()) return false;
    pthread_mutex_lock(&state->audioMutex);
    if (!state->audioConsumerActive &&
        count > state->audioRing.size() - state->audioCount) {
        state->audioDiscard = true;
    }
    while (!state->audioDiscard && count > state->audioRing.size() - state->audioCount)
        pthread_cond_wait(&state->audioCondition, &state->audioMutex);
    if (state->audioDiscard) {
        pthread_mutex_unlock(&state->audioMutex);
        return false;
    }
    const std::size_t first = std::min(count, state->audioRing.size() - state->audioWrite);
    std::copy(samples, samples + first, state->audioRing.begin() + state->audioWrite);
    std::copy(samples + first, samples + count, state->audioRing.begin());
    state->audioWrite = (state->audioWrite + count) % state->audioRing.size();
    state->audioCount += count;
    pthread_mutex_unlock(&state->audioMutex);
    return true;
}

enum AudioReceiveResult
{
    AudioNeedsInput,
    AudioDecoderEnd,
    AudioReceiveFailed
};

template <typename StateType>
AudioReceiveResult ReceiveAudio(StateType *state)
{
    if (state->audioDecoder == NULL || state->audioFrame == NULL ||
        state->resampler == NULL) return AudioReceiveFailed;
    for (;;) {
        const int result = avcodec_receive_frame(state->audioDecoder, state->audioFrame);
        if (result == AVERROR(EAGAIN)) return AudioNeedsInput;
        if (result == AVERROR_EOF) return AudioDecoderEnd;
        if (result < 0) return AudioReceiveFailed;
        const int outputFrames = swr_get_out_samples(state->resampler,
                                                      state->audioFrame->nb_samples);
        if (outputFrames < 0) {
            av_frame_unref(state->audioFrame);
            return AudioReceiveFailed;
        }
        if (outputFrames == 0) {
            av_frame_unref(state->audioFrame);
            continue;
        }
        state->audioConversion.resize(static_cast<std::size_t>(outputFrames) * AudioChannels);
        std::uint8_t *output[] = {
            reinterpret_cast<std::uint8_t *>(state->audioConversion.data())
        };
        const int frames = swr_convert(state->resampler, output, outputFrames,
            reinterpret_cast<const std::uint8_t *const *>(
                state->audioFrame->extended_data),
            state->audioFrame->nb_samples);
        if (frames < 0) {
            av_frame_unref(state->audioFrame);
            return AudioReceiveFailed;
        }
        if (frames > 0)
            QueueAudio(state, state->audioConversion.data(),
                       static_cast<std::size_t>(frames) * AudioChannels);
        av_frame_unref(state->audioFrame);
    }
}

enum AudioSendResult
{
    AudioPacketAccepted,
    AudioPacketPending,
    AudioSendFailed
};

template <typename StateType>
AudioSendResult PumpAudioPacket(StateType *state)
{
    if (!state->audioPacketPending) return AudioPacketAccepted;
    for (unsigned attempt = 0; attempt != 2; ++attempt) {
        const int result = avcodec_send_packet(state->audioDecoder, state->audioPacket);
        if (result == AVERROR(EAGAIN)) {
            if (ReceiveAudio(state) == AudioReceiveFailed) return AudioSendFailed;
            continue;
        }
        av_packet_unref(state->audioPacket);
        state->audioPacketPending = false;
        if (result < 0) return AudioSendFailed;
        if (ReceiveAudio(state) == AudioReceiveFailed) return AudioSendFailed;
        return AudioPacketAccepted;
    }
    return AudioPacketPending;
}

template <typename StateType>
AudioSendResult SendAudioPacket(StateType *state, const AVPacket *packet)
{
    if (state->audioDecoder == NULL) return AudioPacketAccepted;
    AudioSendResult result = PumpAudioPacket(state);
    if (result != AudioPacketAccepted) return result;
    if (av_packet_ref(state->audioPacket, packet) < 0) return AudioSendFailed;
    state->audioPacketPending = true;
    return PumpAudioPacket(state);
}

template <typename StateType>
bool FlushAudio(StateType *state)
{
    if (state->audioFailed.load(std::memory_order_acquire)) return true;
    if (state->audioFlushed.load(std::memory_order_acquire)) return true;
    if (state->audioDecoder != NULL) {
        const AudioSendResult pending = PumpAudioPacket(state);
        if (pending == AudioPacketPending) return false;
        if (pending == AudioSendFailed) {
            MarkAudioFailed(state);
            return true;
        }
        if (!state->audioDrainSent) {
            const int result = avcodec_send_packet(state->audioDecoder, NULL);
            if (result == AVERROR(EAGAIN)) {
                ReceiveAudio(state);
                return false;
            }
            if (result < 0 && result != AVERROR_EOF) {
                MarkAudioFailed(state);
                return true;
            }
            state->audioDrainSent = true;
        }
        const AudioReceiveResult received = ReceiveAudio(state);
        if (received == AudioReceiveFailed) {
            MarkAudioFailed(state);
            return true;
        }
        if (received == AudioNeedsInput) return false;
    }
    if (state->resampler != NULL) {
        for (;;) {
            const int capacity = swr_get_out_samples(state->resampler, 0);
            if (capacity <= 0) break;
            state->audioConversion.resize(static_cast<std::size_t>(capacity) * AudioChannels);
            std::uint8_t *output[] = {
                reinterpret_cast<std::uint8_t *>(state->audioConversion.data())
            };
            const int frames = swr_convert(state->resampler, output, capacity, NULL, 0);
            if (frames <= 0 || !QueueAudio(state, state->audioConversion.data(),
                    static_cast<std::size_t>(frames) * AudioChannels)) break;
        }
    }
    state->audioFlushed.store(true, std::memory_order_release);
    return true;
}

template <typename StateType>
bool PrefetchStartupAudio(StateType *state)
{
    if (state->audioStream < 0) return true;
    AVPacket *packet = av_packet_alloc();
    if (packet == NULL) return false;
    bool success = true;
    std::size_t packetsRead = 0;
    while (state->audioCount / AudioChannels < AudioStartupFrames &&
           state->pendingVideo.size() < PrefetchPacketLimit &&
           state->pendingVideoBytes < PrefetchTriggerBytes &&
           packetsRead < PrefetchReadLimit) {
        if (state->audioPacketPending) {
            const AudioSendResult pending = PumpAudioPacket(state);
            if (pending == AudioPacketPending) continue;
            if (pending == AudioSendFailed) {
                MarkAudioFailed(state);
                break;
            }
        }
        av_packet_unref(packet);
        if (av_read_frame(state->format, packet) < 0) {
            state->demuxEnded.store(true, std::memory_order_release);
            FlushAudio(state);
            break;
        }
        ++packetsRead;
        if (packet->stream_index == state->audioStream) {
            if (SendAudioPacket(state, packet) == AudioSendFailed) {
                MarkAudioFailed(state);
                break;
            }
        } else if (packet->stream_index == state->stream) {
            const std::size_t bytes = packet->size > 0 ?
                static_cast<std::size_t>(packet->size) : 0U;
            if (bytes > PrefetchAbsoluteBytes - state->pendingVideoBytes) {
                success = false;
                break;
            }
            AVPacket *copy = av_packet_clone(packet);
            if (copy == NULL) {
                success = false;
                break;
            }
            state->pendingVideo.push_back(copy);
            state->pendingVideoBytes += bytes;
        }
    }
    av_packet_free(&packet);
    if (success && state->audioCount / AudioChannels < AudioStartupFrames &&
        !state->demuxEnded.load(std::memory_order_acquire)) {
        pthread_mutex_lock(&state->audioMutex);
        state->audioDiscard = true;
        state->audioRead = state->audioWrite = state->audioCount = 0;
        pthread_mutex_unlock(&state->audioMutex);
    }
    return success;
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
    m_state->clockArmed.store(false, std::memory_order_release);
    m_state->count = video->nb_frames;
    const AVRational rate = video->avg_frame_rate.num > 0 ? video->avg_frame_rate :
                                                              AVRational{30, 1};
    m_state->frameDuration = std::max<std::int64_t>(1, av_rescale_q(
        1, av_inv_q(rate), AVRational{1, 1000000}));
    if (m_state->count <= 0 && video->duration > 0 && video->avg_frame_rate.num > 0) {
        m_state->count = av_rescale_q_rnd(video->duration, video->time_base,
            av_inv_q(video->avg_frame_rate), static_cast<AVRounding>(
                AV_ROUND_UP | AV_ROUND_PASS_MINMAX));
    }
    const int audioStream = av_find_best_stream(m_state->format, AVMEDIA_TYPE_AUDIO,
                                                 -1, -1, NULL, 0);
    if (audioStream >= 0) {
        AVStream *audio = m_state->format->streams[audioStream];
        const AVCodec *audioCodec = avcodec_find_decoder(audio->codecpar->codec_id);
        m_state->audioDecoder = audioCodec == NULL ? NULL : avcodec_alloc_context3(audioCodec);
        if (m_state->audioDecoder != NULL &&
            avcodec_parameters_to_context(m_state->audioDecoder, audio->codecpar) >= 0 &&
            avcodec_open2(m_state->audioDecoder, audioCodec, NULL) >= 0) {
            m_state->audioFrame = av_frame_alloc();
            m_state->audioPacket = av_packet_alloc();
            AVChannelLayout outputLayout = {};
            av_channel_layout_default(&outputLayout, AudioChannels);
            AVChannelLayout inputLayout = {};
            if (av_channel_layout_copy(&inputLayout,
                    &m_state->audioDecoder->ch_layout) >= 0 &&
                swr_alloc_set_opts2(&m_state->resampler, &outputLayout,
                    AV_SAMPLE_FMT_S16, AudioRate, &inputLayout,
                    m_state->audioDecoder->sample_fmt,
                    std::max(1, m_state->audioDecoder->sample_rate), 0, NULL) >= 0 &&
                m_state->resampler != NULL && swr_init(m_state->resampler) >= 0 &&
                m_state->audioFrame != NULL && m_state->audioPacket != NULL) {
                m_state->audioStream = audioStream;
                m_state->audioRing.assign(AudioRingSamples, 0);
            }
            av_channel_layout_uninit(&inputLayout);
            av_channel_layout_uninit(&outputLayout);
        }
        if (m_state->audioStream < 0) {
            swr_free(&m_state->resampler);
            av_packet_free(&m_state->audioPacket);
            av_frame_free(&m_state->audioFrame);
            avcodec_free_context(&m_state->audioDecoder);
        }
    }
    if (!decodeNextFrame()) return false;
    if (!PrefetchStartupAudio(m_state)) {
        close();
        return false;
    }
    return true;
}

void VitaBinkVideoDecoder::close()
{
    if (m_state == NULL) return;
    ClearPendingVideo(m_state);
    sws_freeContext(m_state->scaler);
    m_state->scaler = NULL;
    swr_free(&m_state->resampler);
    av_packet_free(&m_state->audioPacket);
    av_frame_free(&m_state->audioFrame);
    avcodec_free_context(&m_state->audioDecoder);
    av_packet_free(&m_state->packet);
    av_frame_free(&m_state->frame);
    avcodec_free_context(&m_state->decoder);
    avformat_close_input(&m_state->format);
    m_state->~State();
    new (m_state) State;
}

void VitaBinkVideoDecoder::startPresentation(std::int64_t clockMicroseconds)
{
    if (!isOpen()) return;
    m_state->clockOrigin = clockMicroseconds;
    m_state->clockArmed.store(true, std::memory_order_release);
}

bool VitaBinkVideoDecoder::presentationStarted() const
{
    return isOpen() && m_state->clockArmed.load(std::memory_order_acquire);
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
            m_state->presentation = pts - m_state->ptsOrigin;
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
        if (m_state->audioPacketPending) {
            const AudioSendResult audio = PumpAudioPacket(m_state);
            if (audio == AudioPacketPending) continue;
            if (audio == AudioSendFailed) MarkAudioFailed(m_state);
        }
        if (m_state->packetPending) {
            result = avcodec_send_packet(m_state->decoder, m_state->packet);
            if (result == AVERROR(EAGAIN)) continue;
            av_packet_unref(m_state->packet);
            m_state->packetPending = false;
            if (result < 0) return FinishStream(m_state);
            continue;
        }
        if (!m_state->pendingVideo.empty()) {
            AVPacket *pending = m_state->pendingVideo.front();
            m_state->pendingVideo.pop_front();
            const std::size_t bytes = pending->size > 0 ?
                static_cast<std::size_t>(pending->size) : 0U;
            m_state->pendingVideoBytes -= std::min(bytes, m_state->pendingVideoBytes);
            av_packet_move_ref(m_state->packet, pending);
            av_packet_free(&pending);
            m_state->packetPending = true;
            continue;
        }
        if (m_state->demuxEnded.load(std::memory_order_acquire)) {
            if (!FlushAudio(m_state)) continue;
            result = avcodec_send_packet(m_state->decoder, NULL);
            if (result == AVERROR(EAGAIN)) continue;
            if (result < 0 && result != AVERROR_EOF)
                return FinishStream(m_state);
            m_state->draining = true;
            continue;
        }
        av_packet_unref(m_state->packet);
        result = av_read_frame(m_state->format, m_state->packet);
        if (result < 0) {
            m_state->demuxEnded.store(true, std::memory_order_release);
            FlushAudio(m_state);
            continue;
        } else if (m_state->packet->stream_index == m_state->stream) {
            m_state->packetPending = true;
        } else if (m_state->packet->stream_index == m_state->audioStream) {
            if (SendAudioPacket(m_state, m_state->packet) == AudioSendFailed)
                MarkAudioFailed(m_state);
            av_packet_unref(m_state->packet);
        }
    }
}

bool VitaBinkVideoDecoder::isFrameReady(std::int64_t clockMicroseconds) const
{
    return m_state != NULL && m_state->hasFrame && presentationStarted() &&
           clockMicroseconds >= m_state->clockOrigin + m_state->presentation;
}

bool VitaBinkVideoDecoder::shouldDropFrame(std::int64_t clockMicroseconds) const
{
    if (!isFrameReady(clockMicroseconds) || !m_state->hasPresented ||
        m_state->index >= m_state->count - 1) return false;
    const std::int64_t elapsed = clockMicroseconds - m_state->clockOrigin;
    const std::int64_t late = elapsed - m_state->presentation;
    if (late < 0) return false;
    if (clockMicroseconds - m_state->lastPresentation >= m_state->frameDuration * 2)
        return false;
    const std::int64_t threshold = std::max<std::int64_t>(m_state->frameDuration, 50000);
    const bool audioPressure = hasAudio() && !audioComplete() &&
                               queuedAudioFrames() < 1024U;
    return late > threshold || audioPressure;
}

void VitaBinkVideoDecoder::markFramePresented(std::int64_t clockMicroseconds)
{
    if (!isOpen()) return;
    m_state->lastPresentation = clockMicroseconds;
    m_state->hasPresented = true;
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
    const bool wasArmed = m_state->clockArmed.load(std::memory_order_acquire);
    AVStream *video = m_state->format->streams[m_state->stream];
    AVRational rate = video->avg_frame_rate.num > 0 ? video->avg_frame_rate :
                                                     AVRational{30, 1};
    const std::int64_t timestamp = av_rescale_q(target, av_inv_q(rate), video->time_base);
    if (av_seek_frame(m_state->format, m_state->stream, timestamp, AVSEEK_FLAG_BACKWARD) < 0)
        return false;
    avcodec_flush_buffers(m_state->decoder);
    if (m_state->audioDecoder != NULL) avcodec_flush_buffers(m_state->audioDecoder);
    pthread_mutex_lock(&m_state->audioMutex);
    m_state->audioRead = m_state->audioWrite = m_state->audioCount = 0;
    pthread_mutex_unlock(&m_state->audioMutex);
    ClearPendingVideo(m_state);
    av_packet_unref(m_state->packet);
    if (m_state->audioPacket != NULL) av_packet_unref(m_state->audioPacket);
    m_state->packetPending = false;
    m_state->audioPacketPending = false;
    m_state->audioDrainSent = false;
    m_state->index = target - 1;
    m_state->clockOrigin = clockMicroseconds;
    m_state->clockArmed.store(wasArmed, std::memory_order_release);
    m_state->ptsOrigin = AV_NOPTS_VALUE;
    m_state->draining = false;
    m_state->finished = false;
    m_state->hasPresented = false;
    if (m_state->resampler != NULL) {
        swr_close(m_state->resampler);
        if (swr_init(m_state->resampler) < 0) return false;
    }
    m_state->audioFlushed.store(false, std::memory_order_release);
    m_state->demuxEnded.store(false, std::memory_order_release);
    return decodeNextFrame();
}

bool VitaBinkVideoDecoder::hasAudio() const
{
    return m_state != NULL && m_state->audioStream >= 0;
}

std::size_t VitaBinkVideoDecoder::queuedAudioFrames() const
{
    if (!hasAudio()) return 0;
    pthread_mutex_lock(&m_state->audioMutex);
    const std::size_t frames = m_state->audioCount / AudioChannels;
    pthread_mutex_unlock(&m_state->audioMutex);
    return frames;
}

std::size_t VitaBinkVideoDecoder::readAudioFrames(std::int16_t *destination,
                                                  std::size_t frames)
{
    if (!hasAudio() || destination == NULL || frames == 0) return 0;
    pthread_mutex_lock(&m_state->audioMutex);
    const std::size_t samples = std::min(frames * AudioChannels, m_state->audioCount);
    const std::size_t first = std::min(samples, m_state->audioRing.size() - m_state->audioRead);
    std::copy(m_state->audioRing.begin() + m_state->audioRead,
              m_state->audioRing.begin() + m_state->audioRead + first, destination);
    std::copy(m_state->audioRing.begin(), m_state->audioRing.begin() + samples - first,
              destination + first);
    m_state->audioRead = (m_state->audioRead + samples) % m_state->audioRing.size();
    m_state->audioCount -= samples;
    pthread_cond_signal(&m_state->audioCondition);
    pthread_mutex_unlock(&m_state->audioMutex);
    return samples / AudioChannels;
}

bool VitaBinkVideoDecoder::audioComplete() const
{
    return !hasAudio() || m_state->audioFailed.load(std::memory_order_acquire) ||
                          (m_state->demuxEnded.load(std::memory_order_acquire) &&
                           m_state->audioFlushed.load(std::memory_order_acquire) &&
                           queuedAudioFrames() == 0);
}

bool VitaBinkVideoDecoder::enableAudioOutput()
{
    if (!hasAudio()) return false;
    pthread_mutex_lock(&m_state->audioMutex);
    const bool enabled = !m_state->audioDiscard;
    m_state->audioConsumerActive = enabled;
    pthread_mutex_unlock(&m_state->audioMutex);
    return enabled;
}

void VitaBinkVideoDecoder::disableAudioOutput()
{
    if (m_state == NULL) return;
    pthread_mutex_lock(&m_state->audioMutex);
    m_state->audioConsumerActive = false;
    m_state->audioDiscard = true;
    m_state->audioRead = m_state->audioWrite = m_state->audioCount = 0;
    pthread_cond_broadcast(&m_state->audioCondition);
    pthread_mutex_unlock(&m_state->audioMutex);
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
std::int64_t VitaBinkVideoDecoder::frameDurationMicroseconds() const
{
    return m_state == NULL ? 33333 : m_state->frameDuration;
}
