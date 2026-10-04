# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_function_lexicon import analyze, inventory
from audit_source_structure import parser

class FunctionLexicon(unittest.TestCase):
    def test_order_duplicates_and_sentinel(self):
        tables,errors=analyze(b'FunctionLexicon::TableEntry t[]={ {K,"same",f}, {K,"same",g}, {K,NULL,NULL} };',parser())
        self.assertFalse(errors)
        self.assertEqual([e['function_candidate'] for e in tables[0]['entries']],['f','g','NULL'])
        self.assertEqual(tables[0]['entries'][-1]['status'],'sentinel_candidate')
    def test_comments_and_other_types(self):
        tables,_=analyze(b'/* FunctionLexicon::TableEntry t[]={{K,"fake",f}}; */ Other::TableEntry x[]={{K,"other",g}}; FunctionLexicon::TableEntry real[]={{K,"yes",f}};',parser())
        self.assertEqual(len(tables),1)
        self.assertEqual(tables[0]['entries'][0]['name_candidate'],'yes')
    def test_string_spelling_and_expression_retained(self):
        tables,_=analyze(b'FunctionLexicon::TableEntry t[]={{K,"a\\n",f}, {K,L"wide",g}, {K,"plain",(void*)h}};',parser())
        rows=tables[0]['entries']
        self.assertEqual([r['status'] for r in rows],['string_spelling_unresolved','string_spelling_unresolved','literal_entry_candidate'])
        self.assertEqual(rows[2]['function_candidate'],'(void*)h')
    def test_conditional_and_parser_errors_retained(self):
        tables,_=analyze(b'FunctionLexicon::TableEntry t[]={\n#if ENABLE\n{K,"x",f},\n#endif\n{K,NULL,NULL}};',parser())
        self.assertEqual(tables[0]['entries'][0]['status'],'unsupported_initializer')
        _,errors=analyze(b'void broken( ;',parser())
        self.assertTrue(errors)
    def test_symlink_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'x.cpp').write_text('void f(){}');(root/'link.cpp').symlink_to(root/'x.cpp')
            with self.assertRaisesRegex(ValueError,'symlink'):inventory(root)
    def test_unpinned_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'x.cpp').write_text('void f(){}')
            with self.assertRaisesRegex(ValueError,'pinned baseline'):inventory(root)
if __name__=='__main__':unittest.main()
