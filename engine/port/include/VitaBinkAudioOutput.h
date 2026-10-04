// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef VITA_BINK_AUDIO_OUTPUT_H
#define VITA_BINK_AUDIO_OUTPUT_H

#include <atomic>
#include <pthread.h>

class VitaBinkVideoDecoder;

class VitaBinkAudioOutput
{
public:
    explicit VitaBinkAudioOutput(VitaBinkVideoDecoder *decoder);
    ~VitaBinkAudioOutput();

    VitaBinkAudioOutput(const VitaBinkAudioOutput &) = delete;
    VitaBinkAudioOutput &operator=(const VitaBinkAudioOutput &) = delete;

    bool start();
    void stop();
    bool isRunning() const;

private:
    static void *threadEntry(void *context);
    void run();

    VitaBinkVideoDecoder *m_decoder;
    pthread_t m_thread;
    std::atomic<bool> m_stop;
    std::atomic<bool> m_running;
    int m_port;
    bool m_threadCreated;
};

#endif
