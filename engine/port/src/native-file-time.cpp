// SPDX-License-Identifier: GPL-3.0-or-later
#include <cstdio>
#include <cstdint>
#include <cstddef>
#include <psp2/io/stat.h>
#include <psp2/rtc.h>
#include "packed-file-time.h"
extern "C" {
#include "thirdparty/newlib-vitadescriptor.h"
}
static_assert(sizeof(DescriptorTypes)==1,"Pinned newlib descriptor enum ABI changed");
static_assert(sizeof(DescriptorTranslation)==20,"Pinned descriptor layout changed");
static_assert(offsetof(DescriptorTranslation,type)==4,"Descriptor type offset changed");
static_assert(offsetof(DescriptorTranslation,ref_count)==8,"Descriptor reference offset changed");
struct DescriptorRef {
 DescriptorTranslation* value;
 explicit DescriptorRef(FILE* file):value(__vita_fd_grab(fileno(file))){}
 ~DescriptorRef(){if(value)__vita_fd_drop(value);}
 DescriptorRef(const DescriptorRef&)=delete;
 DescriptorRef& operator=(const DescriptorRef&)=delete;
};
uint32_t native_raw_packed_time(FILE* file)
{
 DescriptorRef fd(file);
 if(!fd.value || fd.value->type!=VITA_DESCRIPTOR_FILE)return 0;
 SceIoStat info={};
 if(sceIoGetstatByFd(fd.value->sce_uid,&info)<0 || info.st_mtime.microsecond>999999)return 0;
 SceUInt64 seconds=0;
 if(sceRtcGetTime64_t(&info.st_mtime,&seconds)<0 || seconds>INT64_MAX)return 0;
 uint32_t packed=0;
 return generals_file_time::from_epoch(static_cast<int64_t>(seconds),info.st_mtime.microsecond*1000u,packed)?packed:0;
}
bool native_raw_set_packed_time(FILE* file,uint32_t packed)
{
 int64_t seconds=0;
 if(!generals_file_time::to_epoch(packed,seconds))return false;
 DescriptorRef fd(file);
 if(!fd.value || fd.value->type!=VITA_DESCRIPTOR_FILE)return false;
 SceIoStat info={};
 if(sceRtcSetTime64_t(&info.st_mtime,static_cast<SceUInt64>(seconds))<0)return false;
 return sceIoChstatByFd(fd.value->sce_uid,&info,SCE_CST_MT)==0;
}
