# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from tools.stage_original import stage

ROOT=Path(__file__).resolve().parents[1]
class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        shutil.copytree(ROOT/'vendor',self.root/'vendor')
        shutil.copytree(ROOT/'port/patches',self.root/'port/patches')
        self.out=self.root/'build/staged'
    def tearDown(self): self.temp.cleanup()
    def test_deterministic_and_pristine(self):
        before=(self.root/'vendor/ea/wwlib/realcrc.cpp').read_bytes()
        first=stage(self.root,self.out)
        after=(self.out/'wwlib/realcrc.cpp').read_bytes()
        self.assertEqual(first,stage(self.root,self.out))
        self.assertEqual(after,(self.out/'wwlib/realcrc.cpp').read_bytes())
        self.assertEqual(before,(self.root/'vendor/ea/wwlib/realcrc.cpp').read_bytes())
    def test_source_mutation_fails_before_writes(self):
        (self.root/'vendor/ea/wwlib/realcrc.cpp').write_text('changed')
        with self.assertRaisesRegex(ValueError,'original source hash'): stage(self.root,self.out)
        self.assertFalse(self.out.exists())
    def test_patch_mutation_fails_before_writes(self):
        manifest=json.loads((self.root/'vendor/ea/manifest.json').read_text())
        (self.root/manifest['patches'][0]['path']).write_text('changed')
        with self.assertRaisesRegex(ValueError,'patch hash'): stage(self.root,self.out)
        self.assertFalse(self.out.exists())
    def test_result_hash_is_enforced(self):
        p=self.root/'vendor/ea/manifest.json'; m=json.loads(p.read_text())
        m['files'][0]['staged_sha256']='0'*64;p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'patched source hash'): stage(self.root,self.out)
    def test_output_escape_rejected(self):
        for target in [self.root,self.root/'vendor/staged',self.root.parent/'staged']:
            with self.subTest(target=target), self.assertRaises(ValueError): stage(self.root,target)
    def test_manifest_escape_rejected(self):
        p=self.root/'vendor/ea/manifest.json';m=json.loads(p.read_text());m['files'][0]['path']='../../../escape';p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'escapes root'): stage(self.root,self.out)
if __name__=='__main__': unittest.main()
