# SPDX-License-Identifier: GPL-3.0-or-later
"""Decode original map script leaf wire values without runtime remapping.

Source: Scripts.cpp ParseAction, ParseConditionDataChunk and ReadParameter;
Scripts.h ParameterType and MAX_PARMS. Name-key generation, legacy healing,
template validation and runtime reference resolution remain separate.
"""
from map_values import Cursor

def leaf(body, label, version, lookup):
 if label not in ('Condition','ScriptAction','ScriptActionFalse'):
  raise ValueError('unsupported_leaf_label')
 condition=label=='Condition'
 if version not in ((1,2,3,4) if condition else (1,2)):
  raise ValueError('unsupported_leaf_version')
 c=Cursor(body); result={'raw_enum_i32':c.unpack('<i')[0]}
 if version >= (4 if condition else 2):
  packed=c.unpack('<i')[0];ident=(packed>>8)&0xffffffff
  result['raw_name_key']={'packed_i32':packed,'type_byte':packed&255,'id_u32':ident,'name_candidates':lookup.get(ident,[])}
 n=c.unpack('<i')[0]
 # Original fixed parameter array has 12 slots. This is a diagnostic guard,
 # not a claim that the original loader rejects malformed counts safely.
 if n<0 or n>12:raise ValueError('parameter_count_bounds')
 params=[]
 for _ in range(n):
  p={'raw_type_i32':c.unpack('<i')[0]}
  if p['raw_type_i32']==16:p['coordinate_float32_bits']=c.take(12).hex()
  else:p.update(integer_i32=c.unpack('<i')[0],real_float32_bits=c.take(4).hex(),ascii_bytes=c.ascii())
  params.append(p)
 result['raw_parameters']=params
 if c.pos!=len(body):raise ValueError('trailing_leaf_bytes')
 result['runtime_binding_and_healing_verified']=False
 return result
