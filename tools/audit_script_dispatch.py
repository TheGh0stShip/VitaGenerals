#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare original script enums with their runtime dispatcher case labels."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from audit_module_registrations import mask

HEADER='GameEngine/Include/GameLogic/Scripts.h'
BASE='GameEngine/Source/GameLogic/ScriptEngine/'

def block(clean, pattern):
    matches=list(re.finditer(pattern,clean))
    if len(matches)!=1: raise ValueError('owner declaration missing or ambiguous')
    opening=clean.find('{',matches[0].end())
    if opening<0: raise ValueError('owner body missing')
    depth=1;end=opening+1
    while end<len(clean) and depth:
        depth += (clean[end]=='{')-(clean[end]=='}');end+=1
    if depth: raise ValueError('unbalanced owner body')
    return opening+1,end-1

def enum_rows(text,name):
    clean=mask(text);start,end=block(clean,r'\benum\s+'+re.escape(name)+r'\b(?=\s*\{)')
    body=clean[start:end];rows=[];cursor=start;value=0
    if '#' in body: raise ValueError('conditional enum requires preprocessing review')
    for part in body.split(','):
        if not part.strip(): cursor+=len(part)+1;continue
        match=re.fullmatch(r'\s*([A-Za-z_]\w*)\s*(?:=\s*(-?\d+))?\s*',part)
        if not match: raise ValueError('unsupported enum expression')
        if match[2] is not None:value=int(match[2])
        rows.append({'name':match[1],'value':value,'line':clean.count('\n',0,cursor+part.index(match[1]))+1})
        value+=1;cursor+=len(part)+1
    if len({r['name'] for r in rows})!=len(rows):raise ValueError('duplicate enum name')
    return rows

def dispatch_rows(text,owner,qualifier):
    clean=mask(text);start,end=block(clean,re.escape(owner)+r'\s*\([^;{}]*\)')
    body=clean[start:end]
    labels=list(re.finditer(r'\bcase\s+'+re.escape(qualifier)+r'::(\w+)\s*:',body))
    # Refuse labels outside the supported syntax instead of dropping them.
    if len(labels)!=len(re.findall(r'\bcase\b',body)):raise ValueError('unsupported dispatch case')
    rows=[]
    for i,m in enumerate(labels):
        stop=labels[i+1].start() if i+1<len(labels) else len(body)
        fragment=body[m.end():stop]
        rows.append({'name':m[1],'line':clean.count('\n',0,start+m.start())+1,
                     'call_identifier_candidates':sorted(set(re.findall(r'\b([A-Za-z_]\w*)\s*\(',fragment)) - {'if','switch','while','for','sizeof'}),
                     'constant_return_candidates':re.findall(r'\breturn\s+(true|false|TRUE|FALSE|0|1)\s*;',fragment),
                     'behavior_verified':False})
    return rows

def inventory(root):
    files=sorted(p for p in root.rglob('*') if p.is_file())
    tree=hashlib.sha256(json.dumps([[p.relative_to(root).as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()] for p in files],separators=(',',':')).encode()).hexdigest()
    lock=json.loads((Path(__file__).parent/'source-lock.json').read_text())
    if tree!=lock['tree_sha256']:raise ValueError('source tree differs from pinned baseline')
    inputs=[]
    def read(path):
        data=(root/path).read_bytes();inputs.append({'path':path,'sha256':hashlib.sha256(data).hexdigest()})
        return data.decode('latin1')
    header=read(HEADER);engine=read(BASE+'ScriptEngine.cpp');groups=[]
    for enum,qualifier,file,owner in [('ScriptActionType','ScriptAction','ScriptActions.cpp','ScriptActions::executeAction'),('ConditionType','Condition','ScriptConditions.cpp','ScriptConditions::evaluateCondition')]:
        declared=enum_rows(header,enum)
        engine_owner='ScriptEngine::executeActions' if qualifier=='ScriptAction' else 'ScriptEngine::evaluateCondition'
        dispatchers=[{'path':BASE+file,'owner':owner},{'path':BASE+'ScriptEngine.cpp','owner':engine_owner}]
        sites=[]
        for dispatcher,text in zip(dispatchers,[read(BASE+file),engine]):
            sites.extend(dict(r,**dispatcher) for r in dispatch_rows(text,dispatcher['owner'],qualifier))
        template_array='m_actionTemplates' if qualifier=='ScriptAction' else 'm_conditionTemplates'
        templates=[{'name':m[1],'line':engine.count('\n',0,m.start())+1,'path':BASE+'ScriptEngine.cpp'} for m in re.finditer(r'curTemplate\s*=\s*&'+template_array+r'\s*\[\s*'+qualifier+r'::(\w+)\s*\]',mask(engine))]
        names={r['name'] for r in declared};covered={r['name'] for r in sites}
        if covered-names:raise ValueError('dispatch label absent from enum')
        if {r['name'] for r in templates}-names:raise ValueError('template assignment absent from enum')
        groups.append({'enum':enum,'declarations':declared,'dispatchers':dispatchers,'cases':sites,'template_assignment_sites':templates,
                       'declared_without_template_assignment':sorted(names-{r['name'] for r in templates}),
                       'declared_without_case':sorted(names-covered),
                       'duplicate_case_names':[n for n,c in Counter(r['name'] for r in sites).items() if c>1]})
    return {'schema':1,'complete':False,'scope':'ScriptActionType/ConditionType declarations and original engine/subsystem runtime case labels and template assignments',
            'upstream_commit':lock['upstream_commit'],'source_tree_sha256':tree,'inputs':inputs,'groups':groups,
            'summary':{g['enum']:{'declarations':len(g['declarations']),'case_sites':len(g['cases']),'template_assignment_sites':len(g['template_assignment_sites']),'declared_without_case':len(g['declared_without_case'])} for g in groups},
            'unknowns':['Enum sentinels and legacy values need role review','Template registration and parameter semantics','Nested switch labels, fallthrough and control-flow interpretation','Guard/configuration reachability','Retail map/challenge/campaign script references','Save/load remapping and backward compatibility','Target build selection and physical runtime execution']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=inventory(a.source);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
