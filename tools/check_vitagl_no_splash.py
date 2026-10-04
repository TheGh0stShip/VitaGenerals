#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reject vitaGL archives that retain the asynchronous splash renderer."""

import argparse
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vita-sdk', required=True, type=Path)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve()
    nm = args.vita_sdk.resolve() / 'bin/arm-vita-eabi-nm'
    if not archive.is_file() or not nm.is_file():
        parser.error('archive and Vita SDK nm must exist')

    symbols = subprocess.check_output(
        [str(nm), '-a', str(archive)], text=True, errors='replace')
    forbidden_symbols = (
        'invoke_splashscreen',
        'clear_splashscreen',
        'splashscreen_thread',
        'is_splashscreen_active',
    )
    found_symbols = [name for name in forbidden_symbols if name in symbols]
    forbidden_markers = (
        b'vitaGL Splashscreen',
        b'Splashscreen Sema Push',
        b'Splashscreen Sema Pull',
    )
    data = archive.read_bytes()
    found_markers = [value.decode('ascii') for value in forbidden_markers
                     if value in data]
    if found_symbols or found_markers:
        raise SystemExit('vitaGL splash renderer present: ' +
                         ', '.join(found_symbols + found_markers))
    print('PASS: vitaGL splash renderer is absent')


if __name__ == '__main__':
    main()

