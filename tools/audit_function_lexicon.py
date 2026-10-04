#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Inventory exact-spelling callback table initializer candidates in pinned source."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
from audit_source_structure import parser, VERSIONS

def analyze(data, engine):
    source = data.decode('latin1').encode('utf8')
    tree = engine.parse(source)
    def text(node):
        return source[node.start_byte:node.end_byte].decode('utf8') if node else None
    tables, errors, stack = [], [], [tree.root_node]
    while stack:
        node = stack.pop()
        stack.extend(reversed(node.named_children))
        if node.type == 'ERROR' or node.is_missing:
            errors.append({'line': node.start_point.row + 1, 'kind': node.type,
                           'missing': node.is_missing})
        if node.type != 'declaration' or text(node.child_by_field_name('type')) != 'FunctionLexicon::TableEntry':
            continue
        for init in node.named_children:
            if init.type != 'init_declarator':
                continue
            value = init.child_by_field_name('value')
            if not value or value.type != 'initializer_list':
                continue
            entries = []
            for row in value.named_children:
                if row.type == 'comment':
                    continue
                args = [x for x in row.named_children if x.type != 'comment']
                literal = text(args[1]) if len(args) == 3 and args[1].type == 'string_literal' else None
                plain = literal is not None and literal.startswith('"') and literal.endswith('"') and '\\' not in literal
                status = ('literal_entry_candidate' if plain else
                          'string_spelling_unresolved' if literal is not None else
                          'sentinel_candidate' if len(args) == 3 and text(args[1]) == 'NULL' else
                          'unsupported_initializer')
                entries.append({'line': row.start_point.row + 1, 'raw': text(row),
                                'arguments': [text(x) for x in args],
                                'name_candidate': literal[1:-1] if plain else None,
                                'function_candidate': text(args[2]) if len(args) == 3 else None,
                                'parse_has_error': row.has_error, 'status': status,
                                'preprocessor_reachability': 'unresolved'})
            tables.append({'line': node.start_point.row + 1,
                           'declarator': text(init.child_by_field_name('declarator')),
                           'entries': entries, 'parse_has_error': node.has_error})
    return tables, errors

def inventory(root):
    paths = sorted(root.rglob('*'))
    if any(p.is_symlink() for p in paths):
        raise ValueError('symlink source input')
    inputs = [(p, p.read_bytes()) for p in paths if p.is_file()]
    hashes = [[p.relative_to(root).as_posix(), hashlib.sha256(data).hexdigest()] for p, data in inputs]
    tree = hashlib.sha256(json.dumps(hashes, separators=(',', ':')).encode()).hexdigest()
    lock = json.loads((Path(__file__).parent / 'source-lock.json').read_text())
    if tree != lock['tree_sha256']:
        raise ValueError('source differs from pinned baseline')
    engine = parser()
    tables, errors, scanned, selected = [], [], 0, 0
    for (path, data), (name, digest) in zip(inputs, hashes):
        if path.suffix.lower() not in {'.cpp', '.h', '.c', '.hpp', '.inl', '.cc', '.cxx'}:
            continue
        scanned += 1
        if b'TableEntry' not in data:
            continue
        selected += 1
        found, recoveries = analyze(data, engine)
        tables.extend(dict(row, path=name, source_sha256=digest) for row in found)
        errors.extend(dict(row, path=name) for row in recoveries)
    return {'schema': 1, 'complete': False, 'upstream_commit': lock['upstream_commit'],
            'source_tree_sha256': tree, 'parser_versions': VERSIONS,
            'parser_requirements_sha256': hashlib.sha256((Path(__file__).parent / 'parser-requirements.txt').read_bytes()).hexdigest(),
            'scope': 'Raw TableEntry-prefiltered C/C++ inputs; exact FunctionLexicon::TableEntry initializer spelling only',
            'summary': {'C_CPP_inputs': scanned, 'prefiltered_C_CPP_inputs': selected,
                        'tables': len(tables), 'entries': sum(len(x['entries']) for x in tables),
                        'statuses': dict(sorted(Counter(e['status'] for x in tables for e in x['entries']).items())),
                        'parse_recoveries': len(errors)},
            'tables': tables, 'parse_recoveries': errors,
            'unknowns': ['Token prefilter and exact type spelling may omit macros or aliases',
                         'Conditional initializer nodes retained as unsupported; no preprocessing or registration proof',
                         'Escaped or prefixed names unresolved; raw spellings retained',
                         'Callback signature, address, original build/link and runtime ownership unresolved',
                         'Retail WND scope, provider precedence and input routing incomplete',
                         'ARM ABI and physical Vita/PSTV correctness unproven']}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    result = inventory(args.source)
    data = (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gzip.compress(data, mtime=0) if args.output.suffix == '.gz' else data)
    print(json.dumps(result['summary'], sort_keys=True))
if __name__ == '__main__':
    main()
