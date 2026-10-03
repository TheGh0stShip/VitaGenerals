# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_module_registrations import scan

class Registrations(unittest.TestCase):
    def test_comments_and_literals(self):
        rows,defs=scan('// addModule(Fake)\n"addModule(Fake)";\n/* addModule(Fake) */\naddModule(Real);')
        self.assertEqual([(r['line'],r['class_name']) for r in rows],[(4,'Real')])
    def test_multiline_and_definition(self):
        rows,defs=scan('#define addModule(x) something(x)\naddModule(\n Thing\n);')
        self.assertEqual(defs,[1]);self.assertEqual(rows[0]['class_name'],'Thing')
    def test_nested_alternatives(self):
        rows,_=scan('#ifdef A\n#if B\naddModule(X);\n#elif C\naddModule(Y);\n#else\naddModule(Z);\n#endif\n#endif')
        self.assertEqual(len(rows[2]['conditional_branches']),2)
        self.assertEqual([b['directive'] for b in rows[2]['conditional_branches'][1]],['if','elif','else'])
        self.assertEqual(rows[0]['preprocessor_reachability'],'unknown')
    def test_continued_comment(self):
        rows,_=scan('// ignored '+chr(92)+'\naddModule(Fake);\naddModule(Real);')
        self.assertEqual([r['class_name'] for r in rows],['Real'])
    def test_unknown_syntax_fails(self):
        for text in ['addModule(nested(X));','#else\naddModule(X);','#if A\naddModule(X);']:
            with self.assertRaises(ValueError):scan(text)
if __name__=='__main__':unittest.main()
