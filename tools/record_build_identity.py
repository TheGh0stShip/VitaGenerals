#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Retain matching build source/patch, ELF/map/symbol identity; no device access."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-dir',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[1];build=a.build_dir.resolve()
    if not build.is_relative_to(root) or not build.relative_to(root).parts[0].startswith('build-'):
        p.error('identity output must remain under ignored build-*/')
    sdk=Path(os.environ['VITASDK']);prefix=sdk/'bin/arm-vita-eabi-'
    def tool(name,*args): return subprocess.check_output([str(prefix)+name,*map(str,args)],text=True)
    probes=['original_crc_probe','big_header_test','original_math_validity_probe']
    artifact_names=['compile_commands.json']
    maptext=''
    for probe in probes:
        elf=build/probe
        (build/(probe+'.attributes.txt')).write_text(tool('readelf','-h','-A',elf))
        (build/(probe+'.symbols.txt')).write_text(tool('nm','-C','--defined-only',elf))
        maptext += (build/(probe+'.map')).read_text()+'\n'
        artifact_names += [probe,probe+'.map',probe+'.symbols.txt',probe+'.attributes.txt']
    libraries=[]
    for name in sorted(set(re.findall(r'^LOAD (.*\.a)$',maptext,re.M))):
        path=Path(name)
        if not path.is_absolute(): path=build/path
        if not path.is_file(): raise ValueError('link-map library input missing')
        attributes=tool('readelf','-A',path)
        # Missing attributes remain evidence gaps, including hand-written SDK veneers.
        members=attributes.count('File:')
        hard=attributes.count('Tag_ABI_VFP_args: VFP registers')
        libraries.append({'name':path.name,'sha256':sha(path),'archive_members':members,
                          'members_with_hard_float_attributes':hard,
                          'members_without_hard_float_evidence':members-hard,
                          'abi_status':'attributes_verified' if members and members==hard else 'individual_review_required'})
    compiled=[]
    database=json.loads((build/'compile_commands.json').read_text())
    for row in database:
        source=(Path(row['directory'])/row['file']).resolve()
        if not source.is_file(): raise ValueError('compiled source missing')
        label=source.relative_to(root).as_posix() if source.is_relative_to(root) else source.name
        compiled.append({'source':label,'sha256':sha(source)})
    sources=json.loads((root/'vendor/ea/manifest.json').read_text())
    for row in sources['files']:
        if sha(root/'vendor/ea'/row['path'])!=row['sha256'] or sha(build/'staged'/row['path'])!=row['staged_sha256']:
            raise ValueError('source identity does not match manifest')
    result={'schema':1,'evidence_class':'ARM_compile_link_only','hardware_verified':False,
            'compiler':tool('gcc','--version').splitlines()[0],'target':tool('gcc','-dumpmachine').strip(),
            'source_manifest_sha256':sha(root/'vendor/ea/manifest.json'),
            'staging_receipt_sha256':sha(build/'staged/receipt.json'),
            'artifacts':[{'name':name,'sha256':sha(build/name)} for name in
                         artifact_names],
            'compiled_sources':compiled,'linked_libraries':libraries,'package_manifest':{'status':'not_produced','reason':'linked boundary probes are not a game launcher or VPK'}}
    (build/'artifact-identity.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"PASS: {len(result['artifacts'])} matching ARM artifacts retained; library review gaps remain explicit")
if __name__=='__main__': main()
