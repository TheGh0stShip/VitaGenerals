#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Original VC6 project denominators; no build hooks are executed."""
import argparse
import gzip
import io
from collections import Counter
import hashlib
import json
from pathlib import Path
import posixpath
import re
import shlex

TRANSLATION={'.c','.cpp','.cc','.cxx'}
def digest(data):
    return hashlib.sha256(data).hexdigest()
def tri_and(a,b):
    if a is False or b is False: return False
    if a is None or b is None: return None
    return True
def tri_or(a,b):
    if a is True or b is True: return True
    if a is None or b is None: return None
    return False
def tri_not(a):
    return None if a is None else not a

def condition(expression, config):
    match=re.fullmatch(r'\s*"\$\(CFG\)"\s*(==|!=)\s*"([^"]+)"\s*',expression)
    if not match: return None
    return (config==match[2]) if match[1]=='==' else (config!=match[2])

def parse_dsp(text):
    configs=list(dict.fromkeys(re.findall(r'^# Name "([^"]+)"',text,re.M)))
    if not configs: raise ValueError('project configurations missing')
    rows={}; flags=[]; unknown=[]; encountered=0; hooks={}
    for config in configs:
        frames=[]; active=True; current=None; groups=[]; custom=False
        for lineno,line in enumerate(text.splitlines(),1):
            if line.startswith('!IF '):
                encountered+=1
                value=condition(line[4:],config)
                frames.append({'parent':active,'seen':value})
                active=tri_and(active,value)
                if value is None: unknown.append({'line':lineno,'configuration':config})
            elif line.startswith('!ELSEIF '):
                if not frames: raise ValueError('ELSEIF without IF')
                encountered+=1
                frame=frames[-1]; value=condition(line[8:],config)
                active=tri_and(frame['parent'],tri_and(tri_not(frame['seen']),value))
                frame['seen']=tri_or(frame['seen'],value)
                if value is None: unknown.append({'line':lineno,'configuration':config})
            elif line.startswith('!ELSE'):
                if not frames: raise ValueError('ELSE without IF')
                frame=frames[-1];active=tri_and(frame['parent'],tri_not(frame['seen']));frame['seen']=True
            elif line.startswith('!ENDIF'):
                if not frames: raise ValueError('ENDIF without IF')
                active=frames.pop()['parent']
            elif line.startswith('!') and not line.startswith('!MESSAGE'):
                raise ValueError('unsupported IDE directive')
            elif line.startswith('# Begin Group '):
                groups.append(line[len('# Begin Group '):].strip().strip('"'))
            elif line.startswith('# End Group'):
                if groups: groups.pop()
            elif line.startswith('# Begin Custom Build'):
                custom=True
                hooks.setdefault(lineno,{'line':lineno,'kind':'custom_build','configurations':{}})['configurations'][config]=active
            elif line.startswith('# End Custom Build'):
                custom=False
            elif line.startswith('SOURCE=') and not custom:
                current=lineno
                source=line[7:].strip().strip('"').replace('\\','/')
                row=rows.setdefault(current,{'source_expression':source,'line':lineno,'groups':list(groups),'configurations':{}})
                row['configurations'][config]={'present':active,'excluded':False,'exclusion_lines':[]}
            elif line.startswith('# End Source File'):
                current=None
            elif re.match(r'# PROP Exclude_From_Build [01]$',line):
                if current is None: raise ValueError('source exclusion outside source block')
                entry=rows[current]['configurations'][config]
                if active is not False:
                    entry['exclusion_lines'].append(lineno)
                    value=line.endswith('1')
                    entry['excluded']=value if active is True else None
            elif re.match(r'# ADD (?:CPP|LINK32|LIB32) ',line) and active is not False:
                kind=line.split()[2]
                if kind=='CPP':
                    values=re.findall(r'/I\s+"([^"]+)"',line)
                    values += re.findall(r'/D\s+"?([^"\s]+)',line)
                else:
                    values=re.findall(r'(?i)\b[\w.-]+\.lib\b',line)
                flags.append({'configuration':config,'line':lineno,'kind':kind,'tokens':values,'branch_active':active})
        if frames: raise ValueError('unterminated conditional')
    return {'configurations':configs,'rows':list(rows.values()),'build_tokens':flags,'unresolved_conditions':unknown,'conditions_evaluated':encountered,'build_hook_candidates':list(hooks.values())}

def parse_dsw(text):
    matches=list(re.finditer(r'^Project: "([^"]+)"\s*=\s*(.*?)\s*- Package Owner=',text,re.M))
    rows=[]
    for i,match in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else len(text)
        body=text[match.end():end]
        rows.append({'name':match[1],'project_expression':match[2].strip('"').replace('\\','/'),
                     'line':text.count('\n',0,match.start())+1,
                     'dependencies':re.findall(r'^\s*Project_Dep_Name (.*?)\s*$',body,re.M)})
    return rows

def normalized_relative(base, expression):
    if '$(' in expression or re.match(r'^[A-Za-z]:|^/',expression): return None
    return posixpath.normpath(posixpath.join(base,expression))

