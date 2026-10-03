#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install the hash-pinned, isolated CI SDK without package hooks or updates."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tarfile
import urllib.request

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[1];directory=a.directory.resolve()
    if not directory.is_relative_to(root) or not directory.relative_to(root).parts[0].startswith('build-'):
        p.error('SDK installation must remain under an ignored build-*/ tree')
    if platform.system()!='Linux' or platform.machine()!='x86_64':
        p.error('pinned SDK host is x86_64 Linux; Vita target remains ARMv7-A')
    lock=json.loads((root/'tools/vitasdk-lock.json').read_text())
    directory.mkdir(parents=True,exist_ok=True)
    archive=directory/'sdk.tar.bz2'
    if not archive.is_file():
        request=urllib.request.Request(lock['url'],headers={'User-Agent':'VitaGenerals-build'})
        temporary=directory/'sdk.tar.bz2.partial'
        with urllib.request.urlopen(request,timeout=60) as response,temporary.open('wb') as output:
            for chunk in iter(lambda:response.read(1024*1024),b''): output.write(chunk)
        temporary.replace(archive)
    with archive.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    if digest!=lock['sha256']: raise ValueError('SDK archive hash mismatch')
    # Data filter forbids traversal and unsafe link targets. Extraction executes no hooks.
    with tarfile.open(archive,'r:bz2') as package:
        package.extractall(directory,filter='data')
    compiler=directory/'vitasdk/bin/arm-vita-eabi-gcc'
    target=subprocess.check_output([str(compiler),'-dumpmachine'],text=True).strip()
    if target!=lock['target']: raise ValueError('SDK target identity mismatch')
    (directory/'sdk-receipt.json').write_text(json.dumps(lock,indent=2)+'\n')
    print(f"PASS: {lock['release']} SHA-256 and ARM target identity verified")
if __name__=='__main__': main()
