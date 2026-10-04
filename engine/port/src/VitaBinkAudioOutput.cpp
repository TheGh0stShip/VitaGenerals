// SPDX-License-Identifier: GPL-3.0-or-later
#include "VitaBinkAudioOutput.h"

#include "VitaAudioOutputBuffers.h"
#include "VitaBinkVideoDecoder.h"

#include <algorithm>
#include <cstdint>

#include <psp2/audioout.h>
#include <psp2/kernel/threadmgr.h>

namespace {
const std::size_t FramesPerBuffer = 1024;
const std::size_t StartupFrames = FramesPerBuffer * 6;
const int AudioRate = 48000;
}

VitaBinkAudioOutput::VitaBinkAudioOutput(VitaBinkVideoDecoder *decoder) :
    m_decoder(decoder), m_thread(), m_stop(false), m_running(false), m_port(-1),
    m_threadCreated(false)
{
}

VitaBinkAudioOutput::~VitaBinkAudioOutput()
{
    stop();
}

bool VitaBinkAudioOutput::start()
{
    if (m_threadCreated || m_decoder == NULL || !m_decoder->hasAudio()) return false;
    const SceAudioOutPortType ports[] = {
        SCE_AUDIO_OUT_PORT_TYPE_MAIN,
        SCE_AUDIO_OUT_PORT_TYPE_VOICE,
        SCE_AUDIO_OUT_PORT_TYPE_BGM
    };
    for (std::size_t index = 0; index != sizeof(ports) / sizeof(ports[0]); ++index) {
        m_port = sceAudioOutOpenPort(ports[index], FramesPerBuffer, AudioRate,
                                     SCE_AUDIO_OUT_MODE_STEREO);
        if (m_port >= 0) break;
    }
    if (m_port < 0) return false;
    if (!m_decoder->enableAudioOutput()) {
        sceAudioOutReleasePort(m_port);
        m_port = -1;
        return false;
    }
    m_stop.store(false, std::memory_order_release);
    if (pthread_create(&m_thread, NULL, threadEntry, this) != 0) {
        sceAudioOutReleasePort(m_port);
        m_port = -1;
        m_decoder->disableAudioOutput();
        return false;
    }
    m_threadCreated = true;
    return true;
}

void VitaBinkAudioOutput::stop()
{
    if (m_decoder != NULL) m_decoder->disableAudioOutput();
    if (m_threadCreated) {
        m_stop.store(true, std::memory_order_release);
        pthread_join(m_thread, NULL);
        m_threadCreated = false;
    }
    if (m_port >= 0) {
        sceAudioOutReleasePort(m_port);
        m_port = -1;
    }
    m_running.store(false, std::memory_order_release);
}

bool VitaBinkAudioOutput::isRunning() const
{
    return m_running.load(std::memory_order_acquire);
}

void *VitaBinkAudioOutput::threadEntry(void *context)
{
    static_cast<VitaBinkAudioOutput *>(context)->run();
    return NULL;
}

void VitaBinkAudioOutput::run()
{
    m_running.store(true, std::memory_order_release);
    VitaAudioOutputBuffers<FramesPerBuffer * 2> buffers;
    bool started = false;
    while (!m_stop.load(std::memory_order_acquire)) {
        if (!m_decoder->presentationStarted()) {
            sceKernelDelayThread(1000);
            continue;
        }
        const std::size_t queued = m_decoder->queuedAudioFrames();
        const bool complete = m_decoder->audioComplete();
        if (!started && queued < StartupFrames && !complete) {
            sceKernelDelayThread(1000);
            continue;
        }
        if (queued == 0) {
            if (complete) break;
            sceKernelDelayThread(1000);
            continue;
        }
        if (queued < FramesPerBuffer && !complete) {
            sceKernelDelayThread(1000);
            continue;
        }
        started = true;
        VitaAudioOutputBuffers<FramesPerBuffer * 2>::Block &output = buffers.next();
        const std::size_t copied = m_decoder->readAudioFrames(output.data(),
                                                               FramesPerBuffer);
        std::fill(output.begin() + copied * 2, output.end(), 0);
        if (copied != 0 && sceAudioOutOutput(m_port, output.data()) < 0) {
            m_decoder->disableAudioOutput();
            break;
        }
    }
    if (m_port >= 0) sceAudioOutOutput(m_port, NULL);
    m_running.store(false, std::memory_order_release);
}
