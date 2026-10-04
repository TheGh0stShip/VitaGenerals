// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef VITA_BINK_VIDEO_DECODER_H
#define VITA_BINK_VIDEO_DECODER_H

#include <cstddef>
#include <cstdint>

class VitaBinkVideoDecoder
{
public:
    enum PixelFormat
    {
        PixelB8G8R8X8,
        PixelR8G8B8,
        PixelR5G6B5,
        PixelX1R5G5B5
    };

    VitaBinkVideoDecoder();
    ~VitaBinkVideoDecoder();

    VitaBinkVideoDecoder(const VitaBinkVideoDecoder &) = delete;
    VitaBinkVideoDecoder &operator=(const VitaBinkVideoDecoder &) = delete;

    bool open(const char *path, std::int64_t clockMicroseconds);
    void close();
    void startPresentation(std::int64_t clockMicroseconds);
    bool presentationStarted() const;
    bool decodeNextFrame();
    bool isFrameReady(std::int64_t clockMicroseconds) const;
    bool shouldDropFrame(std::int64_t clockMicroseconds) const;
    void markFramePresented(std::int64_t clockMicroseconds);
    bool copyFrame(void *destination, std::size_t pitch, unsigned height,
                   unsigned x, unsigned y, PixelFormat format);
    bool seekFrame(std::int64_t frameIndex, std::int64_t clockMicroseconds);

    bool hasAudio() const;
    std::size_t queuedAudioFrames() const;
    std::size_t readAudioFrames(std::int16_t *destination, std::size_t frames);
    bool audioComplete() const;
    bool enableAudioOutput();
    void disableAudioOutput();

    bool isOpen() const;
    bool isFinished() const;
    int width() const;
    int height() const;
    std::int64_t frameIndex() const;
    std::int64_t frameCount() const;
    std::int64_t frameDurationMicroseconds() const;

private:
    struct State;
    State *m_state;
};

#endif
