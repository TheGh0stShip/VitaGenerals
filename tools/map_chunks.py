# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded host map diagnostics; does not replace the original engine loader.

All scalar widths/endian rules are explicit. Exact termination, size limits and
metadata count limits are diagnostic policies, not original rejection claims.
"""
import collections
import struct
import zlib

LIMIT = 16 * 1024 * 1024
MAX_TABLE_ENTRIES = 65536
MAX_TOP_CHUNKS = 65536

def refpack(data,expected):
 pos=0;out=bytearray()
 def take(n):
  nonlocal pos
  if n<0 or n>len(data)-pos:raise ValueError('truncated_refpack')
  b=data[pos:pos+n];pos+=n;return b
 kind=int.from_bytes(take(2),'big')
 if kind not in (0x10fb,0x11fb,0x90fb,0x91fb):raise ValueError('unsupported_refpack')
 width=4 if kind&0x8000 else 3
 if kind&0x100:take(width)
 size=int.from_bytes(take(width),'big')
 if size!=expected or not 0<=size<=LIMIT:raise ValueError('refpack_size_mismatch')
 def literal(n):
  if n>size-len(out):raise ValueError('literal_output_bounds')
  out.extend(take(n))
 def copy(distance,count):
  if not 1<=distance<=len(out) or count>size-len(out):raise ValueError('copy_output_bounds')
  # Overlap copies must see newly emitted bytes, matching the original decoder.
  for _ in range(count):out.append(out[-distance])
 while True:
  first=take(1)[0]
  if first<0x80:
   second=take(1)[0];literal(first&3);copy(((first&0x60)<<3)+second+1,((first&0x1c)>>2)+3)
  elif first<0xc0:
   second,third=take(2);literal(second>>6);copy(((second&0x3f)<<8)+third+1,(first&0x3f)+4)
  elif first<0xe0:
   second,third,fourth=take(3);literal(first&3);copy(((first&0x10)<<12)+(second<<8)+third+1,((first&0x0c)<<6)+fourth+5)
  elif first<0xfc:literal(((first&0x1f)<<2)+4)
  else:
   literal(first&3);break
 if len(out)!=size or pos!=len(data):raise ValueError('refpack_length_or_trailing_data')
 return bytes(out)

def decode(data):
 if data[:4]==b'CkMp':
  if len(data)>LIMIT:raise ValueError('raw_output_limit')
  return data,'raw'
 if len(data)<8:raise ValueError('wrapper_truncated')
 size=struct.unpack_from('<i',data,4)[0]
 if not 0<=size<=LIMIT:raise ValueError('wrapper_output_limit')
 if data[:4]==b'EAR\0':return refpack(data[8:],size),'refpack'
 if data[:2]==b'ZL' and data[2:3] in b'123456789' and data[3:4]==b'\0':
  stream=zlib.decompressobj();out=stream.decompress(data[8:],size+1)
  if len(out)!=size or not stream.eof or stream.unused_data or stream.unconsumed_tail:raise ValueError('zlib_length_or_trailing_data')
  return out,'zlib'
 raise ValueError('unsupported_map_wrapper')

def framing(data):
 if len(data)>LIMIT:raise ValueError('map_output_limit')
 pos=0
 def take(n):
  nonlocal pos
  if n<0 or n>len(data)-pos:raise ValueError('map_bounds')
  b=data[pos:pos+n];pos+=n;return b
 if take(4)!=b'CkMp':raise ValueError('no_chunk_table')
 count=struct.unpack('<i',take(4))[0]
 if count<0 or count>MAX_TABLE_ENTRIES or count>(len(data)-pos)//5:raise ValueError('table_count_bounds')
 toc=[];lookup=collections.defaultdict(list)
 for _ in range(count):
  name=take(take(1)[0]).decode('latin1');ident=struct.unpack('<I',take(4))[0]
  toc.append({'name':name,'id_u32':ident});lookup[ident].append(name)
 chunks=[]
 while pos<len(data):
  if len(chunks)>=MAX_TOP_CHUNKS:raise ValueError('top_chunk_count_limit')
  offset=pos;ident,version,size=struct.unpack('<IHi',take(10))
  if size<0 or size>len(data)-pos:raise ValueError('top_chunk_bounds')
  chunks.append({'offset':offset,'id_u32':ident,'label_candidates':lookup.get(ident,[]),'version_u16':version,'data_size_i32':size})
  take(size)
 return {'table':toc,'top_chunks':chunks,'duplicate_ids':[i for i,n in lookup.items() if len(n)>1],'complete_references':False}
