#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Join pinned sweep evidence into a single dependency ledger."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

SEVERITIES={'blocking','required','measurement'}

def pointer(document,path):
    if not path.startswith('/'):raise ValueError('evidence pointer must be absolute')
    value=document
    for part in path[1:].split('/'):
        key=part.replace('~1','/').replace('~0','~')
        value=value[int(key)] if isinstance(value,list) else value[key]
    return value

def validate(registry,reports,lock):
    if set(registry['reports'])!=set(reports):raise ValueError('report set mismatch')
    for report in reports.values():
        if report.get('upstream_commit')!=lock['upstream_commit'] or report.get('source_tree_sha256')!=lock['tree_sha256']:
            raise ValueError('mixed or unpinned source evidence')
    findings=registry['findings'];ids=[f['id'] for f in findings]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate finding identity')
    byid={f['id']:f for f in findings}
    for f in findings:
        if f['severity'] not in SEVERITIES or f['kind']!='evidence_gap' or f['status']!='open':raise ValueError('unsupported finding classification')
        if not f['evidence'] or not f['closure_evidence']:raise ValueError('finding lacks evidence or closure criteria')
        if len(f['depends_on'])!=len(set(f['depends_on'])):raise ValueError('duplicate dependency')
        for dependency in f['depends_on']:
            if dependency not in byid:raise ValueError('unknown dependency')
        for ref in f['evidence']:pointer(reports[ref['report']],ref['pointer'])
    order=[];active=set();seen=set()
    def visit(id):
        if id in active:raise ValueError('cyclic finding dependencies')
        if id in seen:return
        active.add(id)
        for child in byid[id]['depends_on']:visit(child)
        active.remove(id);seen.add(id);order.append(id)
    for id in ids:visit(id)
    scopes=[r['scope'] for r in registry['coverage_obligations']]
    if len(scopes)!=len(set(scopes)):raise ValueError('duplicate coverage obligation')
    if any(r['status'] not in {'partial','not_established'} for r in registry['coverage_obligations']):raise ValueError('unsupported completeness claim')
    return order

def consolidate(root):
    registry_path=root/'port/sweep-gaps.json';registry=json.loads(registry_path.read_text())
    lock=json.loads((root/'tools/source-lock.json').read_text());reports={};inputs=[]
    for name in registry['reports']:
        if Path(name).name!=name:raise ValueError('report path must be a basename')
        path=root/'reports/generated'/name;data=path.read_bytes()
        reports[name]=json.loads(gzip.decompress(data) if name.endswith('.gz') else data)
        inputs.append({'report':name,'sha256':hashlib.sha256(data).hexdigest()})
    order=validate(registry,reports,lock);findings=[]
    for f in registry['findings']:
        evidence=[dict(ref,observed_value=pointer(reports[ref['report']],ref['pointer'])) for ref in f['evidence']]
        findings.append(dict(f,evidence=evidence))
    return {'schema':1,'complete':False,'evidence_class':'consolidated_static_evidence_gaps','upstream_commit':lock['upstream_commit'],'source_tree_sha256':lock['tree_sha256'],
            'registry_sha256':hashlib.sha256(registry_path.read_bytes()).hexdigest(),'inputs':inputs,'dependency_order':order,'findings':findings,'coverage_obligations':registry['coverage_obligations'],
            'summary':{'parent_evidence_gaps':len(findings),'by_severity':dict(sorted(Counter(f['severity'] for f in findings).items()))},'counting_rule':registry['counting_rule'],'hardware_acceptance_established':False}

def markdown(result):
    lines=['# Consolidated port gaps','','Generated from `port/sweep-gaps.json` and '+str(len(result['inputs']))+' pinned sweep reports. All findings','are open evidence gaps; counts do not represent unique defects or game completion.','Repeated engine-build gaps from individual sweeps share one parent finding.',
           'Dependencies are joint closure prerequisites, not an exclusive work schedule.',
           'Unique IDs prevent duplicate identities; semantic grouping remains a reviewed',
           'registry decision. The nine current findings are not a complete defect census.','','| Gap | Priority | Dependencies |','| --- | --- | --- |']
    for f in result['findings']:lines.append('| '+f['id']+': '+f['title']+' | '+f['severity']+' | '+(', '.join(f['depends_on']) or 'None')+' |')
    lines+=['','## Evidence and closure criteria','']
    for f in result['findings']:
        lines+=['### '+f['id'],'',f['closure_evidence'],'','Evidence: '+', '.join('['+r['report']+'](../reports/generated/'+r['report']+') `'+r['pointer']+'`' for r in f['evidence'])+'.','']
    lines+=['## Complete-game coverage obligations','','| Scope | Evidence status |','| --- | --- |']
    for r in result['coverage_obligations']:lines.append('| '+r['scope'].replace('_',' ')+' | '+r['status'].replace('_',' ')+' |')
    lines+=['','Partial inventories retain unknowns. Reference, symbol, declaration, parser-recovery','and site counts are observations inside these findings, not additional findings.','Host/ARM compile evidence does not establish physical Vita/PSTV correctness.','','Reproduce: `python3 tools/consolidate_sweep_gaps.py --output build-gaps/consolidated-gaps.json --ledger build-gaps/PORT_GAPS.md`.','Compare both outputs with their published counterparts.']
    return '\n'.join(lines)+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ledger',type=Path,required=True);a=p.parse_args()
    result=consolidate(Path(__file__).resolve().parents[1])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    a.ledger.parent.mkdir(parents=True,exist_ok=True);a.ledger.write_text(markdown(result))
    print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
