// SPDX-License-Identifier: GPL-3.0-or-later
#include "PreRTS.h"
#include "Common/AsciiString.h"
#include <cstring>
int main(){
 initMemoryManager();
 AsciiString a("alpha"); AsciiString b(a); b.concat("beta");
 if(std::strcmp(a.str(),"alpha") || std::strcmp(b.str(),"alphabeta")) return 1;
 a.concat(a.str()); if(std::strcmp(a.str(),"alphaalpha")) return 2;
 b.set(b.str()+5); if(std::strcmp(b.str(),"beta")) return 3;
 char text[2048]; std::memset(text,'x',2046); text[2046]=0;
 AsciiString f; f.format("%s",text); if(f.getLength()!=2046) return 4;
 text[2046]='x';text[2047]=0; bool rejected=false;
 try {f.format("%s",text);} catch(...) {rejected=true;}
 if(!rejected || f.getLength()!=2046) return 5;
 return 0;
}
