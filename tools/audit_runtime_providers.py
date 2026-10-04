#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Separate workspace ordering from authored linker input/provider candidates."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re

TOKENS=re.compile(r'(?:[^\s"]|"[^"]*")+')

def link_options(line):
    if not re.match(r'# ADD (?:LINK32|LIB32) ',line):raise ValueError('expected original linker/librarian directive')
    result={'library_inputs':[],'outputs':[],'import_libraries':[],'excluded_default_libraries':[],'library_search_paths':[]}
    for m in TOKENS.finditer(line):
        token=m[0];option=re.fullmatch(r'/(out|implib|nodefaultlib|libpath):(.*)',token,re.I)
        if option:
            key={'out':'outputs','implib':'import_libraries','nodefaultlib':'excluded_default_libraries','libpath':'library_search_paths'}[option[1].lower()]
            result[key].append(option[2].strip('"'))
        elif not token.startswith('/') and token.strip('"').lower().endswith('.lib'):result['library_inputs'].append(token.strip('"'))
    return result

def basename(name):return name.replace('\\','/').rsplit('/',1)[-1].casefold()

def provider_matches(library,providers):
    return [p for p in providers if basename(p['output'])==basename(library)]

def workspace_provider(row,projects):
    if row['resolution']!='found' or len(row['candidates'])!=1:return None
    return next((p for p in projects if p['path']==row['candidates'][0]),None)

def inventory(root):
    project_root=Path(__file__).resolve().parents[1];path=project_root/'reports/generated/original-projects.json.gz'
    data=path.read_bytes();original=json.loads(gzip.decompress(data));lock=json.loads((project_root/'tools/source-lock.json').read_text())
    files=sorted(p for p in root.rglob('*') if p.is_file())
    tree=hashlib.sha256(json.dumps([[p.relative_to(root).as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()] for p in files],separators=(',',':')).encode()).hexdigest()
    if tree!=lock['tree_sha256'] or original['source_tree_sha256']!=tree or original['upstream_commit']!=lock['upstream_commit']:raise ValueError('mixed or modified original source baseline')
    projects=[];providers=[]
    for p in original['projects']:
        source=root/p['path'];raw=source.read_text(encoding='latin1');lines=raw.splitlines()
        types=re.findall(r'^# TARGTYPE "([^"]+)"',raw,re.M)
        if len(types)!=1:raise ValueError('target type missing or ambiguous')
        kind='static_library' if 'Static Library' in types[0] else 'dynamic_library' if 'Dynamic-Link Library' in types[0] else 'executable' if 'Application' in types[0] else 'unknown'
        records=[]
        for flag in p['build_tokens']:
            if flag['kind'] not in {'LINK32','LIB32'}:continue
            row=dict(link_options(lines[flag['line']-1]),line=flag['line'],configuration=flag['configuration'],branch_active=flag['branch_active'])
            records.append(row)
            for output in row['outputs']+row['import_libraries']:providers.append({'project':p['path'],'configuration':row['configuration'],'line':row['line'],'output':output,'kind':kind})
        projects.append({'path':p['path'],'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_target_type':types[0],'kind':kind,'link_directives':records,'runtime_role':'unknown'})
    rts=next(w for w in original['workspaces'] if w['path']=='RTS.dsw')
    workspace=[]
    for p in rts['projects']:
        if not p['reachable_from_RTS']:continue
        match=workspace_provider(p,projects)
        workspace.append({'name':p['name'],'path':match['path'] if match else p['path'],'resolution':p['resolution'],'line':p['line'],'kind':match['kind'] if match else 'missing' if p['resolution']=='missing' else 'unresolved','dependencies':p['dependencies'],'runtime_role':'unknown'})
    for p in projects:
        for row in p['link_directives']:
            row['input_provider_candidates']=[{'library':name,'providers':provider_matches(name,providers),'configuration_compatibility':'unverified'} for name in row['library_inputs']]
    rts_project=next(p for p in projects if p['path']=='RTS.dsp')
    archive_projects=sorted({c['project'] for row in rts_project['link_directives'] for entry in row['input_provider_candidates'] for c in entry['providers'] if c['kind']=='static_library'})
    return {'schema':1,'complete':False,'scope':'Original project output kinds, typed linker directives and RTS workspace build-order closure',
            'upstream_commit':lock['upstream_commit'],'source_tree_sha256':tree,'original_project_report_sha256':hashlib.sha256(data).hexdigest(),'projects':projects,'RTS_workspace_closure':workspace,'RTS_archive_provider_candidates':archive_projects,
            'summary':{'projects':len(projects),'RTS_workspace_closure_projects':len(workspace),'RTS_closure_kinds':dict(sorted(Counter(p['kind'] for p in workspace).items())),'RTS_direct_archive_provider_projects':len(archive_projects)},
            'unknowns':['Workspace order is not runtime linkage','Exact configuration pairing and final linker retention','Pragma/default libraries and transitive static archive references','Missing middleware providers and licenses','Executable launch/build-hook/content roles','Runtime roles of source-only units and tools','Complete target engine and physical Vita/PSTV behavior']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=inventory(a.source);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
