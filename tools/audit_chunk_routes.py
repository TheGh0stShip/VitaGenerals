#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Inventory named chunk registration/read candidates across pinned source."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
from audit_system_ownership import analyze
from audit_source_structure import parser, VERSIONS

ROUTES = frozenset({'registerParser', 'openDataChunk', 'closeDataChunk',
                    'readDict', 'readAsciiString', 'readUnicodeString'})

def inventory(root):
    paths = sorted(root.rglob('*'))
    if any(p.is_symlink() for p in paths):
        raise ValueError('symlink source input')
    inputs = [(p, p.read_bytes()) for p in paths if p.is_file()]
    hashes = [[p.relative_to(root).as_posix(), hashlib.sha256(data).hexdigest()]
              for p, data in inputs]
    tree = hashlib.sha256(json.dumps(hashes, separators=(',', ':')).encode()).hexdigest()
    lock = json.loads((Path(__file__).parent / 'source-lock.json').read_text())
    if tree != lock['tree_sha256']:
        raise ValueError('source differs from pinned baseline')
    engine = parser()
    calls, recoveries = [], []
    scanned = 0
    for (path, data), (name, digest) in zip(inputs, hashes):
        if path.suffix.lower() not in {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.inl'}:
            continue
        scanned += 1
        _, found, errors = analyze(data, engine, ROUTES)
        calls.extend(dict(row, path=name, source_sha256=digest) for row in found)
        recoveries.extend(dict(row, path=name) for row in errors)
    return {'schema': 1, 'complete': False,
            'scope': 'Unpreprocessed named chunk registration and read call candidates; no receiver binding or asset-loader completeness claim',
            'upstream_commit': lock['upstream_commit'], 'source_tree_sha256': tree,
            'parser_versions': VERSIONS,
            'parser_requirements_sha256': hashlib.sha256((Path(__file__).parent / 'parser-requirements.txt').read_bytes()).hexdigest(),
            'summary': {'files_scanned': scanned, 'route_sites': len(calls),
                        'routes': dict(sorted(Counter(r['route'] for r in calls).items())),
                        'calls_with_own_parse_error': sum(r['parse_has_error'] for r in calls),
                        'parse_recoveries': len(recoveries)},
            'calls': calls, 'parse_recoveries': recoveries,
            'unknowns': ['Call receiver, overload and preprocessing reachability unresolved',
                         'Dynamic parent labels and registration ordering need callback-specific analysis',
                         'Named read methods do not enumerate every asset loader',
                         'Parser recovery can omit calls; raw arguments and errors retained',
                         'Retail nested references, mount precedence and runtime ownership incomplete',
                         'Full engine build and physical Vita/PSTV correctness unproven']}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = inventory(args.source)
    data = (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gzip.compress(data, mtime=0) if args.output.suffix == '.gz' else data)
    print(json.dumps(result['summary'], sort_keys=True))
if __name__ == '__main__':
    main()