def inventory(root, selected=None):
    files=sorted(p for p in root.rglob('*') if p.is_file())
    bycase={}
    for p in files: bycase.setdefault(p.relative_to(root).as_posix().casefold(),[]).append(p.relative_to(root).as_posix())
    def resolve(base,expression):
        candidate=normalized_relative(base,expression)
        if candidate is None or candidate=='..' or candidate.startswith('../'):
            return {'path':None,'candidates':[],'resolution':'outside_or_computed'}
        found=bycase.get(candidate.casefold(),[])
        return {'path':candidate,'candidates':found,
                'resolution':'found' if len(found)==1 else 'case_collision' if found else 'missing'}
    projects=[];workspaces=[];input_hashes=[]
    referenced={}
    for path in files:
        suffix=path.suffix.lower()
        if suffix not in {'.dsp','.dsw'}: continue
        name=path.relative_to(root).as_posix(); text=path.read_text(encoding='latin1')
        input_hashes.append({'path':name,'sha256':digest(path.read_bytes())})
        if suffix=='.dsw':
            entries=parse_dsw(text)
            for row in entries: row.update(resolve(posixpath.dirname(name),row['project_expression']))
            workspaces.append({'path':name,'projects':entries})
            continue
        project=parse_dsp(text);project['path']=name
        for row in project['rows']:
            row.update(resolve(posixpath.dirname(name),row['source_expression']))
            row['translation_unit']=Path(row['source_expression']).suffix.lower() in TRANSLATION
            row['selected_for_vita']=None if selected is None else any(p in selected for p in row['candidates'])
            row['status']='unknown'
            for found in row['candidates']: referenced.setdefault(found,[]).append({'project':name,'line':row['line']})
        projects.append(project)
    units=[{'path':p.relative_to(root).as_posix(),'sha256':digest(p.read_bytes()),
            'original_project_references':referenced.get(p.relative_to(root).as_posix(),[]),
            'status':'unknown','selected_for_vita':None if selected is None else p.relative_to(root).as_posix() in selected} for p in files if p.suffix.lower() in TRANSLATION]
    for workspace in workspaces:
        names={r['name'].casefold():r for r in workspace['projects']}
        seeds=['rts'] if 'rts' in names else []
        reached=set();pending=list(seeds)
        while pending:
            name=pending.pop()
            if name in reached: continue
            reached.add(name)
            if name in names: pending.extend(d.casefold() for d in names[name]['dependencies'])
        workspace['RTS_dependency_closure']=sorted(reached)
        workspace['unlisted_dependency_names']=sorted(n for n in reached if n not in names)
        for row in workspace['projects']: row['reachable_from_RTS']=row['name'].casefold() in reached
    summary={'projects':len(projects),'workspaces':len(workspaces),'translation_units':len(units),
             'units_without_original_project_reference':sum(not r['original_project_references'] for r in units),
             'source_reference_resolutions':dict(Counter(r['resolution'] for p in projects for r in p['rows'])),
             'custom_build_hook_sites':sum(len(p['build_hook_candidates']) for p in projects),
             'configuration_conditions_evaluated':sum(p['conditions_evaluated'] for p in projects),
             'unresolved_configuration_conditions':sum(len(p['unresolved_conditions']) for p in projects),
             'missing_workspace_projects':sum(r['resolution']=='missing' for w in workspaces for r in w['projects'])}
    return {'schema':1,'complete':False,'scope':'All supplied Zero Hour Code project/workspace references and C/C++ translation units',
            'source_tree_sha256':digest(json.dumps([[p.relative_to(root).as_posix(),digest(p.read_bytes())] for p in files],separators=(',',':')).encode()),
            'evidence_class':'original_project_metadata','summary':summary,
            'inputs':input_hashes,'projects':projects,'workspaces':workspaces,'rows':units,'total':len(units),
            'counts':{'unknown':len(units)},
            'open_risks':['Runtime/tool role review','Workspace build order is not final link retention',
                          'Source-only units and generated sources','Missing middleware and original dependencies',
                          'Per-configuration selection differs from port selection','Registrar execution and physical runtime']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--compile-commands',type=Path)
    a=p.parse_args()
    if not a.source.is_dir(): p.error('source root missing')
    selected=None
    if a.compile_commands:
        database=json.loads(a.compile_commands.read_text())
        compiled=set()
        for row in database:
            arguments=row.get('arguments') or shlex.split(row['command'])
            if not arguments or Path(arguments[0]).name not in {'arm-vita-eabi-gcc','arm-vita-eabi-g++','arm-vita-eabi-c++'}:
                p.error('Vita selection audit requires an ARM Vita compile database')
            compiled.add(str((Path(row['directory'])/row['file']).resolve()))
        project=Path(__file__).resolve().parents[1]
        manifest=json.loads((project/'vendor/ea/manifest.json').read_text())
        staged=a.compile_commands.parent/'staged'
        selected={r['upstream_path'].removeprefix('GeneralsMD/Code/') for r in manifest['files']
                  if str((staged/r['path']).resolve()) in compiled}
    result=inventory(a.source,selected)
    pin=json.loads((Path(__file__).resolve().parents[1]/'tools/source-lock.json').read_text())
    if result['source_tree_sha256']!=pin['tree_sha256']:
        p.error('source tree differs from the pinned pristine baseline')
    result['upstream_commit']=pin['upstream_commit']
    result['source_lock_verified']=True
    if a.compile_commands:
        result['compile_commands_sha256']=digest(a.compile_commands.read_bytes())
        result['selected_original_sources']=sorted(selected)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    encoded=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    if a.output.suffix=='.gz':
        buffer=io.BytesIO()
        with gzip.GzipFile(fileobj=buffer,mode='wb',filename='',mtime=0) as stream:
            stream.write(encoded)
        a.output.write_bytes(buffer.getvalue())
    else:
        a.output.write_bytes(encoded)
    print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__': main()
