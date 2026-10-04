# SPDX-License-Identifier: GPL-3.0-or-later
"""Selected audio field handlers on one physical, LF-free INI line.

Source: INI.cpp parseSoundsList/getNextAsciiString/getNextToken. Sound lists
replace the vector; unquoted ASCII consumes one token. Quoted ASCII remains
unresolved. Caller must establish block owner, scope and input provenance.
NUL/comment visibility follows the reader; upstream lexical issues stay separate.
"""
import re
SOUND_LISTS={'Sounds','SoundsNight','SoundsEvening','SoundsMorning','Attack','Decay'}
FILENAMES={'Filename','AudioRoot','MusicFolder','SoundsFolder','StreamingFolder','SoundsExtension'}
def field_value(line):
 if b"\n" in line or len(line)>=1028:raise ValueError("physical_line_bounds")
 visible=line.split(b'\0',1)[0].split(b';',1)[0];visible=bytes(32 if 0<c<32 else c for c in visible)
 # First strtok uses default separators and consumes exactly one separator.
 match=re.match(rb'[ \r\t=]*([^ \r\t=]+)([ \r\t=]|$)',visible)
 if not match:return None
 name=match[1].decode('latin1');remainder=visible[match.end():]
 if name in SOUND_LISTS:
  values=[s.decode('latin1') for s in re.split(rb'[ \t,=]+',remainder) if s]
  return {'field':name,'handler':'parseSoundsList','values':values,'replacement_rule':'clear_then_assign_vector','status':'handler_values_parsed'}
 if name in FILENAMES:
  token=re.search(rb'[^ \r\t=]+',remainder)
  if not token:return {'field':name,'handler':'parseAsciiString','value':'','status':'handler_values_parsed'}
  if token[0].startswith(b'"'):return {'field':name,'handler':'parseAsciiString','status':'quoted_ascii_semantics_unresolved','raw_value':remainder.decode('latin1')}
  return {'field':name,'handler':'parseAsciiString','value':token[0].decode('latin1'),'status':'handler_values_parsed'}
 return None
