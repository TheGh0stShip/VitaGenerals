// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef VITA_AUDIO_OUTPUT_BUFFERS_H
#define VITA_AUDIO_OUTPUT_BUFFERS_H

#include <array>
#include <cstddef>
#include <cstdint>

// sceAudioOutOutput may retain the submitted pointer until the next call.
// Alternating storage lets the producer fill one block without modifying the
// block still owned by the audio device. Drain the port before destroying it.
template <std::size_t Samples> class VitaAudioOutputBuffers
{
    static_assert((Samples * sizeof(std::int16_t)) % 64 == 0,
                  "Vita audio blocks must preserve cache-line alignment");

public:
    typedef std::array<std::int16_t, Samples> Block;

    VitaAudioOutputBuffers() : m_blocks(), m_next(0) {}

    Block &next()
    {
        Block &block = m_blocks[m_next];
        m_next ^= 1U;
        return block;
    }

private:
    alignas(64) Block m_blocks[2];
    unsigned m_next;
};

#endif
