#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Enumerate original Direct3D/W3D boundary references, without runtime claims."""
import argparse
from collections import Counter
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
from audit_module_registrations import mask

IDENT=re.compile(r'\b(?:D3D\w*|IDirect3D\w*|CLASSID_\w*)\b|\bDX8Wrapper\s*::\s*(\w+)')
INCLUDE=re.compile(r'^\s*#\s*include\s*[<"]([^>"\n]+)[>"]',re.M)
CALL=re.compile(r'\b(DX8CALL(?:_HRES|_D3D)?)\s*\(\s*(\w+)\s*\(')

def category(name):
    if name.startswith('DX8CALL'):return 'device_call'
    for prefix,kind in [('DX8Wrapper::','wrapper_member'),('DX8CALL::','device_call'),('CLASSID_','render_class_id'),('D3DFMT_','texture_surface_format'),('D3DRS_','render_state'),('D3DTSS_','texture_stage_state'),('D3DFVF_','vertex_layout'),('D3DPT_','primitive_type'),('D3DUSAGE_','resource_usage'),('D3DLOCK_','resource_lock'),('D3DX','d3dx_helper'),('IDirect3D','device_interface')]:
        if name.startswith(prefix):return kind
    return 'other_d3d_identifier'

def scan(text):
    clean=mask(text);rows=[]
    for m in IDENT.finditer(clean):
        symbol='DX8Wrapper::'+m[1] if m[1] else m[0]
        rows.append({'symbol':symbol,'category':category(symbol),'line':clean.count('\n',0,m.start())+1})
    for m in CALL.finditer(clean):
        symbol=m[1]+'::'+m[2]
        rows.append({'symbol':symbol,'category':category(symbol),'line':clean.count('\n',0,m.start())+1})
    return sorted(rows,key=lambda r:(r['line'],r['symbol']))

def inventory(root):
    files=sorted(p for p in root.rglob('*') if p.is_file())
    hashes={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    tree=hashlib.sha256(json.dumps([[p.relative_to(root).as_posix(),hashes[p]] for p in files],separators=(',',':')).encode()).hexdigest()
    lock=json.loads((Path(__file__).parent/'source-lock.json').read_text())
    if tree!=lock['tree_sha256']:raise ValueError('source differs from pinned baseline')
    inputs=[];symbols={};includes=[];scanned=0
    for p in files:
        if p.suffix.lower() not in {'.c','.cpp','.cc','.cxx','.h','.hpp','.inl'}:continue
        scanned+=1;text=p.read_text(encoding='latin1');name=p.relative_to(root).as_posix();rows=scan(text)
        for row in rows:
            key=(row['category'],row['symbol']);symbols.setdefault(key,[]).append({'path':name,'line':row['line']})
        # Include sites are preliminary; preprocessing reachability is unknown.
        for m in INCLUDE.finditer(text):
            if re.search(r'(?:d3d|dx8)',m[1],re.I):includes.append({'path':name,'line':text.count('\n',0,m.start())+1,'include':m[1],'reachability':'unknown'})
        if rows:inputs.append({'path':name,'sha256':hashes[p]})
    rows=[{'category':k[0],'symbol':k[1],'sites':v,'target_implementation':'unverified'} for k,v in sorted(symbols.items())]
    return {'schema':1,'complete':False,'scope':'Direct3D/D3DX identifiers, DX8Wrapper members, DX8CALL methods and render CLASSID references across pinned source/header tree',
            'upstream_commit':lock['upstream_commit'],'source_tree_sha256':tree,'inputs':inputs,'rows':rows,'include_candidates':includes,
            'summary':{'files_scanned':scanned,'files_with_boundary_references':len(inputs),'distinct_symbols':len(rows),'reference_sites':sum(len(r['sites']) for r in rows),'symbols_by_category':dict(sorted(Counter(r['category'] for r in rows).items()))},
            'unknowns':['References are not unique defects or executed paths','Complete renderer object hierarchy and material/submission ownership','Macro aliases, raw strings, generated code and preprocessing','Format conversion and hardware capabilities','Shader bytecode translation and fixed-function equivalence','Target compile/link selection and runtime execution','Physical visual correctness, RAM/CDRAM usage and frame timings']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=inventory(a.source);a.output.parent.mkdir(parents=True,exist_ok=True)
    encoded=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    if a.output.suffix=='.gz':
        buffer=io.BytesIO()
        with gzip.GzipFile(fileobj=buffer,mode='wb',filename='',mtime=0) as stream:stream.write(encoded)
        a.output.write_bytes(buffer.getvalue())
    else:a.output.write_bytes(encoded)
    print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
