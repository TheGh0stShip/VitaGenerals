// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef GENERALS_PACKED_FILE_TIME_H
#define GENERALS_PACKED_FILE_TIME_H
#include <cstdint>
namespace generals_file_time {
inline bool pack(int year,int month,int day,int hour,int minute,int second,uint32_t& out)
{
 if(year<1980 || year>2107 || month<1 || month>12 || hour<0 || hour>23 || minute<0 || minute>59 || second<0 || second>59) return false;
 static const int days[]={31,28,31,30,31,30,31,31,30,31,30,31};
 const bool leap=year%4==0 && (year%100!=0 || year%400==0);
 const int limit=days[month-1]+(month==2 && leap ? 1:0);
 if(day<1 || day>limit) return false;
 out=(static_cast<uint32_t>(year-1980)<<25)|(static_cast<uint32_t>(month)<<21)|(static_cast<uint32_t>(day)<<16)|(static_cast<uint32_t>(hour)<<11)|(static_cast<uint32_t>(minute)<<5)|static_cast<uint32_t>(second/2);
 return true;
}
inline bool to_epoch(uint32_t packed,int64_t& out)
{
 const int year=1980+static_cast<int>(packed>>25),month=(packed>>21)&15,day=(packed>>16)&31;
 const int hour=(packed>>11)&31,minute=(packed>>5)&63,second=(packed&31)*2;
 uint32_t checked=0;
 if(!pack(year,month,day,hour,minute,second,checked) || checked!=packed) return false;
 int64_t days=0;
 for(int y=1980;y<year;++y)days+=(y%4==0 && (y%100!=0 || y%400==0))?366:365;
 static const int lengths[]={31,28,31,30,31,30,31,31,30,31,30,31};
 for(int m=1;m<month;++m)days+=lengths[m-1]+(m==2 && year%4==0 && (year%100!=0 || year%400==0)?1:0);
 out=INT64_C(315532800)+(days+day-1)*86400+hour*3600+minute*60+second;
 return true;
}
inline bool from_epoch(int64_t seconds, uint32_t nanoseconds, uint32_t& out)
{
 if(nanoseconds >= UINT32_C(1000000000) || seconds < INT64_C(315532798) || seconds > INT64_C(4354819199)) return false;
 seconds += (seconds & 1) ? 1 : (nanoseconds ? 2 : 0);
 if(seconds < INT64_C(315532800) || seconds > INT64_C(4354819198)) return false;
 int64_t days = (seconds-INT64_C(315532800))/86400;
 const int daytime=static_cast<int>(seconds%86400);
 int year=1980;
 for(;;) { int length=(year%4==0 && (year%100!=0 || year%400==0))?366:365; if(days<length) break; days-=length; ++year; }
 static const int lengths[]={31,28,31,30,31,30,31,31,30,31,30,31};
 int month=1;
 for(;;) {int length=lengths[month-1]+(month==2 && year%4==0 && (year%100!=0 || year%400==0)?1:0);if(days<length)break;days-=length;++month;}
 return pack(year,month,static_cast<int>(days)+1,daytime/3600,(daytime/60)%60,daytime%60,out);
}
}
#endif
