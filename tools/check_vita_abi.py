#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check target ELF attributes. Supply every selected dependency archive/object."""
import os
from pathlib import Path
import subprocess
import sys
sdk = Path(os.environ.get('VITASDK', '/usr/local/vitasdk'))
readelf = sdk / 'bin/arm-vita-eabi-readelf'
if len(sys.argv) < 2:
    sys.exit('usage: check_vita_abi.py OBJECT_OR_ARCHIVE [...]')
for filename in sys.argv[1:]:
    result = subprocess.run([str(readelf), '-h', '-A', filename], capture_output=True, text=True, check=True)
    sections = result.stdout.split('File:') if 'File:' in result.stdout else [result.stdout]
    verified = neutral = 0
    for section in sections:
        if not section.strip():
            continue
        if 'Machine:' not in section:
            continue
        if 'Machine:                           ARM' not in section or 'ELF32' not in section or 'little endian' not in section:
            sys.exit('FAIL: non-ELF32 little-endian ARM member')
        for line in section.splitlines():
            if 'Tag_ABI_VFP_args:' in line and 'VFP registers' not in line:
                sys.exit('FAIL: incompatible floating-point argument ABI')
            if 'Tag_CPU_arch:' in line and line.split(':', 1)[1].strip() != 'v7':
                sys.exit('FAIL: unexpected ARM architecture')
        if 'Tag_ABI_VFP_args: VFP registers' in section:
            verified += 1
        else:
            neutral += 1
    if not verified:
        sys.exit('FAIL: no hard-float attribute evidence')
    # Missing attributes are not proof of compatibility; prohibit silent approval.
    if neutral:
        sys.exit(f'FAIL: {neutral} members lack float ABI evidence; review individually')
    print(f'PASS: {verified} ARM members with hard-float attributes')
print('ELF inspection only; no hardware validation')
