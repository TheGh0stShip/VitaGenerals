// SPDX-License-Identifier: GPL-3.0-or-later
#include "VitaAudioOutputBuffers.h"

#include <algorithm>
#include <cassert>
#include <cstdint>

namespace {
const std::size_t SamplesPerBlock = 2048;
}

int main()
{
    VitaAudioOutputBuffers<SamplesPerBlock> buffers;
    VitaAudioOutputBuffers<SamplesPerBlock>::Block &first = buffers.next();
    assert(reinterpret_cast<std::uintptr_t>(first.data()) % 64 == 0);
    std::fill(first.begin(), first.end(), 123);

    VitaAudioOutputBuffers<SamplesPerBlock>::Block &second = buffers.next();
    assert(reinterpret_cast<std::uintptr_t>(second.data()) % 64 == 0);
    assert(first.data() != second.data());
    std::fill(second.begin(), second.begin() + 17, -321);
    std::fill(second.begin() + 17, second.end(), 0);

    assert(std::all_of(first.begin(), first.end(), [](std::int16_t sample) {
        return sample == 123;
    }));
    assert(std::all_of(second.begin(), second.begin() + 17,
                       [](std::int16_t sample) { return sample == -321; }));
    assert(std::all_of(second.begin() + 17, second.end(),
                       [](std::int16_t sample) { return sample == 0; }));
    assert(buffers.next().data() == first.data());
    return 0;
}
