# SPDX-License-Identifier: GPL-3.0-or-later
"""Lexical named INI candidates, not block scope or selected runtime providers.

Source: INI.cpp readLine/getNextToken and named block handlers. Physical LF
lines, byte offsets and original control/comment separators are preserved.
This diagnostic reports overlong lines and NULs without invoking the loader.
Quotes, nested blocks, directives and inheritance are not interpreted.
"""
import re

def scan(data, kinds=('Object','ObjectReskin')):
 declarations=[];directives=[];issues=[]
 # Physical LF lines only: original reader does not split Unicode/control separators.
 offset=0
 for number,line in enumerate(data.split(b'\n'),1):
  if len(line)>=1028:issues.append({'line':number,'reason':'original_line_buffer_boundary'})
  if b'\0' in line:issues.append({'line':number,'reason':'embedded_nul'})
  visible=line.split(b'\0',1)[0].split(b';',1)[0]
  visible=bytes(32 if 0<b<32 else b for b in visible)
  tokens=[t.decode('latin1') for t in re.split(rb'[ \r\t=]+',visible.strip(b' \r\t=')) if t]
  if tokens and tokens[0] in kinds:
   wanted=3 if tokens[0]=='ObjectReskin' else 2
   if len(tokens)<wanted:issues.append({'line':number,'reason':'incomplete_named_declaration'})
   declarations.append({'line':number,'offset':offset,'kind':tokens[0],'name':tokens[1] if len(tokens)>1 else None,'reskin_from':tokens[2] if tokens[0]=='ObjectReskin' and len(tokens)>2 else None,'extra_tokens':tokens[wanted:],'scope':'unresolved'})
  if tokens and tokens[0].startswith('#'):directives.append({'line':number,'tokens':tokens,'semantics':'unresolved'})
  offset+=len(line)+1
 return declarations,directives,issues
