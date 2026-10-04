#include "PreRTS.h"
#include "Common/UnicodeString.h"
#include "Common/AsciiString.h"
#include <cstdlib>
#include <vector>
#include "Common/CriticalSection.h"
#if !defined(__vita__)
#include <thread>
#include <atomic>
#endif
static void check(bool value){if(!value)std::abort();}
int main(){
 initMemoryManager();
 UnicodeString a(u"alpha"),b(a);b.concat(u"beta");check(a.compare(u"alpha")==0 && b.compare(u"alphabeta")==0);
 a.concat(a.str());check(a.compare(u"alphaalpha")==0);b.set(b.str()+5);check(b.compare(u"beta")==0);
 UnicodeString pair(u"\U0001F600");check(pair.getLength()==2);pair.removeLastChar();check(pair.getLength()==1 && pair.getCharAt(0)==0xd83d);
 UnicodeString result;result.format(u"%s:%d:%I64d:%.2f",u"units",7,9223372036854775807ll,1.5);check(result.compare(u"units:7:9223372036854775807:1.50")==0);
 unsigned long hostWideUnsigned=sizeof(unsigned long)>4?0x100000001ul:1ul;
 long hostWideSigned=sizeof(long)>4?long(0x100000001LL):1l;
 result.format(u"%ld/%lu",hostWideSigned,hostWideUnsigned);
 check(result.compare(u"1/1")==0);
 UnicodeString pattern(u"[%ls/%d]");result.format(pattern,u"wide",8);check(result.compare(u"[wide/8]")==0);
 result.format(u"%S","plain");check(result.compare(u"plain")==0);
#if defined(GENERALS_LEGACY_ENCODING_CP932)
 char boundedMultibyte[2]={char(0x82),char(0xa0)};
 result.format(u"%.1S",boundedMultibyte);
 check(result.compare(u"\u3042")==0);
#elif defined(GENERALS_LEGACY_ENCODING_CP1252)
 char boundedMultibyte[1]={char(0xe9)};
 result.format(u"%.1S",boundedMultibyte);
 check(result.compare(u"\u00e9")==0);
#endif
 check(UnicodeString(u"AbC").compareNoCase(u"aBc")==0);
 UnicodeString tokens(u"a b"),token;check(tokens.nextToken(&token) && token.compare(u"a")==0);check(tokens.nextToken(&token) && token.compare(u"b")==0);
 UnicodeString trimSource(u"\u00a0\u3000trim\u202f\u180e"),trimCopy(trimSource);trimCopy.trim();
 check(trimCopy.compare(u"trim")==0 && trimSource.compare(u"\u00a0\u3000trim\u202f\u180e")==0);
 UnicodeString pointerText;void* pointerToken=reinterpret_cast<void*>(uintptr_t(0xabcdef01));
 pointerText.format(u"%p/%#p",pointerToken,pointerToken);
 check(pointerText.compare(sizeof(void*)==4?u"ABCDEF01/0XABCDEF01":u"00000000ABCDEF01/0X00000000ABCDEF01")==0);
 check(sizeof(WideChar)==2);
 UnicodeString shared(u"shared payload");std::vector<UnicodeString> owners;owners.reserve(65534);
 for(unsigned i=0;i<65534;++i)owners.emplace_back(shared);
 UnicodeString assignedAtLimit(u"old destination");assignedAtLimit=shared;
 check(assignedAtLimit.compare(u"shared payload")==0 && assignedAtLimit.str()!=shared.str());
 UnicodeString overflow(shared),second(shared);
 check(overflow.str()!=shared.str() && second.str()!=shared.str());second.clear();
 check(shared.compare(u"shared payload")==0);
 overflow.concat(u" extra");check(shared.compare(u"shared payload")==0);
 owners.front().set(shared);owners.front().concat(u" changed");
 check(shared.compare(u"shared payload")==0);owners.clear();
 shared.concat(u" retained");check(shared.compare(u"shared payload retained")==0);
#if !defined(__vita__)
 CriticalSection dmaMutex,poolMutex,unicodeMutex;
 TheDmaCriticalSection=&dmaMutex;TheMemoryPoolCriticalSection=&poolMutex;TheUnicodeStringCriticalSection=&unicodeMutex;
 for(unsigned n=0;n<256;++n){
  UnicodeString seed(u"final owners"),first(seed),last(seed);seed.clear();std::atomic<bool> ready(false);
  std::thread worker([&]{while(!ready.load(std::memory_order_acquire)){}first.clear();});
  ready.store(true,std::memory_order_release);last.clear();worker.join();
 }
 UnicodeString stable(u"thread shared");std::vector<std::thread> workers;
 for(unsigned i=0;i<4;++i)workers.emplace_back([&]{for(unsigned n=0;n<10000;++n){
  UnicodeString copy(stable),assigned(u"old");assigned=copy;assigned.concat(u" edit");
  check(stable.compare(u"thread shared")==0 && assigned.compare(u"thread shared edit")==0);
 }});
 for(auto& worker:workers)worker.join();
 TheUnicodeStringCriticalSection=nullptr;TheDmaCriticalSection=nullptr;TheMemoryPoolCriticalSection=nullptr;
#endif
}
