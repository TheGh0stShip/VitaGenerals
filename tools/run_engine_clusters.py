#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reproduce original engine dependency cluster builds and retain their evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['host','vita'],required=True)
    parser.add_argument('--build-dir',type=Path,required=True)
    parser.add_argument('--vita-sdk',type=Path)
    parser.add_argument('--source',type=Path,help='Pristine pinned GeneralsMD/Code directory')
    parser.add_argument('--iconv-archive',type=Path,help='Optional hash-checked release archive')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    output=args.build_dir.resolve()
    if not output.is_relative_to(root) or not output.relative_to(root).parts[0].startswith('build-'):
        parser.error('build directory must remain in an ignored build-*/ tree')
    requested=args.build_dir.absolute()
    if output.exists() or any(p.is_symlink() for p in [requested,*requested.parents]):
        parser.error('choose a fresh build directory without symlink parents')
    if args.mode=='vita' and not args.vita_sdk:
        parser.error('Vita builds require an explicit SDK')
    output.mkdir(parents=True)
    environment=os.environ.copy();environment.pop('CMAKE_TOOLCHAIN_FILE',None)
    sdk=args.vita_sdk.resolve() if args.vita_sdk else None
    if sdk:environment['VITASDK']=str(sdk)
    receipt={'schema':1,'mode':args.mode,'checks':[],
             'engine_startup_verified':False,'hardware_verified':False}
    def run(name,command):
        with (output/(name+'.log')).open('w') as log:
            result=subprocess.run(command,cwd=root,env=environment,stdout=log,stderr=subprocess.STDOUT)
        receipt['checks'].append({'name':name,'command':command,'exit':result.returncode})
        (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(f'{name}: {result.returncode}',flush=True)
        if result.returncode:raise RuntimeError(f'{name} failed; inspect retained log')
    python=sys.executable
    source=args.source.resolve() if args.source else output/'source/GeneralsMD/Code'
    if not args.source:
        run('source',[python,'tools/fetch_source_baseline.py','--directory',str(output/'source')])
    run('stage',[python,'tools/stage_engine_tree.py','--source',str(source),'--output',str(output/'staged')])
    codec=[python,'tools/build_libiconv.py','--mode',args.mode,'--output',str(output/'iconv')]
    if sdk:codec+=['--vita-sdk',str(sdk)]
    if args.iconv_archive:codec+=['--archive',str(args.iconv_archive.resolve())]
    run('iconv',codec)
    configure=['cmake','-S','engine','-B',str(output/'cmake'),
               '-DCMAKE_BUILD_TYPE=Release','-DGENERALS_STAGED_CODE='+str(output/'staged/Code'),
               '-DGENERALS_MEMORY_POOL_CONFIG_PATH=Data/INI/MemoryPools.ini',
               '-DGENERALS_ICONV_PREFIX='+str(output/'iconv')]
    if args.mode=='vita':configure+=['-DCMAKE_TOOLCHAIN_FILE='+str(sdk/'share/vita.toolchain.cmake')]
    run('configure',configure)
    run('build',['cmake','--build',str(output/'cmake'),'--parallel','2'])
    cache=(output/'cmake/CMakeCache.txt').read_text().splitlines()
    compiler=next(line.split('=',1)[1] for line in cache if line.startswith('CMAKE_CXX_COMPILER:'))
    receipt['compiler']={'path':compiler,
                         'version':subprocess.check_output([compiler,'--version'],text=True,env=environment),
                         'target':subprocess.check_output([compiler,'-dumpmachine'],text=True,env=environment).strip()}
    if args.mode=='vita':
        for name in ('allocator_alignment','ascii_allocator','wwmath_link_entry'):
            executable=str(output/'cmake'/name)
            run(name+'-symbols',[str(sdk/'bin/arm-vita-eabi-nm'),'--defined-only',executable])
            run(name+'-attributes',[str(sdk/'bin/arm-vita-eabi-readelf'),'-h','-A',executable])
    if args.mode=='host':run('tests',['ctest','--test-dir',str(output/'cmake'),'--output-on-failure'])
    artifacts=[p for p in (output/'cmake').iterdir() if p.is_file() and
               (p.suffix in ('.a','.map') or p.name in ('allocator_alignment','ascii_allocator','wwmath_link_entry',
                                                       'rawfile_probe','factory_probe','chunk-file_probe'))]
    receipt['artifacts']=[{'path':p.relative_to(output).as_posix(),
                          'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(artifacts)]
    receipt['stage_receipt_sha256']=hashlib.sha256((output/'staged/receipt.json').read_bytes()).hexdigest()
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
