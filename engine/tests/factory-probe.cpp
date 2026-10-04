// SPDX-License-Identifier: GPL-3.0-or-later
#include "ffactory.h"
#include "bufffile.h"
#include <cstdlib>
#include <cstdio>
#include <cstring>
static void check(bool v){if(!v)std::abort();}
int main(){const char* path="factory-test.dat";unsigned char expected[4099];for(unsigned i=0;i<sizeof(expected);++i)expected[i]=(i*17u)^0xa5u;{RawFileClass f(path);check(f.Open(FileClass::WRITE));check(f.Write(expected,sizeof(expected))==sizeof(expected));}SimpleFileFactoryClass local;local.Set_Sub_Directory("./");SimpleFileFactoryClass search;search.Set_Sub_Directory("nonexistent/;./");for(int repeat=0;repeat<48;++repeat){FileFactoryClass* owner=repeat%3==0?_TheFileFactory:repeat%3==1?static_cast<FileFactoryClass*>(&local):static_cast<FileFactoryClass*>(&search);file_auto_ptr f(owner,repeat%3 ? "factory-test.dat" : path);if(!f->Open(FileClass::READ)){fprintf(stderr,"factory open failed cycle=%d path=%s\n",repeat,f->File_Name());std::abort();}unsigned char actual[4099];for(unsigned off=0;off<sizeof(actual);){unsigned n=sizeof(actual)-off;if(n>137)n=137;check(f->Read(actual+off,n)==static_cast<int>(n));off+=n;}check(std::memcmp(actual,expected,sizeof(actual))==0);check(f->Seek(1023,SEEK_SET)==1023);check(f->Read(actual,2051)==2051);check(std::memcmp(actual,expected+1023,2051)==0);check(f->Seek(-3,SEEK_END)==4096);check(f->Read(actual,9)==3);check(std::memcmp(actual,expected+4096,3)==0);}std::remove(path);puts("PASS factory ownership and buffered sequential/random reads across48cycles including search-path fallback");}
