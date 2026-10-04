#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Inventory named formatting calls and direct literal format candidates."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
from audit_system_ownership import analyze
from audit_source_structure import parser, VERSIONS

# Positions follow the original/legacy API spelling. Overloads, aliases and
# contemporary CRT signatures still require binding; these are candidates.
FORMAT_INDEX = {name: 0 for name in ('format', 'format_va', 'Format', 'FormatV',
    'printf', 'wprintf', 'vprintf', 'vwprintf', '_tprintf', '_vtprintf')}
FORMAT_INDEX.update({name: 1 for name in ('sprintf', 'vsprintf', 'swprintf',
    'vswprintf', '_stprintf', '_vstprintf', 'fprintf', 'fwprintf', 'vfprintf',
    'vfwprintf', 'wsprintf', 'wsprintfA', 'wsprintfW', 'wvsprintf', 'wvsprintfA', 'wvsprintfW')})
FORMAT_INDEX.update({name: 2 for name in ('snprintf', 'vsnprintf', '_snprintf',
    '_vsnprintf', '_snwprintf', '_vsnwprintf', '_sntprintf', '_vsntprintf')})
DIRECTIVE = re.compile(r'%([-+ #0]*)(\*|[0-9]*)(?:\.(\*|[0-9]*))?(I64|I32|hh|ll|h|l|w|I|z|t|j|L)?([diuoxXfFeEgGaAcCsSpnZ%])')
ESCAPE = {'a':'\a','b':'\b','f':'\f','n':'\n','r':'\r','t':'\t','v':'\v',
          '\\':'\\',"'":"'",'"':'"','?':'?'}

def decode_literal(raw):
    opening=raw.find('"')
    if opening<0 or raw[:opening] not in ('','L','u','U','u8'):return None
    prefix=raw[:opening]
    maximum=255 if prefix in ('','u8') else 65535 if prefix in ('L','u') else 0x10ffff
    value=raw[opening+1:-1];out=[];i=0
    while i<len(value):
        if value[i]!='\\':out.append(value[i]);i+=1;continue
        i+=1
        if i==len(value):return None
        c=value[i];i+=1
        if c=='\n':continue
        if c=='\r' and i<len(value) and value[i]=='\n':i+=1;continue
        if c in ESCAPE:out.append(ESCAPE[c]);continue
        if c in '01234567':
            start=i-1
            while i<len(value) and i-start<3 and value[i] in '01234567':i+=1
            number=int(value[start:i],8)
            if number>maximum:return None
            out.append(chr(number));continue
        if c in ('x','u','U'):
            start=i;limit={'u':4,'U':8}.get(c)
            while i<len(value) and value[i] in '0123456789abcdefABCDEF' and (limit is None or i-start<limit):i+=1
            if i==start or (limit is not None and i-start!=limit):return None
            number=int(value[start:i],16)
            if number>0x10ffff or (c=='x' and number>maximum):return None
            out.append(chr(number));continue
        return None
    return ''.join(out)

def literal_expression(expression, engine):
    source=('void probe(){candidate('+expression+');}').encode('utf8')
    tree=engine.parse(source)
    if tree.root_node.has_error:return None
    pending=[tree.root_node];call=None
    while pending:
        node=pending.pop()
        if node.type=='call_expression':call=node;break
        pending.extend(reversed(node.children))
    if call is None:return None
    args=call.child_by_field_name('arguments')
    nodes=[x for x in args.named_children if x.type!='comment']
    if len(nodes)!=1 or nodes[0].type not in ('string_literal','concatenated_string'):return None
    parts=[nodes[0]] if nodes[0].type=='string_literal' else [x for x in nodes[0].named_children if x.type!='comment']
    decoded=[]
    for part in parts:
        if part.type!='string_literal':return None
        text=source[part.start_byte:part.end_byte].decode('utf8');value=decode_literal(text)
        if value is None:return None
        decoded.append(value)
    return ''.join(decoded)

