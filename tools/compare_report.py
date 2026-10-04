#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare typed JSON report content independently of gzip/zlib encoding."""
import argparse
import gzip
import json
from pathlib import Path

def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate report key')
        result[key]=value
    return result

def invalid_constant(value):raise ValueError('nonfinite JSON report value')

def canonical(path):
    data=path.read_bytes()
    if path.suffix=='.gz':data=gzip.decompress(data)
    value=json.loads(data,object_pairs_hook=unique_object,parse_constant=invalid_constant)
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)

def compare(left,right):
    if canonical(left)!=canonical(right):raise ValueError('report content differs')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('published',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    compare(a.published,a.generated);print('PASS: identical typed JSON report content')
if __name__=='__main__':main()
