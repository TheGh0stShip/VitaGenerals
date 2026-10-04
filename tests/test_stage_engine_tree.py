# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from stage_engine_tree import stage,sha,fingerprint,verify_build_stage

class EngineStaging(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        repo=Path(__file__).resolve().parents[1]
        shutil.copytree(repo/'vendor',self.root/'vendor');shutil.copytree(repo/'port/patches',self.root/'port/patches')
        self.source=self.root/'original/GeneralsMD/Code';self.source.mkdir(parents=True)
        self.manifest=json.loads((self.root/'vendor/ea/manifest.json').read_text())
        for row in self.manifest['files']:
            target=self.source/row['upstream_path'].removeprefix('GeneralsMD/Code/');target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(self.root/'vendor/ea'/row['path'],target)
        (self.source/'extra.cpp').write_text('int original_extra;\n')
        (self.source/'order').mkdir()
        (self.source/'order/a.cpp').write_text('int nested;\n')
        (self.source/'order.cpp').write_text('int sibling;\n')
        (self.root/'LICENSE.md').write_text('license fixture\n');shutil.copyfile(self.root/'LICENSE.md',self.source.parent.parent/'LICENSE.md')
        rows=[[p.relative_to(self.source).as_posix(),sha(p)] for p in sorted(self.source.rglob('*')) if p.is_file()]
        (self.root/'tools').mkdir();(self.root/'tools/source-lock.json').write_text(json.dumps({'upstream_commit':self.manifest['upstream_commit'],'tree_sha256':fingerprint(rows)}))
        self.output=self.root/'build-engine/staged'
    def tearDown(self):self.tmp.cleanup()
    def test_complete_stage_and_idempotence(self):
        original={p:sha(p) for p in self.source.rglob('*') if p.is_file()}
        receipt=stage(self.root,self.source,self.output)
        self.assertEqual(receipt['source_files'],len(self.manifest['files'])+3);self.assertFalse(receipt['engine_build_established'])
        for row in self.manifest['files']:
            p=self.output/'Code'/row['upstream_path'].removeprefix('GeneralsMD/Code/')
            self.assertEqual(sha(p),row['staged_sha256'])
        times={p:p.stat().st_mtime_ns for p in self.output.rglob('*') if p.is_file()}
        self.assertEqual(stage(self.root,self.source,self.output),receipt)
        self.assertEqual(times,{p:p.stat().st_mtime_ns for p in times})
        self.assertEqual(original,{p:sha(p) for p in original})
    def test_dirty_source_rejected_before_output(self):
        (self.source/'extra.cpp').write_text('changed')
        with self.assertRaises(ValueError):stage(self.root,self.source,self.output)
        self.assertFalse(self.output.exists())
    def test_consumer_verifies_current_stage(self):
        receipt=stage(self.root,self.source,self.output)
        self.assertEqual(verify_build_stage(self.root,self.output),receipt)
    def test_consumer_rejects_stale_metadata(self):
        stage(self.root,self.source,self.output)
        lock=self.root/'tools/source-lock.json';lock.write_text(lock.read_text()+'\n')
        with self.assertRaisesRegex(ValueError,'current source and patch pins'):
            verify_build_stage(self.root,self.output)
    def test_consumer_rejects_resigned_incomplete_stage(self):
        receipt=stage(self.root,self.source,self.output)
        (self.output/'Code/extra.cpp').unlink()
        receipt['files']=[row for row in receipt['files'] if row['path']!='Code/extra.cpp']
        receipt['source_files']-=1
        receipt['staged_tree_sha256']=fingerprint([[row['path'],row['sha256']] for row in receipt['files']])
        (self.output/'receipt.json').write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError,'complete pinned original tree'):
            verify_build_stage(self.root,self.output)
    def test_consumer_rejects_resigned_patch_mutation(self):
        receipt=stage(self.root,self.source,self.output)
        row=self.manifest['files'][0]
        name='Code/'+row['upstream_path'].removeprefix('GeneralsMD/Code/')
        target=self.output/name;target.write_bytes(target.read_bytes()+b'\n')
        for entry in receipt['files']:
            if entry['path']==name:entry['sha256']=sha(target)
        receipt['staged_tree_sha256']=fingerprint([[entry['path'],entry['sha256']] for entry in receipt['files']])
        (self.output/'receipt.json').write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError,'mismatched staged patch target'):
            verify_build_stage(self.root,self.output)
    def test_dirty_stage_preserved(self):
        stage(self.root,self.source,self.output);target=self.output/'Code/extra.cpp';target.write_text('local edits')
        with self.assertRaises(ValueError):stage(self.root,self.source,self.output)
        self.assertEqual(target.read_text(),'local edits')
    def test_patch_failure_preserves_previous_stage(self):
        stage(self.root,self.source,self.output);previous=(self.output/'receipt.json').read_bytes()
        with patch('stage_engine_tree.stage_patches',side_effect=ValueError('failure')):
            with self.assertRaises(ValueError):stage(self.root,self.source,self.output)
        self.assertEqual((self.output/'receipt.json').read_bytes(),previous)
    def test_failed_promotion_restores_previous_generation(self):
        stage(self.root,self.source,self.output);previous=(self.output/'receipt.json').read_bytes()
        lock=self.root/'tools/source-lock.json';lock.write_text(lock.read_text()+'\n')
        replace=os.replace
        def fail_generation(source,target):
            if Path(source).name=='generation' and Path(target)==self.output:raise OSError('promotion failure')
            return replace(source,target)
        with patch('stage_engine_tree.os.replace',side_effect=fail_generation):
            with self.assertRaises(OSError):stage(self.root,self.source,self.output)
        self.assertEqual((self.output/'receipt.json').read_bytes(),previous)
        self.assertEqual((self.output/'Code/extra.cpp').read_text(),'int original_extra;\n')
    def test_exception_after_committed_rename_keeps_valid_new_generation(self):
        stage(self.root,self.source,self.output)
        lock=self.root/'tools/source-lock.json';lock.write_text(lock.read_text()+'\n')
        replace=os.replace
        def interrupt_after_commit(source,target):
            result=replace(source,target)
            if Path(source).name=='generation' and Path(target)==self.output:raise KeyboardInterrupt()
            return result
        with patch('stage_engine_tree.os.replace',side_effect=interrupt_after_commit):
            with self.assertRaises(KeyboardInterrupt):stage(self.root,self.source,self.output)
        receipt=json.loads((self.output/'receipt.json').read_text())
        self.assertEqual(receipt['source_lock_sha256'],sha(lock))
        self.assertEqual((self.output/'Code/extra.cpp').read_text(),'int original_extra;\n')
    def test_license_and_output_bounds(self):
        with self.assertRaises(ValueError):stage(self.root,self.source,self.root/'build-engine')
        (self.source.parent.parent/'LICENSE.md').write_text('changed')
        with self.assertRaises(ValueError):stage(self.root,self.source,self.output)
    def test_symlink_output_rejected(self):
        self.output.parent.mkdir();self.output.symlink_to(self.source,target_is_directory=True)
        with self.assertRaises(ValueError):stage(self.root,self.source,self.output)
if __name__=='__main__':unittest.main()
