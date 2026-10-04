// SPDX-License-Identifier: GPL-3.0-or-later
#include <cstddef>
#include <thread>
#include <chrono>
#include "thread.h"
void ThreadClass::Switch_Thread(){std::this_thread::sleep_for(std::chrono::milliseconds(1));}
