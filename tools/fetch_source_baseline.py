#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fetch only the pinned official source revision; never run project build hooks."""
import argparse
import json
from pathlib import Path
import subprocess

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[1];directory=a.directory.resolve()
    if not directory.is_relative_to(root) or not directory.relative_to(root).parts[0].startswith('build-'):
        p.error('source checkout must remain under ignored build-*/')
    lock=json.loads((root/'tools/source-lock.json').read_text())
    def git(*args):
        return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=directory,text=True).strip()
    if directory.exists() and any(directory.iterdir()):
        if not (directory/'.git').is_dir(): p.error('existing source directory is not a Git checkout')
        if git('remote','get-url','origin')!=lock['upstream_url'] or git('rev-parse','HEAD')!=lock['upstream_commit']:
            p.error('existing checkout differs from pinned source; not overwritten')
        if git('status','--porcelain'): p.error('existing source checkout is modified')
    else:
        directory.mkdir(parents=True,exist_ok=True)
        git('init','--quiet')
        git('remote','add','origin',lock['upstream_url'])
        git('fetch','--quiet','--depth','1','origin',lock['upstream_commit'])
        git('checkout','--quiet','--detach','FETCH_HEAD')
    print('PASS: pristine official source commit '+lock['upstream_commit'])
if __name__=='__main__': main()
