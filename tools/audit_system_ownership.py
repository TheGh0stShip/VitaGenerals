#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Inventory parsed subsystem/snapshot candidates; no runtime ownership claim."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
from audit_source_structure import parser, VERSIONS

ROUTES = {'initSubsystem', 'addSubsystem', 'removeSubsystem', 'resetAll',
          'shutdownAll', 'postProcessLoadAll', 'UPDATE', 'DRAW', 'xferSnapshot',
          'crc', 'xfer', 'loadPostProcess', 'init', 'reset', 'update', 'draw',
          'postProcessLoad', 'addSnapshotBlock'}
SEEDS = ('SubsystemInterface', 'Snapshot')

def analyze(data, engine, routes=None):
    routes = ROUTES if routes is None else routes
    source = data.decode('latin1').encode('utf8')
    tree = engine.parse(source)
    classes, calls, recoveries = [], [], []
    def text(node):
        return source[node.start_byte:node.end_byte].decode('utf8') if node else None
    def span(node):
        return {'line': node.start_point.row + 1, 'end_line': node.end_point.row + 1}
    pending = [(tree.root_node, [], None, [])]
    while pending:
        node, context, owner, guards = pending.pop()
        if node.type == 'ERROR' or node.is_missing:
            recoveries.append(dict(span(node), type=node.type, missing=node.is_missing))
        if node.type in {'preproc_if', 'preproc_ifdef', 'preproc_elif', 'preproc_else'}:
            spelling = re.match(r'\s*#\s*(\w+)', text(node))
            guard = dict(span(node), directive=spelling[1] if spelling else node.type,
                         condition=text(node.child_by_field_name('condition') or node.child_by_field_name('name')),
                         reachability='unknown')
            guards = guards + [guard]
        if node.type in {'namespace_definition', 'class_specifier', 'struct_specifier'}:
            name = text(node.child_by_field_name('name'))
            if node.type != 'namespace_definition':
                clause = next((c for c in node.named_children if c.type == 'base_class_clause'), None)
                bases = []
                if clause:
                    # Base nodes preserve commas inside templates. Access tokens are separate.
                    for base in clause.named_children:
                        if base.type in {'access_specifier', 'comment'}:
                            continue
                        spelling = text(base)
                        simple = base.type in {'type_identifier', 'qualified_identifier'} and bool(re.fullmatch(r'(?:::)?(?:[A-Za-z_]\w*::)*[A-Za-z_]\w*', spelling))
                        bases.append({'spelling': spelling, 'node_type': base.type,
                                      'simple_name_candidate': spelling.lstrip(':') if simple else None})
                classes.append(dict(span(node), name=name, context=context,
                                    qualified_name_candidate='::'.join([*context, name]) if name and all(context) else None,
                                    base_clause=text(clause), bases=bases, guards=guards,
                                    has_body=node.child_by_field_name("body") is not None,
                                    parse_has_error=node.has_error))
            context = context + [name]
        if node.type == 'function_definition':
            owner = {'kind': node.type, 'declarator': text(node.child_by_field_name('declarator')), **span(node)}
        elif node.type == 'lambda_expression':
            owner = {'kind': node.type, 'declarator': None, **span(node)}
        if node.type == 'call_expression':
            expression = text(node.child_by_field_name('function')) or ''
            last = re.search(r'([A-Za-z_]\w*)$', expression)
            if last and last[1] in routes:
                args = node.child_by_field_name('arguments')
                calls.append(dict(span(node), call=expression, route=last[1], arguments=text(args),
                                  argument_node_candidates=[text(c) for c in args.named_children if c.type != 'comment'] if args else [],
                                  context=context, callable=owner, guards=guards,
                                  parse_has_error=node.has_error, file_has_parse_error=tree.root_node.has_error,
                                  receiver_binding='unresolved', runtime_execution='unverified'))
        pending.extend((c, context, owner, guards) for c in reversed(node.children))
    return classes, calls, recoveries