def directives(value):
    result=[];unknown=[];i=0
    while i<len(value):
        if value[i]!='%':i+=1;continue
        match=DIRECTIVE.match(value,i)
        if match is None:unknown.append({'offset':i,'suffix':value[i:]});i+=1;continue
        result.append({'offset':i,'spelling':match[0],'flags':match[1],
                       'width':match[2],'precision':match[3],'length':match[4],
                       'conversion':match[5]})
        i=match.end()
    return result,unknown

def inventory(root):
    paths=sorted(root.rglob('*'))
    if root.is_symlink() or any(p.is_symlink() for p in paths):raise ValueError('symlink source input')
    inputs=[(p,p.read_bytes()) for p in paths if p.is_file()]
    hashes=[[p.relative_to(root).as_posix(),hashlib.sha256(data).hexdigest()] for p,data in inputs]
    tree=hashlib.sha256(json.dumps(hashes,separators=(',',':')).encode()).hexdigest()
    lock=json.loads((Path(__file__).parent/'source-lock.json').read_text())
    if tree!=lock['tree_sha256']:raise ValueError('source differs from pinned baseline')
    engine=parser();calls=[];recoveries=[];scanned=0
    for (path,data),(name,digest) in zip(inputs,hashes):
        if path.suffix.lower() not in {'.c','.cpp','.cc','.cxx','.h','.hpp','.inl'}:continue
        scanned+=1
        _,found,errors=analyze(data,engine,set(FORMAT_INDEX))
        for row in found:
            index=FORMAT_INDEX[row['route']];args=row['argument_node_candidates']
            expression=args[index] if index<len(args) else None
            value=literal_expression(expression,engine) if expression is not None else None
            formats,unknown=directives(value) if value is not None else ([],[])
            calls.append(dict(row,path=name,source_sha256=digest,format_argument_index_candidate=index,
                format_expression_candidate=expression,direct_literal_candidate=value,
                directives=formats,unparsed_percent_sequences=unknown,format_binding='unresolved'))
        recoveries.extend(dict(row,path=name) for row in errors)
    return {'schema':1,'complete':False,
        'scope':'Named unpreprocessed formatting calls and direct literal format candidates; receiver/API binding and retail format coverage unresolved',
        'upstream_commit':lock['upstream_commit'],'source_tree_sha256':tree,'parser_versions':VERSIONS,
        'parser_requirements_sha256':hashlib.sha256((Path(__file__).parent/'parser-requirements.txt').read_bytes()).hexdigest(),
        'format_argument_positions':FORMAT_INDEX,
        'summary':{'files_scanned':scanned,'route_sites':len(calls),
            'routes':dict(sorted(Counter(r['route'] for r in calls).items())),
            'direct_literal_sites':sum(r['direct_literal_candidate'] is not None for r in calls),
            'unresolved_format_expressions':sum(r['direct_literal_candidate'] is None for r in calls),
            'directive_sites':sum(len(r['directives']) for r in calls),
            'unparsed_percent_sequences':sum(len(r['unparsed_percent_sequences']) for r in calls),
            'calls_with_own_parse_error':sum(r['parse_has_error'] for r in calls),'parse_recoveries':len(recoveries)},
        'calls':calls,'parse_recoveries':recoveries,
        'unknowns':['Named routes are candidates, not resolved Unicode/ASCII/CRT overloads',
            'Original legacy format argument positions need caller/signature binding',
            'Macros, aliases, custom wrappers, preprocessor reachability and parser recoveries can conceal formats',
            'Raw string literals and unsupported escapes remain unresolved expressions',
            'Dynamic/localized retail formats, codepages, locale state and argument types require separate evidence',
            'No full-engine build, format ABI or physical Vita/PSTV correctness claim']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();result=inventory(args.source);data=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(gzip.compress(data,mtime=0) if args.output.suffix=='.gz' else data)
    print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
