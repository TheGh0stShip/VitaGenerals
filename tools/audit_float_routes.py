#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Original numeric conversion and rounding call candidates."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
from audit_system_ownership import analyze
from audit_source_structure import parser, VERSIONS

HELPERS = frozenset({'fast_float2long_round', 'fast_float_trunc',
                    'fast_float_floor', 'fast_float_ceil'})
CONTROL = frozenset({'setFPMode', '_controlfp', '_statusfp', '_fpreset'})

def conversion_macros(data, engine):
    """Retain function-like macro bodies mentioning selected helper calls.

    Macro bodies remain unexpanded text; a mention is not a resolved binding.
    """
    tree = engine.parse(data)
    pending, rows = [tree.root_node], []
    pattern = re.compile(rb'\b(?:' + b'|'.join(x.encode() for x in sorted(HELPERS)) + rb')\s*\(')
    while pending:
        node = pending.pop()
        pending.extend(reversed(node.children))
        if node.type != 'preproc_function_def':
            continue
        name = node.child_by_field_name('name')
        value = node.child_by_field_name('value')
        if name is None or value is None:
            continue
        body = data[value.start_byte:value.end_byte]
        if not pattern.search(body):
            continue
        rows.append({'name': data[name.start_byte:name.end_byte].decode('utf8'),
                     'line': node.start_point.row + 1,
                     'raw': data[node.start_byte:node.end_byte].decode('utf8'),
                     'value': body.decode('utf8'), 'parse_has_error': node.has_error,
                     'binding': 'unexpanded_helper_mention_candidate'})
    return rows

def inventory(root):
    paths = sorted(root.rglob('*'))
    if root.is_symlink() or any(p.is_symlink() for p in paths):
        raise ValueError('symlink source input')
    inputs = [(p, p.read_bytes()) for p in paths if p.is_file()]
    hashes = [[p.relative_to(root).as_posix(), hashlib.sha256(data).hexdigest()]
              for p, data in inputs]
    tree = hashlib.sha256(json.dumps(hashes, separators=(',', ':')).encode()).hexdigest()
    lock = json.loads((Path(__file__).parent / 'source-lock.json').read_text())
    if tree != lock['tree_sha256']:
        raise ValueError('source differs from pinned baseline')
    engine = parser()
    header = 'Libraries/Include/Lib/BaseType.h'
    data = next(data for (path, data), (name, _) in zip(inputs, hashes) if name == header)
    macros = [dict(row, path=header, source_sha256=hashlib.sha256(data).hexdigest())
              for row in conversion_macros(data, engine)]
    routes = HELPERS | CONTROL | {row['name'] for row in macros}
    calls, recoveries, scanned = [], [], 0
    for (path, data), (name, digest) in zip(inputs, hashes):
        if path.suffix.lower() not in {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.inl'}:
            continue
        scanned += 1
        _, found, errors = analyze(data, engine, routes)
        calls.extend(dict(row, path=name, source_sha256=digest) for row in found)
        recoveries.extend(dict(row, path=name) for row in errors)
    return {'schema': 1, 'complete': False,
            'scope': 'Unpreprocessed original conversion macro/helper and rounding-control call candidates; no complete numeric census claim',
            'upstream_commit': lock['upstream_commit'], 'source_tree_sha256': tree,
            'parser_versions': VERSIONS,
            'parser_requirements_sha256': hashlib.sha256((Path(__file__).parent / 'parser-requirements.txt').read_bytes()).hexdigest(),
            'summary': {'files_scanned': scanned, 'conversion_macros': len(macros),
                        'route_sites': len(calls),
                        'routes': dict(sorted(Counter(r['route'] for r in calls).items())),
                        'calls_with_own_parse_error': sum(r['parse_has_error'] for r in calls),
                        'parse_recoveries': len(recoveries)},
            'macros': macros, 'calls': calls, 'parse_recoveries': recoveries,
            'unknowns': ['Unexpanded macro mention can include text rather than an executable helper call',
                         'Aliases, preprocessing, receiver and overload binding unresolved',
                         'Parser recovery can conceal calls; macro expansion and numeric input domains unknown',
                         'Rounding/precision/exception state, compiler effects and thread ownership unresolved',
                         'Full engine determinism and physical Vita/PSTV correctness unproven']}

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
