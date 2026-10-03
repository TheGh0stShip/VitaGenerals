#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare regenerated original-source metadata, excluding machine-specific build hash."""
import argparse
import gzip
import json
from pathlib import Path

def load(path):
    data=path.read_bytes()
    if path.suffix=='.gz': data=gzip.decompress(data)
    result=json.loads(data)
    result.pop('compile_commands_sha256',None)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('regenerated',type=Path);a=p.parse_args()
    expected=Path(__file__).resolve().parents[1]/'reports/generated/original-projects.json.gz'
    actual=load(a.regenerated);snapshot=load(expected)
    if actual!=snapshot: raise ValueError('published original-project inventory does not match regeneration')
    if actual['total']!=len(actual['rows']): raise ValueError('translation-unit denominator mismatch')
    print('PASS: published original-project inventory reproduced from pristine source and ARM selection')
if __name__=='__main__': main()
