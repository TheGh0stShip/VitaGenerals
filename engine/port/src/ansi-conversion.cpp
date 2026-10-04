// SPDX-License-Identifier: GPL-3.0-or-later
#include <iconv.h>
#include <cerrno>
#include <climits>
#include <cstdint>
#include <cstring>
#include <vector>
#ifndef GENERALS_WWLIB_ANSI_ENCODING
#error Select the original installation ANSI encoding explicitly
#endif
namespace wwstring_detail {
int utf16_to_ansi(const char16_t *source,char *output,int capacity,bool *unmapped) {
 if(unmapped)*unmapped=false;
 if(!source || capacity<0)return 0;
 std::vector<char> input;
 for(size_t index=0;source[index];++index){
  if(input.size()>size_t(INT_MAX)-2)return 0;
  const uint16_t unit=source[index];
  input.push_back(char(unit&255));input.push_back(char(unit>>8));
 }
 iconv_t descriptor=iconv_open(GENERALS_WWLIB_ANSI_ENCODING,"UTF-16LE");
 if(descriptor==iconv_t(-1))return 0;
 std::vector<char> converted;
 char *cursor=input.data();size_t remaining=input.size();bool replaced=false,failed=false;
 while(remaining){
  char chunk[64];char *destination=chunk;size_t available=sizeof(chunk);
  errno=0;const size_t result=iconv(descriptor,&cursor,&remaining,&destination,&available);
  const size_t produced=sizeof(chunk)-available;
  if(converted.size()>size_t(INT_MAX)-1-produced){failed=true;break;}
  converted.insert(converted.end(),chunk,chunk+produced);
  if(result!=size_t(-1))continue;
  if(errno==E2BIG)continue;
  if((errno!=EILSEQ && errno!=EINVAL)||remaining<2){failed=true;break;}
  const unsigned unit=static_cast<unsigned char>(cursor[0])|(unsigned(static_cast<unsigned char>(cursor[1]))<<8);
  size_t skipped=2;
  if(unit>=0xd800 && unit<=0xdbff && remaining>=4){
   const unsigned next=static_cast<unsigned char>(cursor[2])|(unsigned(static_cast<unsigned char>(cursor[3]))<<8);
   if(next>=0xdc00 && next<=0xdfff)skipped=4;
  }
  converted.push_back('?');replaced=true;cursor+=skipped;remaining-=skipped;
  if(iconv(descriptor,nullptr,nullptr,nullptr,nullptr)==size_t(-1)){failed=true;break;}
 }
 // Flush any trailing encoding state before appending the C terminator.
 if(!failed){char chunk[64];char *destination=chunk;size_t available=sizeof(chunk);
  if(iconv(descriptor,nullptr,nullptr,&destination,&available)==size_t(-1))failed=true;
  else converted.insert(converted.end(),chunk,destination);
 }
 iconv_close(descriptor);
 if(failed || converted.size()>=size_t(INT_MAX))return 0;
 converted.push_back(0);if(unmapped)*unmapped=replaced;
 const int required=int(converted.size());
 if(output){if(capacity<required)return 0;std::memcpy(output,converted.data(),converted.size());}
 return required;
}
}
