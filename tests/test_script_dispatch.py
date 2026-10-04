# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_script_dispatch import enum_rows, dispatch_rows

class ScriptDispatch(unittest.TestCase):
    def test_enum_values_and_comments(self):
        rows=enum_rows('enum E { A, /* fake */ B=7, C, }; enum E member;', 'E')
        self.assertEqual([(r['name'],r['value']) for r in rows],[('A',0),('B',7),('C',8)])
    def test_enum_expression_fails(self):
        for text in ['enum E {A=1<<2};','enum E {A,A};','enum E {\n#if X\nA\n#endif\n};']:
            with self.assertRaises(ValueError):enum_rows(text,'E')
    def test_dispatch_scope_and_literals(self):
        text='void Other(){case Q::Fake: foo();} void Owner::run(){switch(x){case Q::A: call(); return false; case Q::B: "case Q::Fake:"; nested(get()); return;}}'
        rows=dispatch_rows(text,'Owner::run','Q')
        self.assertEqual([r['name'] for r in rows],['A','B'])
        self.assertEqual(rows[0]['constant_return_candidates'],['false'])
        self.assertEqual(rows[1]['call_identifier_candidates'],['get','nested'])
    def test_unsupported_label_fails(self):
        with self.assertRaises(ValueError):dispatch_rows('void O::run(){case 7: return;}','O::run','Q')
    def test_ambiguous_or_missing_owner_fails(self):
        for text in ['void O::run(){','void O::run(){} void O::run(int x){}','void Other(){}']:
            with self.assertRaises(ValueError):dispatch_rows(text,'O::run','Q')
if __name__=='__main__':unittest.main()
