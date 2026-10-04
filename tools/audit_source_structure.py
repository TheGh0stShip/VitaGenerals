#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Unpreprocessed C++ structure inventory with explicit parser recovery gaps."""
import argparse
import gzip
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path

VERSIONS={'tree-sitter':'0.25.2','tree-sitter-cpp':'0.23.4'}

def parser():
    for name,version in VERSIONS.items():
        if importlib.metadata.version(name)!=version:raise ValueError('parser dependency version mismatch')
    from tree_sitter import Language,Parser
    import tree_sitter_cpp
    return Parser(Language(tree_sitter_cpp.language()))

def analyze(data,engine):
    # Original source is byte-oriented legacy text. Transcode explicitly, retaining
    # original input hash and line provenance; UTF-8 byte columns are not disk offsets.
    source=data.decode('latin1').encode('utf8');tree=engine.parse(source)
    functions=[];guards=[];returns=[];errors=[];classes=[]
    def text(node):return source[node.start_byte:node.end_byte].decode('utf8') if node else None
    def span(node):return {'line':node.start_point.row+1,'end_line':node.end_point.row+1}
    pending=[(tree.root_node,None,[],[])]
    while pending:
        node,owner,guard_chain,class_chain=pending.pop()
        if node.type=='ERROR' or node.is_missing:
            errors.append(dict(span(node),kind='missing' if node.is_missing else 'ERROR',node_type=node.type))
        if node.type in {'preproc_if','preproc_ifdef','preproc_elif','preproc_else'}:
            condition=node.child_by_field_name('condition') or node.child_by_field_name('name')
            index=len(guards);guards.append(dict(span(node),kind=node.type,directive=text(node.children[0]),condition=text(condition),parent_guard_indices=list(guard_chain),reachability='unknown'));guard_chain=guard_chain+[index]
        if node.type in {'class_specifier','struct_specifier'}:
            name=text(node.child_by_field_name('name'));classes.append(dict(span(node),name=name,parse_has_error=node.has_error))
            class_chain=class_chain+[name]
        if node.type in {'function_definition','lambda_expression'}:
            owner=len(functions);body=node.child_by_field_name('body');declarator=node.child_by_field_name('declarator')
            children=[c for c in body.named_children if c.type!='comment'] if body else []
            functions.append(dict(span(node),kind=node.type,declarator=text(declarator),class_context=list(class_chain),guard_indices=list(guard_chain),parse_has_error=node.has_error,file_has_parse_error=tree.root_node.has_error,body_empty_candidate=bool(body) and not children,
                sole_return_candidate=len(children)==1 and children[0].type=='return_statement',behavior_verified=False))
        if node.type=='return_statement':
            values=[c for c in node.named_children if c.type!='comment'];value=values[0] if values else None
            spelling=text(value)
            literal=(value is not None and value.type in {'true','false','number_literal','null','nullptr'}) or spelling in {'NULL','TRUE','FALSE'}
            returns.append(dict(span(node),function_index=owner,guard_indices=list(guard_chain),value_node_type=value.type if value else None,literal_candidate=spelling if literal else None,void_return=value is None,control_flow_verified=False))
        pending.extend((child,owner,guard_chain,class_chain) for child in reversed(node.children))
    return {'functions':functions,'classes':classes,'guards':guards,'returns':returns,'parse_recoveries':errors,'parse_has_error':tree.root_node.has_error}

def inventory(root):
    files=sorted(p for p in root.rglob('*') if p.is_file())
    if any(p.is_symlink() for p in root.rglob('*')):raise ValueError('symlink source inputs are unsupported')
    hashes={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    tree=hashlib.sha256(json.dumps([[p.relative_to(root).as_posix(),hashes[p]] for p in files],separators=(',',':')).encode()).hexdigest()
    lock=json.loads((Path(__file__).parent/'source-lock.json').read_text())
    if tree!=lock['tree_sha256']:raise ValueError('source differs from pinned baseline')
    engine=parser();rows=[]
    for p in files:
        if p.suffix.lower() not in {'.c','.cpp','.cc','.cxx','.h','.hpp','.inl'}:continue
        rows.append(dict(analyze(p.read_bytes(),engine),path=p.relative_to(root).as_posix(),sha256=hashes[p]))
    summary={'files_scanned':len(rows),'files_with_parse_recoveries':sum(r['parse_has_error'] for r in rows)}
    for key in ['functions','classes','guards','returns','parse_recoveries']:summary[key]=sum(len(r[key]) for r in rows)
    summary['functions_with_own_parse_error']=sum(f['parse_has_error'] for r in rows for f in r['functions'])
    summary['returns_without_callable_owner']=sum(v['function_index'] is None for r in rows for v in r['returns'])
    summary['literal_return_candidates']=sum(v['literal_candidate'] is not None for r in rows for v in r['returns'])
    return {'schema':1,'complete':False,'scope':'Unpreprocessed parsed structure across pinned C/C++ source/header files; C files parsed using C++ grammar',
            'upstream_commit':lock['upstream_commit'],'source_tree_sha256':tree,'parser_versions':VERSIONS,'parser_requirements_sha256':hashlib.sha256((Path(__file__).parent/'parser-requirements.txt').read_bytes()).hexdigest(),'input_encoding':'latin1 transcoded to UTF-8; original SHA256 and line coordinates retained',
            'summary':summary,'rows':rows,'unknowns':['Parser recoveries may omit or misclassify structure','Preprocessor branches and macro expansion are not evaluated','Return candidates are not stubs or proven early exits','Class context is not resolved inheritance or name lookup','Callable identities, signatures and build/link selection','Physical runtime behavior and complete game acceptance']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=inventory(a.source);a.output.parent.mkdir(parents=True,exist_ok=True)
    encoded=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    if a.output.suffix=='.gz':
        buffer=io.BytesIO()
        with gzip.GzipFile(fileobj=buffer,mode='wb',filename='',mtime=0) as stream:stream.write(encoded)
        a.output.write_bytes(buffer.getvalue())
    else:a.output.write_bytes(encoded)
    print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
