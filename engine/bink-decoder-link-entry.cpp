// SPDX-License-Identifier: GPL-3.0-or-later
#include "VitaBinkVideoDecoder.h"
#include "VitaBinkAudioOutput.h"

int main()
{
    VitaBinkVideoDecoder decoder;
    VitaBinkAudioOutput output(&decoder);
    return decoder.isOpen() || decoder.width() != 0 || output.isRunning() ? 1 : 0;
}
