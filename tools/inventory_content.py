#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Static source candidates and retail BIG directory metadata; never runtime proof."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct

EXTENSIONS = {'.w3d', '.dds', '.tga', '.wav', '.mp3', '.bik', '.ini', '.wnd', '.map', '.str', '.csf', '.ani'}
SOURCE = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.inl'}
TOKENS = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def normalized(name):
    return name.replace('\\', '/').casefold()

def big_directory(path):
    rows = []
    with path.open('rb') as stream:
        header = stream.read(16)
        if len(header) != 16 or header[:4] != b'BIGF':
            raise ValueError('unsupported_or_truncated_header')
        size = struct.unpack('<I', header[4:8])[0]
        count, end = struct.unpack('>II', header[8:16])
        if size != path.stat().st_size or not 16 <= end <= size or count > (end-16)//9:
            raise ValueError('invalid_header_bounds')
        digest = hashlib.sha256(header)
        for index in range(count):
            if stream.tell() + 9 > end:
                raise ValueError('truncated_directory')
            raw = stream.read(8)
            digest.update(raw)
            offset, length = struct.unpack('>II', raw)
            name = bytearray()
            while True:
                if stream.tell() >= end:
                    raise ValueError('unterminated_member_name')
                byte = stream.read(1)
                if not byte:
                    raise ValueError('truncated_member_name')
                digest.update(byte)
                if byte == b'\0':
                    break
                name.extend(byte)
                if len(name) > 4096:
                    raise ValueError('member_name_limit_exceeded')
            if not name or (length != 0 and offset < end) or offset > size or length > size-offset:
                raise ValueError('invalid_member_bounds')
            decoded = name.decode('latin1')
            rows.append({'index': index, 'name': decoded, 'normalized': normalized(decoded),
                         'offset_u32': offset, 'size_u32': length,
                         'kind': Path(normalized(decoded)).suffix,
                         'empty_entry_semantics': 'unresolved' if length == 0 else None,
                         'runtime_verified': False})
        # Directory identity includes padding; payload is never read or exported.
        while stream.tell() < end:
            block = stream.read(min(65536, end-stream.tell()))
            if not block:
                raise ValueError('truncated_directory_padding')
            digest.update(block)
        return {'size': size, 'directory_sha256': digest.hexdigest(),
                'payload_hashed': False, 'members': rows}

def source_inventory(root):
    rows, edges, candidates = [], [], []
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        rows.append({'path': relative, 'sha256': sha(data), 'bytes': len(data),
                     'translation_unit': path.suffix.lower() in {'.c','.cpp','.cc','.cxx'},
                     'selected_for_vita': False})
        if path.suffix.lower() not in SOURCE:
            continue
        text = data.decode('latin1')
        mask = list(text)
        for token in TOKENS.finditer(text):
            raw = token[0]
            if raw.startswith('"'):
                value = raw[1:-1].replace('\\\\', '\\')
                suffix = Path(normalized(value)).suffix
                if suffix in EXTENSIONS:
                    edges.append({'source': relative, 'line': text.count('\n',0,token.start())+1,
                                  'literal': value, 'normalized': normalized(value),
                                  'kind': suffix, 'evidence': 'lexical_literal_candidate'})
            for i in range(token.start(), token.end()):
                if mask[i] != '\n':
                    mask[i] = ' '
        clean = ''.join(mask)
        patterns = {
            'function_definition_candidate': r'\b([A-Za-z_]\w*(?:::\w+)*)\s*\([^;{}]*\)\s*(?:const\s*)?\{',
            'pointer_width_candidate': r'\b(?:reinterpret_cast|uintptr_t|intptr_t|DWORD|LONG|size_t)\b',
            'script_dispatch_candidate': r'\b(?:ScriptAction|ScriptCondition|ScriptEngine|register[A-Za-z_]*|DECLARE_[A-Z_]+)\b',
        }
        for kind, expression in patterns.items():
            for match in re.finditer(expression, clean):
                token = match[1] if match.lastindex else match[0]
                if kind == 'function_definition_candidate' and token in {'if','for','while','switch','catch'}:
                    continue
                candidates.append({'source': relative, 'line': text.count('\n',0,match.start())+1,
                                   'token': token, 'kind': kind, 'status': 'unknown'})
    return rows, edges, candidates

def inventory(source, data_roots):
    sources, edges, candidates = source_inventory(source)
    archives, loose, failures = [], [], []
    names = {}
    for root_index, root in enumerate(data_roots):
        for path in sorted(root.rglob('*')):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            identity = {'root_index': root_index, 'path': relative}
            if path.suffix.lower() == '.big':
                try:
                    archive = dict(identity, **big_directory(path))
                    archives.append(archive)
                    for member in archive['members']:
                        names.setdefault(member['normalized'], []).append(dict(identity, index=member['index']))
                except (ValueError, OSError) as error:
                    failures.append(dict(identity, error=str(error)))
            else:
                loose.append(dict(identity, size=path.stat().st_size))
                names.setdefault(normalized(relative), []).append(identity)
    for edge in edges:
        edge['exact_path_candidates'] = names.get(edge['normalized'], [])
        edge['status'] = 'present_candidate' if edge['exact_path_candidates'] else 'unresolved'
    summary = {'source_files': len(sources), 'translation_units': sum(r['translation_unit'] for r in sources),
               'archives': len(archives), 'archive_members': sum(len(a['members']) for a in archives),
               'loose_files': len(loose), 'archive_failures': len(failures), 'source_asset_literals': len(edges),
               'unresolved_literals': sum(e['status']=='unresolved' for e in edges),
               'source_candidate_kinds': dict(Counter(c['kind'] for c in candidates)),
               'member_extensions': dict(sorted(Counter(m['kind'] for a in archives for m in a['members']).items())),
               'names_with_multiple_candidates': sum(len(v)>1 for v in names.values())}
    return {'schema': 1, 'complete': False, 'evidence_class': 'static_metadata_only',
            'summary': summary, 'sources': sources, 'archives': archives, 'loose_files': loose,
            'source_asset_edges': edges, 'source_candidates': candidates, 'failures': failures,
            'open_risks': ['Computed names and IDs', 'Mount order and overrides', 'INI/WND/MAP reference graphs',
                           'Nested W3D/media dependencies', 'C++ parsing and inactive branches',
                           'Actual function/pointer linkage', 'Runtime loaders and physical hardware']}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--data', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    private = Path(__file__).resolve().parents[1] / '.local'
    if not args.output.resolve().is_relative_to(private.resolve()):
        parser.error('detailed receipts must remain under ignored .local/')
    if not args.source.is_dir() or any(not p.is_dir() for p in args.data):
        parser.error('input directory missing')
    result = inventory(args.source, args.data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
    return 1 if result['failures'] else 0
if __name__ == '__main__':
    raise SystemExit(main())
