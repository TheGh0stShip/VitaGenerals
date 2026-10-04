#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate the exact staged Git tree with no ignored source or retail inputs."""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ref');p.add_argument('--vita-sdk',type=Path)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    tree=subprocess.check_output(['git','rev-parse',a.ref+'^{tree}'] if a.ref else ['git','write-tree'],cwd=root,text=True).strip()
    content=subprocess.check_output(['git','archive',tree],cwd=root)
    receipts=root/'build-publication';receipts.mkdir(exist_ok=True)
    result={'schema':1,'tree':tree,'checks':[],'hardware_verified':False}
    with tempfile.TemporaryDirectory(prefix='vita-generals-snapshot-') as directory:
        snapshot=Path(directory)
        with tarfile.open(fileobj=io.BytesIO(content)) as archive:
            archive.extractall(snapshot,filter='data')
        environment=os.environ.copy()
        # Host checks must not silently consume the caller's cross toolchain.
        environment.pop('CMAKE_TOOLCHAIN_FILE',None)
        checks=[('host_contracts',[sys.executable,'tools/run_host_probes.py','--build-dir','build-publication-host','--sanitizer','asan-ubsan']),
                ('host_engine_clusters',[sys.executable,'tools/run_engine_clusters.py','--mode','host',
                                         '--build-dir','build-publication-clusters-host']),
                ('host_engine_clusters_cp932',[sys.executable,'tools/run_engine_clusters.py','--mode','host',
                                               '--build-dir','build-publication-clusters-cp932',
                                               '--legacy-encoding','CP932'])]
        if a.vita_sdk:
            sdk=a.vita_sdk.resolve();environment['VITASDK']=str(sdk)
            checks += [('arm_configure',['cmake','-S','.','-B','build-publication-arm','-DCMAKE_BUILD_TYPE=Debug',
                                        '-DCMAKE_TOOLCHAIN_FILE='+str(sdk/'share/vita.toolchain.cmake')]),
                       ('arm_build',['cmake','--build','build-publication-arm','--parallel','2']),
                       ('arm_identity',['python3','tools/record_build_identity.py','--build-dir','build-publication-arm']),
                       ('arm_engine_clusters',[sys.executable,'tools/run_engine_clusters.py','--mode','vita',
                                               '--build-dir','build-publication-clusters-arm','--vita-sdk',str(sdk)])]
        for name,command in checks:
            completed=subprocess.run(command,cwd=snapshot,env=environment,capture_output=True,
                                     timeout=900 if 'engine_clusters' in name else 240)
            (receipts/(name+'.log')).write_bytes(completed.stdout+completed.stderr)
            result['checks'].append({'name':name,'exit':completed.returncode})
            (receipts/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
            print(f'{name}: {completed.returncode}',flush=True)
            if completed.returncode: return 1
    print('PASS: exact staged tree '+tree)
    return 0
if __name__=='__main__': raise SystemExit(main())
