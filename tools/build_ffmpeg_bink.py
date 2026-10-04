#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the pinned Vita libraries needed for retail Bink playback."""
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
    if output.exists() or any(p.is_symlink() for p in [args.output, *args.output.parents]):
        parser.error('choose a fresh output directory without symlink parents')
    if args.jobs < 1:
        parser.error('jobs must be positive')
    sdk = args.vita_sdk.resolve()
    compiler = sdk / 'bin/arm-vita-eabi-gcc'
    if subprocess.check_output([str(compiler), '-dumpmachine'], text=True).strip() != 'arm-vita-eabi':
        parser.error('unexpected target compiler')
    lock = json.loads((root / 'tools/ffmpeg-bink-lock.json').read_text())
    output.mkdir(parents=True)
    archive = output / ('ffmpeg-' + lock['version'] + '.tar.xz')
    if args.archive:
        shutil.copyfile(args.archive.resolve(), archive)
    else:
        with urllib.request.urlopen(lock['url'], timeout=60) as source, archive.open('wb') as target:
            shutil.copyfileobj(source, target)
    if sha(archive) != lock['sha256']:
        raise ValueError('release checksum mismatch; source was not executed')
    source_root = output / 'source'
    with tarfile.open(archive) as package:
        package.extractall(source_root, filter='data')
    source = source_root / ('ffmpeg-' + lock['version'])
    build = output / 'build'
    install = output / 'install'
    build.mkdir()
    environment = os.environ.copy()
    for key in ('CC', 'CXX', 'AR', 'RANLIB', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS',
                'LIBS', 'CONFIG_SITE', 'CMAKE_TOOLCHAIN_FILE'):
        environment.pop(key, None)
    environment['LC_ALL'] = 'C'
    environment['VITASDK'] = str(sdk)
    environment['PATH'] = str(sdk / 'bin') + os.pathsep + environment['PATH']
    common_flags = ('-std=gnu11 -mcpu=cortex-a9 -mthumb -mfpu=neon '
                    '-mfloat-abi=hard -O2 -ffunction-sections -fdata-sections '
                    '-fomit-frame-pointer -D_BSD_SOURCE')
    configure = [str(source / 'configure'), '--prefix=' + str(install),
        '--enable-cross-compile', '--cross-prefix=' + str(sdk / 'bin/arm-vita-eabi-'),
        '--arch=armv7-a', '--cpu=cortex-a9', '--target-os=none', '--disable-shared',
        '--enable-static', '--disable-programs', '--disable-doc', '--disable-avdevice',
        '--disable-avfilter', '--disable-network', '--disable-autodetect',
        '--disable-runtime-cpudetect', '--disable-armv5te', '--disable-armv6t2',
        '--disable-everything', '--enable-avformat', '--enable-avcodec',
        '--enable-avutil', '--enable-swscale', '--enable-swresample',
        '--enable-demuxer=bink', '--enable-decoder=bink,binkaudio_dct,binkaudio_rdft',
        '--enable-protocol=file', '--enable-pthreads', '--disable-small',
        '--disable-debug', '--disable-bzlib', '--disable-iconv', '--disable-lzma',
        '--disable-sdl2', '--disable-securetransport', '--disable-xlib',
        '--extra-cflags=' + common_flags,
        '--extra-ldflags=-L{} -Wl,--gc-sections'.format(sdk / 'arm-vita-eabi/lib')]
    receipt = {'schema': 1, 'source': lock, 'target': 'arm-vita-eabi',
               'configure': configure[1:], 'checks': [], 'hardware_verified': False,
               'retail_content_included': False}

    def run(name, command, cwd):
        with (output / (name + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=cwd, env=environment,
                                    stdout=log, stderr=subprocess.STDOUT)
        receipt['checks'].append({'name': name, 'command': command, 'exit': result.returncode})
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(name + ': ' + str(result.returncode), flush=True)
        if result.returncode:
            raise RuntimeError(name + ' failed; inspect retained log')

    run('configure', configure, build)
    run('build', ['make', '--jobs=' + str(args.jobs)], build)
    run('install', ['make', 'install'], build)
    names = ('libavformat.a', 'libavcodec.a', 'libswscale.a',
             'libswresample.a', 'libavutil.a')
    artifacts = [install / 'lib' / name for name in names]
    if not all(path.is_file() for path in artifacts):
        raise RuntimeError('expected static library is missing')
    run('member_abi', ['python3', str(root / 'tools/check_ffmpeg_vita_abi.py'),
                       '--vita-sdk', str(sdk), *map(str, artifacts)], root)
    licenses = output / 'licenses'
    licenses.mkdir()
    for name in ('LICENSE.md', 'COPYING.LGPLv2.1'):
        shutil.copyfile(source / name, licenses / name)
    receipt['compiler'] = subprocess.check_output([str(compiler), '--version'], text=True)
    receipt['artifacts'] = [{'path': str(path.relative_to(output)), 'sha256': sha(path)}
                            for path in artifacts]
    receipt['licenses'] = [{'path': str(path.relative_to(output)), 'sha256': sha(path)}
                           for path in licenses.iterdir()]
    receipt['source_retained'] = True
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('PASS: Bink decode libraries built; playback and hardware remain separate gates')


if __name__ == '__main__':
    main()
