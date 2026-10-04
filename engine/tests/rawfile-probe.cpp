// SPDX-License-Identifier: GPL-3.0-or-later
#include "RAWFILE.H"
#include <cstdlib>
#include <cstring>
#include <cstdio>
#include <sys/stat.h>
#include <fcntl.h>
static void check(bool value){if(!value)std::abort();}
struct ObservedFile : RawFileClass { int errors=0; ObservedFile(const char* p):RawFileClass(p){} void Error(int,int,const char*) override {++errors;} };
static void check_open_modes() {
    const char* path="rawfile-modes.dat";
    std::remove(path);
    RawFileClass file(path);
    check(!file.Open(FileClass::READ));
    check(file.Open(FileClass::READ|FileClass::WRITE));
    check(file.Seek(0,SEEK_CUR)==0);
    const unsigned char original[]={0,13,10,26,255,42};
    check(file.Write(original,sizeof(original))==sizeof(original));
    check(file.Seek(0,SEEK_SET)==0);
    unsigned char bytes[sizeof(original)]={};
    check(file.Read(bytes,sizeof(bytes))==sizeof(bytes));
    check(std::memcmp(bytes,original,sizeof(bytes))==0);
    file.Close();
    for(int cycle=0;cycle<32;++cycle) {
        check(file.Open(FileClass::READ|FileClass::WRITE));
        check(file.Seek(0,SEEK_CUR)==0);
        check(file.Read(bytes,sizeof(bytes))==sizeof(bytes));
        check(std::memcmp(bytes,original,sizeof(bytes))==0);
        file.Close();
    }
    check(file.Open(FileClass::READ|FileClass::WRITE));
    check(file.Seek(2,SEEK_SET)==2);
    const unsigned char replacement=7;
    check(file.Write(&replacement,1)==1);
    file.Close();
    check(file.Open(FileClass::READ));
    check(file.Read(bytes,sizeof(bytes))==sizeof(bytes));
    check(bytes[0]==0 && bytes[1]==13 && bytes[2]==7 && bytes[3]==26 && bytes[4]==255 && bytes[5]==42);
    file.Close();
    check(file.Open(FileClass::WRITE));
    check(file.Write("x",1)==1);
    file.Close();
    check(file.Open(FileClass::READ));
    check(file.Read(bytes,sizeof(bytes))==1 && bytes[0]=='x');
    file.Close();
    std::remove(path);
    RawFileClass missing("missing-file-directory/leaf.dat");
    check(!missing.Open(FileClass::READ|FileClass::WRITE));
}
int main(){check_open_modes();const char* path="rawfile-test.dat";RawFileClass f(path);check(f.Open(FileClass::WRITE));check(f.Write("0123456789",10)==10);f.Close();check(f.Open(FileClass::READ));check(f.Size()==10);check(f.Seek(3,SEEK_SET)==3);check(f.Size()==10);check(f.Seek(0,SEEK_CUR)==3);char data[16]={};check(f.Read(data,4)==4);check(std::memcmp(data,"3456",4)==0);check(f.Seek(-2,SEEK_END)==8);check(f.Read(data,8)==2);check(std::memcmp(data,"89",2)==0);check(f.Read(data,1)==0);f.Close();f.Bias(2,4);check(f.Open(FileClass::READ));check(f.Size()==4);check(f.Read(data,12)==4);check(std::memcmp(data,"2345",4)==0);check(f.Read(data,1)==0);f.Close();struct timespec times[2]={{1709210040,500000000},{1709210040,500000000}};check(utimensat(AT_FDCWD,path,times,0)==0);check(f.Get_Date_Time()==static_cast<unsigned long>((22621u<<16)|25665u));check(!f.Is_Open());check(f.Open(FileClass::READ));check(f.Get_Date_Time()==static_cast<unsigned long>((22621u<<16)|25665u));check(f.Is_Open());check(f.Set_Date_Time((22621u<<16)|25666u));check(f.Get_Date_Time()==((22621u<<16)|25666u));check(!f.Set_Date_Time(0));check(f.Get_Date_Time()==((22621u<<16)|25666u));f.Close();check(!f.Set_Date_Time((22621u<<16)|25666u));std::remove(path);ObservedFile bad(".");check(bad.Open(FileClass::READ));check(bad.Read(data,1)==0);check(bad.errors==1);bad.Close();puts("PASS raw file write/read/seek/size/EOF/biased range");}
