#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check every object in the selected Vita FFmpeg static archives."""
import argparse
import os
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archives', nargs='+', type=Path)
    parser.add_argument('--vita-sdk', type=Path)
    args = parser.parse_args()
    sdk = (args.vita_sdk or Path(os.environ.get('VITASDK', '/usr/local/vitasdk'))).resolve()
    readelf = sdk / 'bin/arm-vita-eabi-readelf'
    compatible_arches = {'v4', 'v4T', 'v5T', 'v5TE', 'v5TEJ', 'v6', 'v6K',
                          'v6T2', 'v7'}
    totals = {'members': 0, 'vfp': 0}
    arches = {}
    for archive in args.archives:
        output = subprocess.check_output([str(readelf), '-h', '-A', str(archive)], text=True)
        sections = output.split('File:') if 'File:' in output else [output]
        for section in sections:
            if 'Machine:' not in section:
                continue
            totals['members'] += 1
            if ('Machine:                           ARM' not in section or
                    'ELF32' not in section or 'little endian' not in section):
                raise SystemExit('FAIL: non-ELF32 little-endian ARM member')
            match = re.search(r'Tag_CPU_arch:\s*(\S+)', section)
            if not match or match.group(1) not in compatible_arches:
                raise SystemExit('FAIL: unsupported or missing ARM architecture attribute')
            arches[match.group(1)] = arches.get(match.group(1), 0) + 1
            if 'Tag_ABI_VFP_args: VFP registers' not in section:
                raise SystemExit('FAIL: member lacks hard-float argument ABI evidence')
            totals['vfp'] += 1
    if not totals['members']:
        raise SystemExit('FAIL: no archive members inspected')
    print('PASS: {} FFmpeg ARM members use hard-float; CPU attributes {}'.format(
        totals['members'], ', '.join('{}={}'.format(k, arches[k]) for k in sorted(arches))))
    print('ELF inspection only; no decoder execution or hardware validation')


if __name__ == '__main__':
    main()
