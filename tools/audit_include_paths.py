#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Inventory literal include spellings without guessing compiler search paths."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
from audit_module_registrations import TOKEN, mask

EXTENSIONS = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.inl'}

def scan(text):
    # Splice physical lines before masking, preserving their original start lines.
    logical = []
    lines = []
    physical = 1
    cursor = 0
    for match in re.finditer(r'\\\r?\n', text):
        chunk = text[cursor:match.start()]
        logical.append(chunk)
        for char in chunk:
            lines.append(physical)
            physical += char == '\n'
        physical += 1
        cursor = match.end()
    chunk = text[cursor:]
    logical.append(chunk)
    for char in chunk:
        lines.append(physical)
        physical += char == '\n'
    original = ''.join(logical)
    clean = mask(original)
    operands = TOKEN.sub(lambda m: "".join("\n" if c == "\n" else " " for c in m[0])
                         if m[0].startswith("/") else m[0], original)
    rows = []
    for directive in re.finditer(r'^[^\S\n]*#[^\S\n]*include\b', clean, re.M):
        start = directive.end()
        end = original.find('\n', start)
        if end < 0:
            end = len(original)
        operand = operands[start:end].strip()
        quoted = re.fullmatch(r'"([^"\n]+)"', operand)
        angled = re.fullmatch(r'<([^>\n]+)>', operand)
        match = quoted or angled
        hash_position = clean.find('#', directive.start(), directive.end())
        rows.append({'line': lines[hash_position],
                     'kind': 'quoted' if quoted else 'angled' if angled else 'computed_or_unsupported',
                     'operand': match[1] if match else operand})
    return rows

def indices(names):
    relative = defaultdict(list)
    suffix = defaultdict(list)
    for name in sorted(names):
        relative[name.casefold()].append(name)
        parts = name.split("/")
        for offset in range(len(parts)):
            suffix["/".join(parts[offset:]).casefold()].append(name)
    return relative, suffix

def resolve(source, operand, names, lookup=None):
    normalized = operand.replace('\\', '/')
    relative = posixpath.normpath(str(PurePosixPath(source).parent / normalized))
    relative_index, suffix_index = lookup if lookup is not None else indices(names)
    relative_candidates = relative_index.get(relative.casefold(), [])
    suffix = posixpath.normpath(normalized)
    candidates = suffix_index.get(suffix.casefold(), []) if not suffix.startswith(('../', '/')) else []
    return {'normalized_operand': normalized, 'backslash_spelling': '\\' in operand,
            'relative_path': relative, 'relative_exact': relative in names,
            'relative_case_candidates': relative_candidates,
            'search_root_candidates': candidates,
            'search_root_ambiguous': len(candidates) > 1,
            'candidate_path_rules': 'Windows separator normalization and casefold lookup; not POSIX compiler resolution',
            'selected_header': None, 'configuration_reachability': 'unknown'}

def inventory(root):
    files = sorted(p for p in root.rglob('*') if p.is_file())
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('symlinks in source tree')
    hashes = [[p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()] for p in files]
    tree = hashlib.sha256(json.dumps(hashes, separators=(',', ':')).encode()).hexdigest()
    lock = json.loads((Path(__file__).parent / 'source-lock.json').read_text())
    if tree != lock['tree_sha256']:
        raise ValueError('source tree differs from pinned baseline')
    names = {n for n, _ in hashes}
    lookup = indices(names)
    rows = []
    scanned = 0
    for p, (name, digest) in zip(files, hashes):
        if p.suffix.lower() not in EXTENSIONS:
            continue
        scanned += 1
        for row in scan(p.read_text(encoding='latin1')):
            row.update(path=name, source_sha256=digest)
            if row['kind'] != 'computed_or_unsupported':
                row.update(resolve(name, row['operand'], names, lookup))
            rows.append(row)
    collisions = defaultdict(list)
    for name in sorted(names):
        collisions[name.casefold()].append(name)
    return {'schema': 1, 'complete': False, 'upstream_commit': lock['upstream_commit'],
            'source_tree_sha256': tree,
            'scope': 'Unpreprocessed literal include spellings across original C/C++ sources and headers',
            'summary': {'files_scanned': scanned, 'include_sites': len(rows),
                        'kinds': dict(sorted(Counter(r['kind'] for r in rows).items())),
                        'backslash_sites': sum(r.get('backslash_spelling', False) for r in rows),
                        'relative_case_mismatch_sites': sum(not r.get('relative_exact', False) and bool(r.get('relative_case_candidates')) for r in rows),
                        'ambiguous_search_root_sites': sum(len(r.get('search_root_candidates', [])) > 1 for r in rows)},
            'case_collisions': [v for v in collisions.values() if len(v) > 1], 'rows': rows,
            'unknowns': ['Original configuration and compiler include search order; candidates are not selected headers',
                         'Macro-expanded operands, raw strings, compiler extensions and preprocessing reachability',
                         'SDK/system/generated headers outside the pinned Code tree',
                         'Transitive compile/link compatibility and physical Vita/PSTV behavior']}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.source)
    data = (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gzip.compress(data, mtime=0) if args.output.suffix == '.gz' else data)
    print(json.dumps(result['summary'], sort_keys=True))
if __name__ == '__main__':
    main()
