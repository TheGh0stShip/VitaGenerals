# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_include_paths import scan, resolve

class IncludePaths(unittest.TestCase):
    def test_comments_strings_and_inactive_directives(self):
        text = '// #include "fake.h"\nconst char *s = "#include fake";\n/*\n#include "fake2.h"\n*/\n#if 0\n#include "real.h" // trailing\n#endif\n'
        self.assertEqual(scan(text), [{'line': 7, 'kind': 'quoted', 'operand': 'real.h'}])
    def test_multiline_trailing_comment(self):
        self.assertEqual(scan('#include "a.h" /* trailing\n comment */\n')[0]["operand"], "a.h")
        self.assertEqual(scan('#include "a.h" /* trailing\n comment */\n')[0]["kind"], "quoted")
    def test_splicing_and_computed_operands(self):
        rows = scan('#inc\\\nlude "a.h"\n#include HEADER\n#include <stdio.h>\n')
        self.assertEqual([r['line'] for r in rows], [1, 3, 4])
        self.assertEqual([r['kind'] for r in rows], ['quoted', 'computed_or_unsupported', 'angled'])
    def test_relative_case_and_duplicate_roots(self):
        r = resolve('Lib/thread.h', 'vector.h', {'Lib/Vector.H', 'Tools/Vector.H'})
        self.assertFalse(r['relative_exact'])
        self.assertEqual(r['relative_case_candidates'], ['Lib/Vector.H'])
        self.assertEqual(r['search_root_candidates'], ['Lib/Vector.H', 'Tools/Vector.H'])
        self.assertIsNone(r['selected_header'])
    def test_backslash_and_parent_resolution(self):
        r = resolve('Lib/Debug/a.h', '..\\..\\Engine\\debug.h', {'Engine/debug.h'})
        self.assertTrue(r['backslash_spelling'])
        self.assertTrue(r['relative_exact'])
        self.assertEqual(r['search_root_candidates'], [])
    def test_comment_between_directive_and_operand(self):
        self.assertEqual(scan('# /*x*/ include /*y*/ "a.h"')[0]['operand'], 'a.h')
if __name__ == '__main__':
    unittest.main()
