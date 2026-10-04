# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_chunk_routes import ROUTES, inventory
from audit_system_ownership import analyze, ROUTES as LIFECYCLE_ROUTES
from audit_source_structure import parser
import tempfile

class ChunkRoutes(unittest.TestCase):
    def test_raw_dynamic_arguments_and_guard(self):
        data = b'#if ENABLE_MAP\nvoid f(){ file.registerParser(AsciiString("Object"), info->label, Callback); }\n#endif\n'
        _, rows, _ = analyze(data, parser(), ROUTES)
        self.assertEqual(rows[0]['argument_node_candidates'], ['AsciiString("Object")', 'info->label', 'Callback'])
        self.assertEqual(rows[0]['guards'][0]['condition'], 'ENABLE_MAP')
        self.assertEqual(rows[0]['receiver_binding'], 'unresolved')
    def test_comments_strings_and_unrelated_routes(self):
        _, rows, _ = analyze(b'void f(){ /* readDict(); */ const char *s="registerParser()"; x.init(); x.readDict(); }', parser(), ROUTES)
        self.assertEqual([r['route'] for r in rows], ['readDict'])
        _, lifecycle, _ = analyze(b'void f(){x.init();x.readDict();}', parser())
        self.assertEqual([r['route'] for r in lifecycle], ['init'])
    def test_lambda_ownership_and_recovery(self):
        _, rows, _ = analyze(b'void f(){auto cb=[](){f.readUnicodeString();};}', parser(), ROUTES)
        self.assertEqual(rows[0]['callable']['kind'], 'lambda_expression')
        _, _, errors = analyze(b'void broken( ;', parser(), ROUTES)
        self.assertTrue(errors)
    def test_explicit_default_routes_match(self):
        data = b'void f(){x.init(); x.reset(); x.readDict();}'
        self.assertEqual(analyze(data, parser()), analyze(data, parser(), LIFECYCLE_ROUTES))
    def test_symlink_source_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'real.cpp').write_text('void f(){}')
            (root / 'link.cpp').symlink_to(root / 'real.cpp')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                inventory(root)
    def test_unpinned_source_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'x.cpp').write_text('void f(){}')
            with self.assertRaisesRegex(ValueError, 'pinned baseline'):
                inventory(root)
if __name__ == '__main__':
    unittest.main()
