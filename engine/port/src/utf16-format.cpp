// SPDX-License-Identifier: GPL-3.0-or-later
#include "utf16-string-operations.h"
#include <string>
#include <vector>
#include <cstdio>
#include <climits>
#include <cerrno>
#include <cstdint>
#include <type_traits>
#include <iconv.h>
#include "legacy-decimal.h"
#ifndef GENERALS_WIDE_CRT_ENCODING
#error Select the installation ANSI encoding explicitly
#endif
namespace legacy_text {
namespace {
struct Args { va_list value; explicit Args(va_list input) {va_copy(value,input);} ~Args(){va_end(value);} };
struct Codec {
    iconv_t value;
    Codec():value(iconv_open("UTF-16LE",GENERALS_WIDE_CRT_ENCODING)){}
    ~Codec(){if(value!=iconv_t(-1))iconv_close(value);}
    Codec(const Codec&)=delete;Codec& operator=(const Codec&)=delete;
};
bool decimal(const char16_t*& cursor,int& value) {
    value=0;
    while(*cursor>=u'0' && *cursor<=u'9') {
        int digit=*cursor++-u'0';
        if(value>(INT_MAX-digit)/10) return false;
        value=value*10+digit;
    }
    return true;
}
bool decode(const char* text,std::u16string& result,int precision) {
    if(!text) {result=u"(null)";return true;}
    if(std::strcmp(GENERALS_WIDE_CRT_ENCODING,"C")==0) {
        while((precision<0 || result.size()<size_t(precision)) && *text)
            result.push_back(char16_t(uint8_t(*text++)));
        return true;
    }
    if(precision==0)return true;
    Codec converter;
    if(converter.value==iconv_t(-1))return false;
    std::vector<char> pending;
    bool ok=true;
    while(precision<0 || result.size()<size_t(precision)) {
        // Do not inspect a terminator beyond a satisfied precision. A caller
        // may supply only the bytes required for the requested characters.
        if(*text==0){ok=pending.empty();break;}
        pending.push_back(*text++);
        char* source=pending.data();size_t remaining=pending.size();
        char bytes[4];char* destination=bytes;size_t available=sizeof(bytes);
        errno=0;
        size_t status=iconv(converter.value,&source,&remaining,&destination,&available);
        int conversion_error=errno;
        size_t produced=sizeof(bytes)-available;
        size_t consumed=pending.size()-remaining;
        pending.erase(pending.begin(),pending.begin()+consumed);
        if(produced%2){ok=false;break;}
        // Selected legacy ANSI pages emit BMP units. A supplementary character
        // is emitted as both UTF-16 units, subject to the string precision.
        for(size_t i=0;i<produced && (precision<0 || result.size()<size_t(precision));i+=2)
            result.push_back(char16_t(uint16_t(uint8_t(bytes[i]))|(uint16_t(uint8_t(bytes[i+1]))<<8)));
        if(status==size_t(-1) && conversion_error!=EINVAL && conversion_error!=E2BIG){ok=false;break;}
        if(status==size_t(-1) && conversion_error==E2BIG && produced==0){ok=false;break;}
    }
    return ok;
}
template<class T> bool number(std::u16string& output,size_t capacity,const std::string& directive,T value) {
    size_t remaining=capacity-output.size();
    std::vector<char> bytes(remaining);
    int count=std::snprintf(bytes.data(),bytes.size(),directive.c_str(),value);
    if(count<0 || size_t(count)>=remaining)return false;
    for(int i=0;i<count;++i)output.push_back(char16_t(uint8_t(bytes[size_t(i)])));
    return true;
}
bool render(std::u16string& output,size_t capacity,const char16_t* pattern,va_list& arguments) {
    while(*pattern) {
        if(*pattern!=u'%') {
            if(output.size()+1>=capacity)return false;
            output.push_back(*pattern++);continue;
        }
        ++pattern;
        if(*pattern==u'%') {
            if(output.size()+1>=capacity)return false;
            output.push_back(*pattern++);continue;
        }
        std::string flags;
        while(*pattern && (*pattern==u'-'||*pattern==u'+'||*pattern==u' '||*pattern==u'#'||*pattern==u'0'))
            flags.push_back(char(*pattern++));
        int width=0,precision=-1;
        if(*pattern==u'*') {
            ++pattern;width=va_arg(arguments,int);
            if(width==INT_MIN)return false;
            if(width<0){width=-width;flags.push_back('-');}
        } else if(!decimal(pattern,width))return false;
        if(*pattern==u'.') {
            ++pattern;
            if(*pattern==u'*'){++pattern;precision=va_arg(arguments,int);}
            else if(!decimal(pattern,precision))return false;
        }
        if(size_t(width)>=capacity || (precision>=0 && size_t(precision)>=capacity))return false;
        enum Length {normal,half,byte,wide,long_value,quad,word32,size_value,difference,pointer_value,long_double,max_value};
        Length length=normal;
        if(*pattern==u'h') {++pattern;length=half;if(*pattern==u'h'){++pattern;length=byte;}}
        else if(*pattern==u'l') {++pattern;length=long_value;if(*pattern==u'l'){++pattern;length=quad;}}
        else if(*pattern==u'w') {++pattern;length=wide;}
        else if(*pattern==u'I') {
            ++pattern;length=pointer_value;
            if(pattern[0]==u'6' && pattern[1]==u'4'){pattern+=2;length=quad;}
            else if(pattern[0]==u'3' && pattern[1]==u'2'){pattern+=2;length=word32;}
        }
        else if(*pattern==u'z'){++pattern;length=size_value;}
        else if(*pattern==u't'){++pattern;length=difference;}
        else if(*pattern==u'j'){++pattern;length=max_value;}
        else if(*pattern==u'L'){++pattern;length=long_double;}
        char16_t kind=*pattern;
        if(!kind)return false;
        ++pattern;
        if(kind==u's'||kind==u'S'||kind==u'c'||kind==u'C') {
            bool narrow=length==half || length==byte || ((kind==u'S'||kind==u'C')&&length==normal);
            if(length!=normal && length!=half && length!=byte && length!=long_value && length!=wide)return false;
            std::u16string text;
            if(kind==u'c'||kind==u'C') {
                unsigned value=unsigned(va_arg(arguments,int));
                if(narrow && (value&255u)==0)text.push_back(0);
                else if(narrow){char bytes[2]={char(value),0};if(!decode(bytes,text,-1))return false;}
                else text.push_back(char16_t(value));
            } else if(narrow) {
                if(!decode(va_arg(arguments,const char*),text,precision))return false;
            } else {
                const char16_t* value=va_arg(arguments,const char16_t*);
                if(!value)value=u"(null)";
                while((precision<0 || text.size()<size_t(precision)) && *value)text.push_back(*value++);
            }
            if((kind==u's'||kind==u'S') && precision>=0 && text.size()>size_t(precision))text.resize(size_t(precision));
            size_t padding=size_t(width)>text.size()?size_t(width)-text.size():0;
            if(text.size()+padding>=capacity-output.size())return false;
            bool left=flags.find('-')!=std::string::npos;
            if(!left)output.append(padding,u' ');
            output+=text;
            if(left)output.append(padding,u' ');
            continue;
        }
        std::string directive="%"+flags;
        if(width)directive+=std::to_string(width);
        if(precision>=0)directive+="."+std::to_string(precision);
        if(kind==u'd'||kind==u'i'||kind==u'u'||kind==u'o'||kind==u'x'||kind==u'X') {
            bool sign=kind==u'd'||kind==u'i';
            if(length==wide||length==long_double)return false;
            if(sign) {
                long long value;
                switch(length) {
                // Windows long is 32-bit. Consume the host ABI type first,
                // then preserve the original value width on LP64 hosts.
                case long_value:value=static_cast<int32_t>(va_arg(arguments,long));break;
                case quad:value=va_arg(arguments,long long);break;
                case max_value:value=va_arg(arguments,intmax_t);break;
                case size_value:value=va_arg(arguments,typename std::make_signed<size_t>::type);break;
                case difference:value=va_arg(arguments,ptrdiff_t);break;
                case pointer_value:value=va_arg(arguments,intptr_t);break;
                case half:value=static_cast<short>(va_arg(arguments,int));break;
                case byte:value=static_cast<signed char>(va_arg(arguments,int));break;
                default:value=va_arg(arguments,int);break;
                }
                directive+="ll";directive.push_back(char(kind));
                if(!number(output,capacity,directive,value))return false;
            } else {
                unsigned long long value;
                switch(length) {
                case long_value:value=static_cast<uint32_t>(va_arg(arguments,unsigned long));break;
                case quad:value=va_arg(arguments,unsigned long long);break;
                case max_value:value=va_arg(arguments,uintmax_t);break;
                case size_value:value=va_arg(arguments,size_t);break;
                case difference:value=va_arg(arguments,typename std::make_unsigned<ptrdiff_t>::type);break;
                case pointer_value:value=va_arg(arguments,uintptr_t);break;
                case half:value=static_cast<unsigned short>(va_arg(arguments,int));break;
                case byte:value=static_cast<unsigned char>(va_arg(arguments,int));break;
                default:value=va_arg(arguments,unsigned int);break;
                }
                directive+="ll";directive.push_back(char(kind));
                if(!number(output,capacity,directive,value))return false;
            }
        } else if(kind==u'f'||kind==u'F'||kind==u'e'||kind==u'E'||kind==u'g'||kind==u'G'||kind==u'a'||kind==u'A') {
            if(length!=normal && length!=long_value && length!=long_double)return false;
            directive.push_back(char(kind));
            if(length==long_double){directive.insert(directive.size()-1,"L");if(!number(output,capacity,directive,va_arg(arguments,long double)))return false;}
            else {
                double value=va_arg(arguments,double);
                if(kind!=u'a' && kind!=u'A') {
                    if(!decimal_float(output,capacity,value,char(kind),flags,width,precision))return false;
                } else if(!number(output,capacity,directive,value))return false;
            }
        } else if(kind==u'p' && length==normal) {
            // Preserve actual host pointer width. Vita naturally emits eight
            // digits under ILP32; a 64-bit host must retain all pointer bits.
            uintptr_t value=reinterpret_cast<uintptr_t>(va_arg(arguments,void*));
            bool prefix=value!=0 && flags.find('#')!=std::string::npos;
            constexpr size_t digits=sizeof(uintptr_t)*2;
            char16_t text[digits];
            for(size_t i=digits;i--;) {text[i]=u"0123456789ABCDEF"[value&15];value>>=4;}
            size_t size=digits+(prefix?2:0);
            size_t padding=width>0 && size_t(width)>size?size_t(width)-size:0;
            if(size+padding>=capacity-output.size())return false;
            bool left=flags.find('-')!=std::string::npos;
            if(!left)output.append(padding,u' ');
            if(prefix)output+=u"0X";
            output.append(text,digits);
            if(left)output.append(padding,u' ');
        } else return false;
    }
    return true;
}
}
int format(char16_t* destination,size_t capacity,const char16_t* pattern,va_list input) {
    if(!destination || !capacity || !pattern || capacity>size_t(INT_MAX))return -1;
    Args arguments(input);std::u16string output;
    if(!render(output,capacity,pattern,arguments.value))return -1;
    std::memmove(destination,output.c_str(),(output.size()+1)*sizeof(char16_t));
    return int(output.size());
}
// Observed current Windows msvcrt C-locale wide classification. Keep this
// independent of the host libc locale and its Unicode database version.
bool is_space(char16_t value) {
    return (value>=9 && value<=13) || value==32 || value==0x00a0 ||
           value==0x1680 || value==0x180e || (value>=0x2000 && value<=0x200a) ||
           value==0x2028 || value==0x2029 || value==0x202f || value==0x205f || value==0x3000;
}
int compare_no_case(const char16_t* left,const char16_t* right) {
    for(;;++left,++right) {
        unsigned a=*left,b=*right;
        if(a>='A'&&a<='Z')a+='a'-'A';
        if(b>='A'&&b<='Z')b+='a'-'A';
        if(a!=b)return int(a)-int(b);
        if(!a)return 0;
    }
}
}
