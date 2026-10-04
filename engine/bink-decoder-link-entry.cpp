// SPDX-License-Identifier: GPL-3.0-or-later
#include "VitaBinkVideoDecoder.h"

int main()
{
    VitaBinkVideoDecoder decoder;
    return decoder.isOpen() || decoder.width() != 0 ? 1 : 0;
}
