// SPDX-License-Identifier: GPL-3.0-or-later
#include <psp2/kernel/threadmgr/thread.h>
#include "PreRTS.h"
#include "thread.h"
void ThreadClass::Switch_Thread(){
 if(sceKernelDelayThread(1000)<0) std::abort();
}
