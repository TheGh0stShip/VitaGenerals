# SPDX-License-Identifier: GPL-3.0-or-later
import struct
import tempfile
from pathlib import Path
import unittest
from tools.inventory_content import big_directory, source_inventory

class InventoryTests(unittest.TestCase):
    def archive(self, raw):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'fixture.big'
            path.write_bytes(raw)
            return big_directory(path)
    def fixture(self, offset=26, length=1, name=b'x\0'):
        return b'BIGF'+struct.pack('<I',27)+struct.pack('>II',1,26)+struct.pack('>II',offset,length)+name+b'z'
    def test_directory(self):
        result = self.archive(self.fixture())
        self.assertEqual(result['members'][0]['name'], 'x')
        self.assertEqual(result['members'][0]['offset_u32'], 26)
        self.assertFalse(result['payload_hashed'])
    def test_empty_marker(self):
        result = self.archive(self.fixture(offset=0,length=0))
        self.assertEqual(result['members'][0]['empty_entry_semantics'],'unresolved')
    def test_payload_bounds(self):
        for offset,length in [(25,1),(28,0),(26,2),(0xffffffff,1)]:
            with self.subTest(offset=offset,length=length), self.assertRaises(ValueError):
                self.archive(self.fixture(offset,length))
    def test_termination(self):
        with self.assertRaises(ValueError):
            self.archive(self.fixture(name=b'xx'))
    def test_truncation(self):
        raw=self.fixture()
        for n in range(len(raw)):
            with self.subTest(n=n), self.assertRaises(ValueError):
                self.archive(raw[:n])
    def test_source_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'a.cpp').write_text('// "ignored.dds"\nconst char *s="Data/Art/a.dds";\nvoid f() { size_t n=0; }\n')
            rows,edges,candidates=source_inventory(root)
            self.assertEqual(len(rows),1)
            self.assertEqual(len(edges),1)
            self.assertEqual(edges[0]['line'],2)
            self.assertEqual(edges[0]['evidence'],'lexical_literal_candidate')
            self.assertTrue(any(c['token']=='f' for c in candidates))
            self.assertTrue(any(c['token']=='size_t' for c in candidates))
if __name__=='__main__':
    unittest.main()