def candidate_graph(classes):
    by_name, by_qualified = defaultdict(list), defaultdict(list)
    for index, row in enumerate(classes):
        row['class_index'] = index
        if row['name']:
            by_name[row['name']].append(index)
        if row['qualified_name_candidate']:
            by_qualified[row['qualified_name_candidate']].append(index)
    for row in classes:
        for base in row['bases']:
            name = base['simple_name_candidate']
            candidates = (by_qualified if name and '::' in base['spelling'] else by_name).get(name, []) if name else []
            base['class_candidates'] = list(candidates)
            base['ambiguous'] = len(candidates) > 1
            base['binding'] = 'unresolved'
    # Propagate independently per record, retaining all ambiguous candidates.
    membership = [set(seed for seed in SEEDS if row['name'] == seed and row['has_body']) for row in classes]
    changed = True
    while changed:
        changed = False
        for index, row in enumerate(classes):
            candidate = set(membership[index])
            for base in row['bases']:
                for parent in base['class_candidates']:
                    candidate.update(membership[parent])
            if candidate != membership[index]:
                membership[index] = candidate
                changed = True
    for row, seeds in zip(classes, membership):
        row['seed_candidates'] = sorted(seeds)
    return {seed: [i for i, values in enumerate(membership) if seed in values] for seed in SEEDS}

def inventory(root):
    paths = sorted(root.rglob('*'))
    if any(p.is_symlink() for p in paths):
        raise ValueError('symlink source input')
    files = [p for p in paths if p.is_file()]
    inputs = [(p, p.read_bytes()) for p in files]
    hashes = [[p.relative_to(root).as_posix(), hashlib.sha256(data).hexdigest()] for p, data in inputs]
    tree = hashlib.sha256(json.dumps(hashes, separators=(',', ':')).encode()).hexdigest()
    lock = json.loads((Path(__file__).parent / 'source-lock.json').read_text())
    if tree != lock['tree_sha256']:
        raise ValueError('source differs from pinned baseline')
    engine = parser()
    classes, calls, recoveries = [], [], []
    scanned = 0
    for (path, data), (name, digest) in zip(inputs, hashes):
        if path.suffix.lower() not in {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.inl'}:
            continue
        scanned += 1
        groups = analyze(data, engine)
        for output, group in zip((classes, calls, recoveries), groups):
            output.extend(dict(row, path=name, source_sha256=digest) for row in group)
    closure = candidate_graph(classes)
    return {'schema': 1, 'complete': False, 'scope': 'Unpreprocessed class/base candidates and named lifecycle/snapshot call routes across pinned C/C++ files',
            'upstream_commit': lock['upstream_commit'], 'source_tree_sha256': tree,
            'parser_versions': VERSIONS, 'parser_requirements_sha256': hashlib.sha256((Path(__file__).parent / 'parser-requirements.txt').read_bytes()).hexdigest(),
            'summary': {'files_scanned': scanned, 'class_records': len(classes),
                        'seed_class_candidates': {k: len(v) for k, v in closure.items()},
                        'class_records_with_body': sum(c['has_body'] for c in classes),
                        'route_sites': len(calls), 'routes': dict(sorted(Counter(r['route'] for r in calls).items())),
                        'calls_with_own_parse_error': sum(r['parse_has_error'] for r in calls),
                        'ambiguous_base_sites': sum(b['ambiguous'] for r in classes for b in r['bases']),
                        'unsupported_base_nodes': sum(b['simple_name_candidate'] is None for r in classes for b in r['bases']),
                        'parse_recoveries': len(recoveries)},
            'classes': classes, 'seed_candidate_indices': closure, 'calls': calls, 'parse_recoveries': recoveries,
            'unknowns': ['Candidate edges do not resolve C++ namespace lookup, aliases, templates or preprocessing',
                         'Name matches can include unrelated classes and tools; no runtime graph selection',
                         'Parser recoveries can omit structure or split allocation-macro argument nodes; raw argument spellings retained',
                         'Named calls do not prove receiver/overload binding, lifetime or registration execution',
                         'Additional lifecycle, factory and transfer mechanisms; complete asset/input/game ownership',
                         'Host/ARM engine compilation, full game behavior and physical Vita/PSTV acceptance']}

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
