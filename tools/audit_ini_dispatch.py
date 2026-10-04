#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pinned top-level INI block dispatch and source definition candidates."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from audit_module_registrations import TOKEN, mask
from audit_script_dispatch import block

OWNER='GameEngine/Source/Common/INI/INI.cpp'

def table_rows(text):
    # Keep ordinary literals for authored tokens, blank comments with same layout.
    clean=TOKEN.sub(lambda m: m[0] if m[0][0] in {'"',"'"} else ''.join('\n' if c=='\n' else ' ' for c in m[0]),text)
    start,end=block(mask(text),r'\btheTypeTable\s*\[\s*\]\s*=')
    body=clean[start:end]
    pattern=re.compile(r'\{\s*("[A-Za-z_]\w*"|NULL)\s*,\s*([A-Za-z_]\w*(?:::\w+)*)\s*\}\s*,?')
    rows=[];cursor=0;sentinel=False
    for m in pattern.finditer(body):
        if body[cursor:m.start()].strip():raise ValueError('unsupported table initializer')
        if sentinel:raise ValueError('entry follows null sentinel')
        if m[1]=='NULL':
            if m[2]!='NULL':raise ValueError('invalid sentinel')
            sentinel=True
        else:
            rows.append({'token':m[1][1:-1],'handler':m[2],'line':clean.count('\n',0,start+m.start())+1})
        cursor=m.end()
    if body[cursor:].strip() or not sentinel:raise ValueError('incomplete dispatch table')
    if len({r['token'] for r in rows})!=len(rows):raise ValueError('duplicate table token')
    return rows

def definitions(text,handler):
    clean=mask(text)
    pattern=r'(?<![\w:])'+re.escape(handler)+r'\s*\([^;{}]*\)\s*\{'
    return [clean.count('\n',0,m.start())+1 for m in re.finditer(pattern,clean)]

def inventory(root):
    files=sorted(p for p in root.rglob('*') if p.is_file())
    hashes={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    tree=hashlib.sha256(json.dumps([[p.relative_to(root).as_posix(),hashes[p]] for p in files],separators=(',',':')).encode()).hexdigest()
    lock=json.loads((Path(__file__).parent/'source-lock.json').read_text())
    if tree!=lock['tree_sha256']:raise ValueError('source differs from pinned baseline')
    rows=table_rows((root/OWNER).read_text(encoding='latin1'))
    sources=[p for p in files if p.suffix.lower() in {'.c','.cc','.cpp','.cxx','.h','.hpp','.inl'}]
    for row in rows:row.update(path=OWNER,definition_candidates=[],target_selection='unknown',runtime_binding='unverified')
    for p in sources:
        text=p.read_text(encoding='latin1')
        for row in rows:
            if row['handler'] not in text:continue
            for line in definitions(text,row['handler']):row['definition_candidates'].append({'path':p.relative_to(root).as_posix(),'line':line,'sha256':hashes[p]})
    return {'schema':1,'complete':False,'scope':'Original theTypeTable top-level INI tokens and lexical handler definition candidates',
            'upstream_commit':lock['upstream_commit'],'source_tree_sha256':tree,'dispatch_source_sha256':hashes[root/OWNER],
            'summary':{'block_tokens':len(rows),'files_scanned_for_definitions':len(sources),'tokens_without_definition_candidate':sum(not r['definition_candidates'] for r in rows),'tokens_with_multiple_definition_candidates':sum(len(r['definition_candidates'])>1 for r in rows)},
            'rows':rows,'unknowns':['Full C++ preprocessing, raw strings and generated definitions','Nested field parse tables and object module configuration','Retail block/field references and mount precedence','Inheritance, overrides, includes and duplicate semantics','Pointer/offset field layout on ARM and LP64 host','Target build selection, link retention and physical runtime behavior']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=inventory(a.source);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
