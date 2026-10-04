# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit-width host map values; retains wire values, not runtime string ABI.

Dictionary entries remain ordered and duplicated. Float values retain raw bits;
UTF-16 units retain unpaired surrogates. Native wchar_t is never used.
"""
import struct

class Cursor:
 def __init__(self,data): self.data=data;self.pos=0
 def take(self,n):
  if n<0 or n>len(self.data)-self.pos: raise ValueError('map_value_bounds')
  result=self.data[self.pos:self.pos+n];self.pos+=n;return result
 def unpack(self,fmt):
  if not fmt.startswith(('<','>')):raise ValueError('explicit_endian_required')
  return struct.unpack(fmt,self.take(struct.calcsize(fmt)))
 def ascii(self): return self.take(self.unpack('<H')[0]).decode('latin1')
 def dictionary(self,lookup):
  rows=[]
  for _ in range(self.unpack('<H')[0]):
   packed=self.unpack('<i')[0];kind=packed&255;ident=(packed>>8)&0xffffffff
   if kind==0:value=self.take(1)[0]!=0
   elif kind==1:value=self.unpack('<i')[0]
   elif kind==2:value={'float32_bits':self.take(4).hex()}
   elif kind==3:value=self.ascii()
   elif kind==4:
    count=self.unpack('<H')[0];value={'utf16le_units':list(self.unpack('<'+'H'*count))}
   else:raise ValueError('unsupported_dict_type_'+str(kind))
   rows.append({'id_u32':ident,'key_candidates':lookup.get(ident,[]),'type':kind,'value':value})
  return rows
