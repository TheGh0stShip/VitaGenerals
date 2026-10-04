# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded CSF wire diagnostic: int32 fields and 16-bit encoded units."""
import hashlib
from map_values import Cursor
CSF=0x43534620;LBL=0x4c424c20;STR=0x53545220;STRW=0x53545257
MAX=1_000_000
MAX_BYTES=16*1024*1024
def count(c):
 n=c.unpack('<i')[0]
 if n<0 or n>MAX:raise ValueError('csf_count_policy')
 return n
def parse(data):
 if len(data)>MAX_BYTES:raise ValueError('csf_size_policy')
 c=Cursor(data);header=list(c.unpack('<6i'))
 if header[0]!=CSF:raise ValueError('csf_magic')
 if any(n<0 or n>MAX for n in header[2:4]):raise ValueError('csf_header_count_policy')
 rows=[];total=0
 while c.pos<len(data):
  if len(rows)>=MAX:raise ValueError('csf_label_policy')
  offset=c.pos
  if c.unpack('<I')[0]!=LBL:raise ValueError('csf_label_tag')
  num=count(c);label=c.take(count(c));strings=[]
  for _ in range(num):
   total+=1
   if total>MAX:raise ValueError('csf_string_policy')
   tag=c.unpack('<I')[0]
   if tag not in (STR,STRW):raise ValueError('csf_string_tag')
   units=count(c);raw=c.take(units*2);zeros=[i for i in range(units) if raw[2*i:2*i+2]==b'\0\0'];speech=None
   if tag==STRW:
    wave=c.take(count(c));speech={'bytes':len(wave),'sha256':hashlib.sha256(wave).hexdigest()}
   strings.append({'tag_u32':tag,'utf16le_encoded_unit_count':units,'encoded_sha256':hashlib.sha256(raw).hexdigest(),'encoded_zero_unit_offsets':zeros,'speech_metadata':speech})
  rows.append({'offset':offset,'label_bytes':len(label),'label':label.decode('latin1'),'label_contains_nul':b'\0' in label,'strings':strings})
 return {'header_int32':header,'rows':rows,'header_label_count_matches':header[2]==len(rows),'header_string_count_matches':header[3]==total,'string_count':total,'exact_end':True,'runtime_semantics':'unverified'}
