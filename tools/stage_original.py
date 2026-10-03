#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Hash-pinned, zero-fuzz staging of declared original source; no build hooks."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import os

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def within(root, relative):
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('manifest path escapes root')
    return path

def stage(root, output):
    root, output = root.resolve(), output.resolve()
    if output == root or not output.is_relative_to(root):
        raise ValueError('staging output must be inside project build tree')
    if not any(output.is_relative_to(p.resolve()) for p in [root/'build', *root.glob('build-*')]):
        raise ValueError('staging output must be under build/ or build-*/')
    manifest_path = root/'vendor/ea/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    paths = [r['path'] for r in manifest['files']]
    if len(paths)!=len(set(paths)):
        raise ValueError('duplicate staging paths')
    # Validate all inputs before creating or modifying staging.
    for row in manifest['files']:
        if sha(within(root/'vendor/ea',row['path'])) != row['sha256']:
            raise ValueError('original source hash mismatch')
        within(output,row['path'])
    for patch in manifest['patches']:
        if sha(within(root,patch['path'])) != patch['sha256']:
            raise ValueError('patch hash mismatch')
    output.parent.mkdir(parents=True,exist_ok=True)
    receipt={'schema':1,'manifest_sha256':sha(manifest_path),'inputs':manifest['files'],
             'patches':manifest['patches'],'evidence_class':'source_staging_only'}
    with tempfile.TemporaryDirectory(prefix='.source-stage-',dir=output.parent) as directory:
        scratch=Path(directory)
        for row in manifest['files']:
            target=within(scratch,row['path'])
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(within(root/'vendor/ea',row['path']).read_bytes())
            if sha(target)!=row['sha256']:
                raise ValueError('staged input hash mismatch')
        for patch in manifest['patches']:
            command=['patch','--batch','--forward','--fuzz=0','--no-backup-if-mismatch',
                     '--reject-file=-','-p1','-d',str(scratch),'-i',str(within(root,patch['path']))]
            subprocess.run(command+['--dry-run'],check=True,capture_output=True)
            subprocess.run(command,check=True,capture_output=True)
        for row in manifest['files']:
            if sha(within(scratch,row['path'])) != row['staged_sha256']:
                raise ValueError('patched source hash mismatch')
        allowed=set(paths)|{'receipt.json'}
        if output.exists() and any(p.relative_to(output).as_posix() not in allowed
                                   for p in output.rglob('*') if p.is_file()):
            raise ValueError('unexpected files in staging output')
        output.mkdir(parents=True,exist_ok=True)
        (output/'receipt.json').unlink(missing_ok=True)
        for row in manifest['files']:
            target=within(output,row['path']);target.parent.mkdir(parents=True,exist_ok=True)
            incoming=within(scratch,row['path'])
            if not target.is_file() or target.read_bytes()!=incoming.read_bytes():
                os.replace(incoming,target)
        staged_receipt=scratch/'receipt.json'
        staged_receipt.write_text(json.dumps(receipt,indent=2)+'\n')
        os.replace(staged_receipt,output/'receipt.json')
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    result=stage(Path(__file__).resolve().parents[1],a.output)
    print(f"PASS: {len(result['inputs'])} original files staged with verified patches")
if __name__=='__main__':
    main()
