// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#ifndef __VIDEODEVICE_BINKDEVICE_H_
#define __VIDEODEVICE_BINKDEVICE_H_

#include "Common/GameType.h"
#include "Common/NameKeyType.h"
#include "Common/ScienceType.h"
#include "GameClient/VideoPlayer.h"

class VitaBinkVideoDecoder;
class VitaBinkAudioOutput;
class BinkVideoPlayer;

class BinkVideoStream : public VideoStream
{
    friend class BinkVideoPlayer;
protected:
    VitaBinkVideoDecoder *m_decoder;
    VitaBinkAudioOutput *m_audioOutput;
    BinkVideoStream();
    virtual ~BinkVideoStream();
public:
    virtual void update();
    virtual Bool isFrameReady();
    virtual void frameDecompress();
    virtual void frameRender(VideoBuffer *buffer);
    virtual void frameNext();
    virtual Int frameIndex();
    virtual Int frameCount();
    virtual void frameGoto(Int index);
    virtual Int height();
    virtual Int width();
};

class BinkVideoPlayer : public VideoPlayer
{
protected:
    VideoStreamInterface *createStream(VitaBinkVideoDecoder *decoder);
public:
    BinkVideoPlayer();
    virtual ~BinkVideoPlayer();
    virtual void init();
    virtual void reset();
    virtual void update();
    virtual void deinit();
    virtual void loseFocus();
    virtual void regainFocus();
    virtual VideoStreamInterface *open(AsciiString movieTitle);
    virtual VideoStreamInterface *load(AsciiString movieTitle);
    virtual void notifyVideoPlayerOfNewProvider(Bool nowHasValid);
    virtual void initializeBinkWithMiles();
};

#endif
