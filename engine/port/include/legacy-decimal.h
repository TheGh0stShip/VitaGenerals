// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <string>
#include <cstdint>
#include <cstring>
#include <limits>
namespace legacy_text {
namespace {
// Exact binary64 magnitude as decimal integer digits times 10^-scale.
// Decimal multiplication keeps every digit, including subnormal tails.
struct Decimal {
    std::string digits;
    int scale;
    explicit Decimal(uint64_t bits) {
        unsigned exponent=unsigned((bits>>52)&2047);
        uint64_t mantissa=bits&UINT64_C(0xfffffffffffff);
        if(exponent==2047) {
            digits=bits==UINT64_C(0xfff8000000000000)?"1#IND":mantissa==0?"1#INF":(mantissa & (UINT64_C(1)<<51))?"1#QNAN":"1#SNAN";
            scale=int(digits.size())-1;return;
        }
        int power=-1074;
        if(exponent){mantissa|=UINT64_C(1)<<52;power=int(exponent)-1075;}
        digits=std::to_string(mantissa);scale=power<0?-power:0;
        int factor=power<0?5:2;
        for(int i=0;i<(power<0?-power:power);++i) {
            int carry=0;
            for(size_t j=digits.size();j--;) {
                int value=(digits[j]-'0')*factor+carry;
                digits[j]=char('0'+value%10);carry=value/10;
            }
            if(carry)digits.insert(digits.begin(),char('0'+carry));
        }
        if(mantissa==0){digits="0";scale=0;}
    }
    int exponent()const{return digits=="0"?0:int(digits.size())-scale-1;}
    void round(int new_scale) {
        int remove=scale-new_scale;
        if(remove<=0){digits.append(size_t(-remove),'0');scale=new_scale;return;}
        int keep=int(digits.size())-remove;
        bool up=keep>=0 && size_t(keep)<digits.size() && digits[size_t(keep)]>='5';
        digits=keep>0?digits.substr(0,size_t(keep)):"0";
        if(up) {
            size_t i=digits.size();
            while(i && digits[i-1]=='9'){digits[--i]='0';}
            if(i)++digits[i-1];else digits.insert(digits.begin(),'1');
        }
        scale=new_scale;
    }
    std::string fixed(int places,bool alternate)const {
        std::string text=digits;
        if(scale<0)text.append(size_t(-scale),'0');
        else if(scale>0){if(text.size()<=size_t(scale))text.insert(0,size_t(scale)+1-text.size(),'0');text.insert(text.size()-size_t(scale),1,'.');}
        if(places==0 && alternate)text+='.';
        return text;
    }
};
bool decimal_float(std::u16string& output,size_t capacity,double value,char kind,
                   const std::string& flags,int width,int precision) {
    static_assert(sizeof(double)==8 && std::numeric_limits<double>::is_iec559,"binary64 required");
    uint64_t bits;std::memcpy(&bits,&value,sizeof(bits));
    bool negative=(bits>>63)!=0,alternate=flags.find('#')!=std::string::npos;
    bool general=kind=='g'||kind=='G',scientific=kind=='e'||kind=='E';
    if(precision<0)precision=6;
    if(general && precision==0)precision=1;
    Decimal decimal(bits);
    int exponent=decimal.exponent();
    // The legacy CRT emits at most 17 significant decimal digits, padding
    // further requested places with zeroes, even for exact large integers.
    if(((bits>>52)&2047)!=2047)decimal.round(16-exponent);
    decimal.round(general?precision-1-exponent:scientific?precision-exponent:precision);
    exponent=decimal.exponent();
    if(general){scientific=exponent < -4 || exponent>=precision;precision=scientific?precision-1:precision-1-exponent;
        if((bits & UINT64_C(0x7fffffffffffffff))==0 && alternate)++precision;}
    std::string text;
    if(scientific) {
        // Rounding can carry into another decade. Reposition the already rounded
        // exact integer without a second rounding operation.
        std::string significant=decimal.digits;
        significant.resize(size_t(precision)+1,'0');
        text=significant.substr(0,1);
        if(precision || alternate)text+='.';
        text+=significant.substr(1);
    } else {
        decimal.round(precision);text=decimal.fixed(precision,alternate);
    }
    if(general && !alternate) {
        size_t dot=text.find('.');
        if(dot!=std::string::npos){while(text.back()=='0')text.pop_back();if(text.back()=='.')text.pop_back();}
    }
    if(scientific) {
        text+=kind=='E'||kind=='G'?'E':'e';text+=exponent<0?'-':'+';
        std::string power=std::to_string(exponent<0?-exponent:exponent);
        if(power.size()<3)text.append(3-power.size(),'0');text+=power;
    }
    char sign=negative?'-':flags.find('+')!=std::string::npos?'+':flags.find(' ')!=std::string::npos?' ':0;
    size_t size=text.size()+(sign?1:0);
    size_t padding=width>0 && size_t(width)>size?size_t(width)-size:0;
    if(size+padding>=capacity-output.size())return false;
    bool left=flags.find('-')!=std::string::npos;
    bool zero=!left && flags.find('0')!=std::string::npos;
    if(!left && !zero)output.append(padding,u' ');
    if(sign)output.push_back(char16_t(sign));
    if(zero)output.append(padding,u'0');
    for(char c:text)output.push_back(char16_t(uint8_t(c)));
    if(left)output.append(padding,u' ');
    return true;
}
}
}
