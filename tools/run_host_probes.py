#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run reproducible retail-free host tests with bounded processes and receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

def run(command,root,log,timeout,environment):
    begin=time.monotonic()
    with log.open('wb') as stream:
        process=subprocess.Popen(command,cwd=root,stdout=stream,stderr=subprocess.STDOUT,
                                 env=environment,start_new_session=True)
        try: code=process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait();code='timeout'
    return {'exit':code,'seconds':round(time.monotonic()-begin,3),'log':log.name,
            'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-dir',type=Path,required=True)
    p.add_argument('--sanitizer',choices=['none','asan-ubsan'],default='asan-ubsan')
    p.add_argument('--timeout',type=int,default=120)
    a=p.parse_args();root=Path(__file__).resolve().parents[1];build=a.build_dir.resolve()
    if a.timeout<1: p.error('timeout must be positive')
    if not (build.is_relative_to(root/'build') or (build.is_relative_to(root) and build.relative_to(root).parts[0].startswith('build-'))):
        p.error('receipt and logs must stay in ignored build trees')
    build.mkdir(parents=True,exist_ok=True);logs=build/'probe-logs';logs.mkdir(exist_ok=True)
    env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
    summary={'schema':1,'evidence_class':'host_only','sanitizer':a.sanitizer,'steps':[],
             'runtime_hardware_verified':False}
    compiler=env.get('CXX','c++')
    summary['compiler_identity']=subprocess.check_output([compiler,'--version'],text=True).splitlines()[0]
    steps=[('configure',['cmake','-S',str(root),'-B',str(build),'-DCMAKE_BUILD_TYPE=Debug',
                        '-DVG_HOST_SANITIZERS='+('ON' if a.sanitizer=='asan-ubsan' else 'OFF')]),
           ('build',['cmake','--build',str(build),'--parallel','2']),
           ('cxx_probes',['ctest','--test-dir',str(build),'--output-on-failure']),
           ('python_contracts',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py'])]
    for name,command in steps:
        result=run(command,root,logs/(name+'.log'),a.timeout,env)
        summary['steps'].append(dict(result,name=name))
        (build/'host-probe-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(f'{name}: {result["exit"]}',flush=True)
        if result['exit']!=0: return 1
    summary['test_denominator']=len(json.loads(subprocess.check_output(['ctest','--test-dir',str(build),'--show-only=json-v1'],text=True))['tests'])
    summary['artifacts']=[{'name':name,'sha256':hashlib.sha256((build/name).read_bytes()).hexdigest()}
                          for name in ['original_crc_probe','big_header_test','compile_commands.json','staged/receipt.json']]
    (build/'host-probe-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return 0
if __name__=='__main__': raise SystemExit(main())
