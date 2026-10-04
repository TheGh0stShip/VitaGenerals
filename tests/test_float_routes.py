# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_float_routes import HELPERS, CONTROL, conversion_macros, inventory
from audit_system_ownership import analyze
from audit_source_structure import parser

class FloatRoutes(unittest.TestCase):
    def test_macro_bodies_preserve_narrowing_and_multiline(self):
        data = b'#define DOUBLE_TO_INT(x) ((Int)fast_float2long_round(\\\n fast_float_trunc(x)))\n'
        rows = conversion_macros(data, parser())
        self.assertEqual([r['name'] for r in rows], ['DOUBLE_TO_INT'])
        self.assertIn('fast_float_trunc(x)', rows[0]['value'])
        self.assertIn('\\\n', rows[0]['raw'])
        self.assertEqual(rows[0]['binding'], 'unexpanded_helper_mention_candidate')

    def test_macro_comments_aliases_and_string_mentions(self):
        data = b'/* #define FAKE(x) fast_float_trunc(x) */\n#define ALIAS(x) OTHER(x)\n#define TEXT(x) "fast_float_trunc(x)"\n'
        rows = conversion_macros(data, parser())
        self.assertEqual([r['name'] for r in rows], ['TEXT'])
        self.assertEqual(rows[0]['value'], '"fast_float_trunc(x)"')

    def test_macro_call_arguments_and_control_order(self):
        routes = HELPERS | CONTROL | {'REAL_TO_INT'}
        _, rows, _ = analyze(b'void f(){setFPMode(); auto x=REAL_TO_INT(a+b); _controlfp(value,mask);}', parser(), routes)
        self.assertEqual([r['route'] for r in rows], ['setFPMode', 'REAL_TO_INT', '_controlfp'])
        self.assertEqual(rows[1]['argument_node_candidates'], ['a+b'])
        self.assertEqual(rows[2]['argument_node_candidates'], ['value', 'mask'])

    def test_comment_and_string_calls_not_executable(self):
        _, rows, _ = analyze(b'#if NUMERIC\nvoid f(){/*fast_float_trunc(x);*/ const char*s="setFPMode()"; fast_float_floor(x);}\n#endif', parser(), HELPERS | CONTROL)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['guards'][0]['condition'], 'NUMERIC')
        self.assertEqual(rows[0]['runtime_execution'], 'unverified')

    def test_lambda_and_recovery(self):
        _, rows, _ = analyze(b'void f(){auto fn=[](){return fast_float_ceil(x);};}', parser(), HELPERS)
        self.assertEqual(rows[0]['callable']['kind'], 'lambda_expression')
        _, _, errors = analyze(b'void broken( ;', parser(), HELPERS)
        self.assertTrue(errors)

    def test_unpinned_and_symlink_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'x.cpp').write_text('void f(){}')
            with self.assertRaisesRegex(ValueError, 'pinned baseline'):
                inventory(root)
            (root / 'link.cpp').symlink_to(root / 'x.cpp')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                inventory(root)
            (root / 'link.cpp').unlink()
            (root / 'alias').symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                inventory(root / 'alias')

if __name__ == '__main__':
    unittest.main()
