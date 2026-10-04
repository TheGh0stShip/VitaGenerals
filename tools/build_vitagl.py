#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the pinned Vita graphics dependency for the original W3D boundary."""
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
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--vita-sdk', required=True, type=Path)
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
    if output.exists() or any(path.is_symlink() for path in [args.output, *args.output.parents]):
        parser.error('choose a fresh output directory without symlink parents')
    if args.jobs < 1:
        parser.error('jobs must be positive')

    lock = json.loads((root / 'tools/vitagl-lock.json').read_text())
    sdk = args.vita_sdk.resolve()
    compiler = sdk / 'bin/arm-vita-eabi-gcc'
    archiver = sdk / 'bin/arm-vita-eabi-ar'
    if subprocess.check_output([str(compiler), '-dumpmachine'], text=True).strip() != 'arm-vita-eabi':
        parser.error('unexpected target compiler')
    required = ('libvitashark.a', 'libSceShaccCgExt.a', 'libSceShaccCg_stub.a')
    for name in required:
        if not (sdk / 'arm-vita-eabi/lib' / name).is_file():
            parser.error('Vita SDK is missing ' + name)

    output.mkdir(parents=True)
    archive = output / ('vitagl-' + lock['revision'] + '.tar.gz')
    if args.archive:
        shutil.copyfile(args.archive.resolve(), archive)
    else:
        with urllib.request.urlopen(lock['url'], timeout=60) as source, archive.open('wb') as target:
            shutil.copyfileobj(source, target)
    if sha(archive) != lock['sha256']:
        raise ValueError('source checksum mismatch; source was not executed')

    source = output / 'source'
    source.mkdir()
    with tarfile.open(archive) as package:
        package.extractall(source, filter='data')
    children = [path for path in source.iterdir() if path.is_dir()]
    if len(children) != 1:
        raise RuntimeError('unexpected source archive layout')
    source = children[0]
    receipt = {'schema': 1, 'source': lock, 'target': 'arm-vita-eabi',
               'checks': [], 'hardware_verified': False,
               'retail_content_included': False}
    environment = os.environ.copy()
    for key in ('CC', 'CXX', 'AR', 'RANLIB', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS',
                'LIBS', 'CONFIG_SITE', 'CMAKE_TOOLCHAIN_FILE'):
        environment.pop(key, None)
    environment['LC_ALL'] = 'C'
    environment['VITASDK'] = str(sdk)
    environment['PATH'] = str(sdk / 'bin') + os.pathsep + environment['PATH']

    def run(name, command, cwd):
        with (output / (name + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=cwd, env=environment,
                                    stdout=log, stderr=subprocess.STDOUT)
        receipt['checks'].append({'name': name, 'command': command, 'exit': result.returncode})
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(name + ': ' + str(result.returncode), flush=True)
        if result.returncode:
            raise RuntimeError(name + ' failed; inspect retained log')

    for index, relative in enumerate(lock['patches']):
        patch = root / relative
        if not patch.is_file():
            raise RuntimeError('missing dependency patch: ' + relative)
        run('patch_{:02d}'.format(index + 1),
            ['patch', '--batch', '--fuzz=0', '--no-backup-if-mismatch',
             '-p1', '-i', str(patch)], source)
    for relative, expected in lock['patched_files'].items():
        if sha(source / relative) != expected:
            raise RuntimeError('patched dependency source differs: ' + relative)

    flags = ('-O3 -g0 -mcpu=cortex-a9 -mthumb -mfpu=neon -mfloat-abi=hard '
             '-mfp16-format=ieee -ffunction-sections -fdata-sections '
             '-Wno-incompatible-pointer-types -Wno-stringop-overflow '
             '-DVGL_GIT_HASH=\\"{}\\" -Isource -DSKIP_ERROR_HANDLING '
             '-DSKIP_SPLASHSCREEN -DHAVE_SHADER_CACHE -DHAVE_VITA3K_SUPPORT '
             '-DDISABLE_HW_ETC1').format(lock['revision'][:7])
    run('build', ['make', '-B', '--jobs=' + str(args.jobs), 'CFLAGS=' + flags], source)
    library = source / 'libvitaGL.a'
    header = source / 'source/vitaGL.h'
    if not library.is_file() or not header.is_file():
        raise RuntimeError('expected vitaGL artifacts are missing')
    members = subprocess.check_output([str(archiver), 't', str(library)], text=True).splitlines()
    if (not members or len(members) != len(set(members)) or
            any(not name or '/' in name or name in ('.', '..') for name in members)):
        raise RuntimeError('unsafe or ambiguous archive member list')
    normalize = output / 'normalize'
    normalize.mkdir()
    run('normalize_extract', [str(archiver), 'x', str(library.resolve())], normalize)
    normalized = output / 'libvitaGL.normalized.a'
    run('normalize_archive', [str(archiver), 'rcD', str(normalized), *members], normalize)
    run('normalize_index', [str(archiver), 'sD', str(normalized)], normalize)
    os.replace(normalized, library)
    shutil.rmtree(normalize)
    run('member_abi', ['python3', str(root / 'tools/check_ffmpeg_vita_abi.py'),
                       '--vita-sdk', str(sdk), '--label', 'vitaGL', str(library)], root)
    run('no_splash', ['python3', str(root / 'tools/check_vitagl_no_splash.py'),
                      '--vita-sdk', str(sdk), str(library)], root)

    install = output / 'install'
    (install / 'lib').mkdir(parents=True)
    (install / 'include').mkdir()
    shutil.copyfile(library, install / 'lib/libvitaGL.a')
    shutil.copyfile(header, install / 'include/vitaGL.h')
    licenses = output / 'licenses'
    licenses.mkdir()
    for name in ('COPYING', 'COPYING.LESSER'):
        shutil.copyfile(source / name, licenses / name)
    artifacts = (install / 'lib/libvitaGL.a', install / 'include/vitaGL.h')
    receipt['compiler'] = subprocess.check_output([str(compiler), '--version'], text=True)
    receipt['flags'] = flags
    receipt['artifacts'] = [{'path': str(path.relative_to(output)), 'sha256': sha(path)}
                            for path in artifacts]
    receipt['licenses'] = [{'path': str(path.relative_to(output)), 'sha256': sha(path)}
                           for path in sorted(licenses.iterdir())]
    receipt['source_retained'] = True
    receipt['splash_renderer'] = 'disabled-and-archive-verified'
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('PASS: Vita graphics dependency built; renderer and hardware remain separate gates')


if __name__ == '__main__':
    main()
