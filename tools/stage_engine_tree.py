#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Stage the complete pinned Code tree and declared patches; execute no hooks."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from stage_original import stage as stage_patches


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def files(root):
    entries=sorted(root.rglob('*'))
    if any(p.is_symlink() for p in entries):raise ValueError('symlink staging inputs are unsupported')
    return [p for p in entries if p.is_file()]

def fingerprint(rows):
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()

def verify_existing(output):
    receipt_path=output/'receipt.json'
    if not receipt_path.is_file():raise ValueError('existing stage lacks a receipt')
    receipt=json.loads(receipt_path.read_text());expected={r['path']:r['sha256'] for r in receipt['files']}
    actual={p.relative_to(output).as_posix():sha(p) for p in files(output) if p!=receipt_path}
    if actual!=expected:raise ValueError('existing stage is modified or has unexpected files')
    return receipt

def stage(root,source,output):
    root=root.resolve();source=source.resolve()
    output=Path(os.path.abspath(output))
    if not output.is_relative_to(root):raise ValueError('output must stay in project build trees')
    parts=output.relative_to(root).parts
    if len(parts)<2 or not (parts[0]=='build' or parts[0].startswith('build-')):raise ValueError('output must be a subdirectory of build/ or build-*/')
    if any(p.is_symlink() for p in [output,*output.parents] if p.is_relative_to(root)):raise ValueError('symlink output paths are unsupported')
    lock_path=root/'tools/source-lock.json';lock_bytes=lock_path.read_bytes();lock=json.loads(lock_bytes)
    manifest_path=root/'vendor/ea/manifest.json';manifest_bytes=manifest_path.read_bytes();manifest=json.loads(manifest_bytes)
    if manifest['upstream_commit']!=lock['upstream_commit']:raise ValueError('patch/source pins differ')
    inputs=files(source);original=[[p.relative_to(source).as_posix(),sha(p)] for p in inputs]
    if fingerprint(original)!=lock['tree_sha256']:raise ValueError('source tree differs from pinned baseline')
    license_path=source.parent.parent/'LICENSE.md'
    license_sha=sha(root/'LICENSE.md')
    if license_path.is_symlink() or not license_path.is_file() or sha(license_path)!=license_sha:raise ValueError('upstream license differs from preserved license')
    if len({r['upstream_path'] for r in manifest['files']})!=len(manifest['files']):raise ValueError('duplicate original patch targets')
    for row in manifest['files']:
        prefix='GeneralsMD/Code/'
        if not row['upstream_path'].startswith(prefix):raise ValueError('patch source outside Code tree')
        relative=row['upstream_path'][len(prefix):]
        if relative not in dict(original) or dict(original)[relative]!=row['sha256']:raise ValueError('patch input differs from original tree')
    output.parent.mkdir(parents=True,exist_ok=True)
    stage_lock=output.parent/(output.name+'.lock')
    if stage_lock.is_symlink():raise ValueError('symlink staging locks are unsupported')
    with stage_lock.open('a') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX)
        old=verify_existing(output) if output.exists() else None
        with tempfile.TemporaryDirectory(prefix='.engine-stage-',dir=output.parent) as directory:
            scratch=Path(directory);generation=scratch/'generation';code=generation/'Code'
            code.mkdir(parents=True)
            for p in inputs:
                target=code/p.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
            shutil.copyfile(license_path,generation/'LICENSE.md')
            patched=scratch/'patch-sources';stage_patches(root,patched)
            for row in manifest['files']:
                target=code/row['upstream_path'].removeprefix('GeneralsMD/Code/')
                shutil.copyfile(patched/row['path'],target)
            staged=[[p.relative_to(generation).as_posix(),sha(p)] for p in files(generation)]
            expected={'Code/'+name:digest for name,digest in original};expected['LICENSE.md']=license_sha
            for row in manifest['files']:expected['Code/'+row['upstream_path'].removeprefix('GeneralsMD/Code/')]=row['staged_sha256']
            if dict(staged)!=expected:raise ValueError('complete staged tree identity mismatch')
            if lock_path.read_bytes()!=lock_bytes or manifest_path.read_bytes()!=manifest_bytes:raise ValueError('staging metadata changed during generation')
            receipt={'schema':1,'evidence_class':'complete_source_staging_only','upstream_commit':lock['upstream_commit'],
                     'source_tree_sha256':lock['tree_sha256'],'source_lock_sha256':hashlib.sha256(lock_bytes).hexdigest(),'patch_manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),
                     'patches':manifest['patches'],'staged_tree_sha256':fingerprint(staged),
                     'files':[{'path':p,'sha256':digest} for p,digest in staged],
                     'source_files':len(inputs),'patched_files':len(manifest['files']),'engine_build_established':False,'hardware_verified':False}
            (generation/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
            if old==receipt:return receipt
            previous=scratch/'previous'
            if output.exists():os.replace(output,previous)
            try:os.replace(generation,output)
            except BaseException:
                if previous.exists() and not output.exists():os.replace(previous,output)
                raise
        return receipt

def summary(receipt):
    keys=['upstream_commit','source_tree_sha256','source_lock_sha256','patch_manifest_sha256','staged_tree_sha256','source_files','patched_files','engine_build_established','hardware_verified']
    return dict({k:receipt[k] for k in keys},schema=1,complete=False,scope='Complete pinned Code file staging and declared patch outputs',evidence_class='source_staging_only')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--summary',type=Path);a=p.parse_args()
    if a.summary and (a.summary.resolve().is_relative_to(a.source.resolve().parent.parent) or a.summary.resolve().is_relative_to(a.output.resolve())):
        p.error('summary must stay outside the pristine source and staged generation')
    result=stage(Path(__file__).resolve().parents[1],a.source,a.output)
    if a.summary:
        a.summary.parent.mkdir(parents=True,exist_ok=True);a.summary.write_text(json.dumps(summary(result),indent=2,sort_keys=True)+'\n')
    print(f"PASS: {result['source_files']} original Code files staged; {result['patched_files']} declared patched files; no engine build or hardware proof")
if __name__=='__main__':main()
