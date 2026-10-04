#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build pinned conversion libraries; retain source, licenses and artifact identity."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=('host', 'vita'), required=True)
    parser.add_argument('--vita-sdk', type=Path)
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if not output.is_relative_to(root):
        parser.error('output must be inside the project')
    parts = output.relative_to(root).parts
    if not parts or not (parts[0] == 'build' or parts[0].startswith('build-')):
        parser.error('output must be in a build tree')
    if output.exists() or any(p.is_symlink() for p in [args.output, *args.output.parents]):
        parser.error('choose a fresh output directory without symlink parents')
    if args.jobs < 1:
        parser.error('jobs must be positive')
    lock = json.loads((root / 'tools/libiconv-lock.json').read_text())
    environment = os.environ.copy()
    for key in ('CC', 'CXX', 'AR', 'RANLIB', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS', 'LIBS', 'CONFIG_SITE'):
        environment.pop(key, None)
    environment['CONFIG_SITE'] = '/dev/null'
    environment['LC_ALL'] = 'C'
    configure_flags = ['--disable-shared', '--enable-static', '--disable-nls']
    if args.mode == 'vita':
        if not args.vita_sdk:
            parser.error('Vita mode requires --vita-sdk')
        sdk = args.vita_sdk.resolve()
        compiler = sdk / 'bin/arm-vita-eabi-gcc'
        target = subprocess.check_output([str(compiler), '-dumpmachine'], text=True).strip()
        if target != 'arm-vita-eabi':
            parser.error('unexpected target compiler')
        environment.update(CC=str(compiler), AR=str(sdk / 'bin/arm-vita-eabi-ar'),
                           RANLIB=str(sdk / 'bin/arm-vita-eabi-ranlib'), VITASDK=str(sdk))
        environment['PATH'] = str(sdk / 'bin') + os.pathsep + environment['PATH']
        environment['CFLAGS'] = '-O2 -mcpu=cortex-a9 -mthumb -mfpu=neon -mfloat-abi=hard -D__DYNAMIC_REENT__'
        configure_flags += ['--host=arm-vita-eabi', '--build=' + subprocess.check_output(
            ['gcc', '-dumpmachine'], text=True).strip()]
    else:
        compiler = Path(shutil.which('gcc') or 'gcc')
        environment.update(CC=str(compiler), CFLAGS='-O2')
        environment.pop('VITASDK', None)
    output.mkdir(parents=True)
    archive = output / ('libiconv-' + lock['version'] + '.tar.gz')
    if args.archive:
        shutil.copyfile(args.archive, archive)
    else:
        with urllib.request.urlopen(lock['url'], timeout=60) as source, archive.open('wb') as dest:
            shutil.copyfileobj(source, dest)
    if sha(archive) != lock['sha256']:
        raise ValueError('release checksum mismatch; source was not executed')
    source_dir = output / 'source'
    with tarfile.open(archive) as package:
        package.extractall(source_dir, filter='data')
    source = source_dir / ('libiconv-' + lock['version'])
    build = output / 'library'
    build.mkdir()
    receipt = {'schema': 1, 'source': lock, 'mode': args.mode, 'checks': [],
               'compiler': subprocess.check_output([str(compiler), '--version'], text=True),
               'cflags': environment['CFLAGS'], 'hardware_verified': False}

    def run(name, command, cwd):
        with (output / (name + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=cwd, env=environment,
                                    stdout=log, stderr=subprocess.STDOUT)
        receipt['checks'].append({'name': name, 'command': command, 'exit': result.returncode})
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(name + ': ' + str(result.returncode), flush=True)
        if result.returncode:
            raise RuntimeError(name + ' failed; inspect its build log')

    run('configure', [str(source / 'configure'), *configure_flags,
                      '--prefix=' + str(output / 'install')], build)
    run('charset_headers', ['make', 'lib/localcharset.h'], build)
    flags = [] if args.mode == 'vita' else ['CFLAGS=-O1 -fsanitize=address,undefined -fno-omit-frame-pointer']
    run('libraries', ['make', '--jobs=' + str(args.jobs), *flags], build / 'lib')
    artifacts = [build / 'lib/.libs/libiconv.a', build / 'libcharset/lib/.libs/libcharset.a']
    if args.mode == 'vita':
        run('member_abi', ['python3', str(root / 'tools/check_vita_abi.py'),
                           *map(str, artifacts)], root)
    licenses = output / 'licenses'
    licenses.mkdir()
    shutil.copyfile(source / 'COPYING.LIB', licenses / 'libiconv-LGPL-2.1.txt')
    shutil.copyfile(source / 'libcharset/COPYING.LIB', licenses / 'libcharset-LGPL-2.1.txt')
    receipt['artifacts'] = [{'path': str(p.relative_to(output)), 'sha256': sha(p)} for p in artifacts]
    receipt['licenses'] = [{'path': str(p.relative_to(output)), 'sha256': sha(p)} for p in licenses.iterdir()]
    receipt['source_retained'] = True
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('PASS: conversion libraries built; runtime behavior and hardware remain separate gates')


if __name__ == '__main__':
    main()
