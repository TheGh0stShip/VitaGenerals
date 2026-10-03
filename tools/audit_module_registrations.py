#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Inventory authored addModule sites; no preprocessing or runtime claims."""
import argparse
import hashlib
import json
from pathlib import Path
import re

TOKEN = re.compile(r'//(?:\\\r?\n|[^\n])*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)

def mask(text):
    return TOKEN.sub(lambda m: ''.join('\n' if c=='\n' else ' ' for c in m[0]), text)

def scan(text):
    clean=mask(text)
    frames=[]; guards={}; definitions=[]
    for number,line in enumerate(clean.splitlines(),1):
        directive=re.match(r'\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)',line)
        if directive:
            kind,expr=directive.groups()
            if kind in {'if','ifdef','ifndef'}:
                frames.append([{'line':number,'directive':kind,'expression':expr.strip()}])
            elif kind in {'elif','else'}:
                if not frames: raise ValueError('unmatched conditional branch')
                frames[-1].append({'line':number,'directive':kind,'expression':expr.strip()})
            else:
                if not frames: raise ValueError('unmatched endif')
                frames.pop()
        guards[number]=[list(branches) for branches in frames]
        if re.match(r'\s*#\s*define\s+addModule\b',line): definitions.append(number)
    if frames: raise ValueError('unterminated conditional')
    rows=[]
    for match in re.finditer(r'\baddModule\s*\(([^()]*)\)',clean):
        line=clean.count('\n',0,match.start())+1
        if line in definitions: continue
        argument=match[1].strip()
        rows.append({'line':line,'argument':argument,
                     'class_name':argument if re.fullmatch(r'[A-Za-z_]\w*(?:::\w+)*',argument) else None,
                     'conditional_branches':guards[line],
                     'preprocessor_reachability':'unknown','runtime_registration':'unverified'})
    # Unsupported nested arguments remain explicit, rather than silently disappearing.
    starts=list(re.finditer(r'\baddModule\s*\(',clean))
    accounted=len(rows)+len(definitions)
    if len(starts)!=accounted: raise ValueError('unsupported addModule syntax')
    return rows,definitions

def inventory(root):
    files=sorted(p for p in root.rglob('*') if p.is_file())
    tree=hashlib.sha256(json.dumps([[p.relative_to(root).as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()] for p in files],separators=(',',':')).encode()).hexdigest()
    lock=json.loads((Path(__file__).parent/'source-lock.json').read_text())
    if tree!=lock['tree_sha256']: raise ValueError('source tree differs from pinned baseline')
    rows=[];definitions=[];scanned=0
    for p in files:
        if p.suffix.lower() not in {'.c','.cpp','.cc','.cxx','.h','.hpp','.inl'}: continue
        scanned+=1
        sites,defs=scan(p.read_text(encoding='latin1'))
        name=p.relative_to(root).as_posix()
        for row in sites: rows.append(dict(row,path=name,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        for line in defs: definitions.append({'path':name,'line':line})
    return {'schema':1,'complete':False,'scope':'Authored addModule macro call sites across C/C++ source and headers',
            'upstream_commit':lock['upstream_commit'],'source_tree_sha256':tree,
            'summary':{'files_scanned':scanned,'registration_sites':len(rows),'distinct_class_names':len({r['class_name'] for r in rows if r['class_name']}),'guarded_sites':sum(bool(r['conditional_branches']) for r in rows)},
            'macro_definitions':definitions,'rows':rows,
            'unknowns':['Other registrar mechanisms and macro aliases','Raw strings, token pasting and complete C++ preprocessing are outside this lexical scanner','Full preprocessor expansion and configuration reachability','Class implementation and INI binding coverage','Link retention and startup execution','Physical Vita/PSTV runtime behavior']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=inventory(a.source)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__': main()
