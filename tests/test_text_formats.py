# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_text_formats import FORMAT_INDEX, decode_literal, directives, literal_expression, inventory
from audit_source_structure import parser
from audit_system_ownership import analyze

class TextFormats(unittest.TestCase):
    def test_adjacent_literals_and_escapes(self):
        engine=parser()
        value=literal_expression(r'L"\x25" /*separator*/ L"I64d\n"',engine)
        self.assertEqual(value,'%I64d\n')
        self.assertEqual(literal_expression(r'u"\045s/\u0025d"',engine),'%s/%d')
        self.assertEqual(literal_expression('"a" "b"',engine),'ab')

    def test_dynamic_macro_raw_and_cast_remain_unknown(self):
        for expression in ['GetText("ID")','FORMAT_NAME','R"(%s)"','(const wchar_t*)"%s"','"%s" MACRO']:
            self.assertIsNone(literal_expression(expression,parser()))
        self.assertIsNone(decode_literal(r'"\x"'))
        self.assertIsNone(decode_literal(r'"\UFFFFFFFF"'))
        self.assertIsNone(decode_literal(r'"\q"'))
        self.assertIsNone(literal_expression(r'"\x125s"',parser()))
        self.assertIsNone(literal_expression(r'"\777"',parser()))
        self.assertIsNone(literal_expression(r'L"\x10025s"',parser()))
        self.assertEqual(literal_expression(r'L"\x125s"',parser()),'\u0125s')

    def test_legacy_directives_width_precision_and_lengths(self):
        rows,unknown=directives('%% %*.*ls %I64d %I32u %hs %hhu %+#08.2f %n %Z')
        self.assertFalse(unknown)
        self.assertEqual([r['conversion'] for r in rows],['%','s','d','u','s','u','f','n','Z'])
        self.assertEqual(rows[1]['width'],'*');self.assertEqual(rows[1]['precision'],'*')
        self.assertEqual(rows[2]['length'],'I64');self.assertEqual(rows[5]['length'],'hh')

    def test_unrecognized_and_positional_sequences_are_retained(self):
        _,unknown=directives('%1$d %Q tail%')
        self.assertEqual(len(unknown),3)
        self.assertEqual(unknown[0]['suffix'],'%1$d %Q tail%')

    def test_api_position_candidates(self):
        self.assertEqual(FORMAT_INDEX['format'],0)
        self.assertEqual(FORMAT_INDEX['swprintf'],1)
        self.assertEqual(FORMAT_INDEX['_snwprintf'],2)
        self.assertEqual(FORMAT_INDEX['fwprintf'],1)

    def test_nested_calls_guards_comments_and_strings(self):
        data=b'#if LOCALIZED\nvoid f(){/*x.format("%n");*/ const char*s="printf()"; result.format(GetText("ID"), value); _snwprintf(dst,32,L"%ls",text);}\n#endif'
        _,rows,_=analyze(data,parser(),set(FORMAT_INDEX))
        self.assertEqual([r['route'] for r in rows],['format','_snwprintf'])
        self.assertEqual(rows[0]['argument_node_candidates'][0],'GetText("ID")')
        self.assertEqual(rows[0]['guards'][0]['condition'],'LOCALIZED')
        self.assertEqual(rows[1]['receiver_binding'],'unresolved')

    def test_lambda_and_parser_recovery(self):
        _,rows,_=analyze(b'void f(){auto fn=[](){text.format(L"%d",7);};}',parser(),set(FORMAT_INDEX))
        self.assertEqual(rows[0]['callable']['kind'],'lambda_expression')
        _,_,errors=analyze(b'void broken( ;',parser(),set(FORMAT_INDEX))
        self.assertTrue(errors)

    def test_unpinned_and_symlink_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'x.cpp').write_text('void f(){}')
            with self.assertRaisesRegex(ValueError,'pinned baseline'):inventory(root)
            (root/'link.cpp').symlink_to(root/'x.cpp')
            with self.assertRaisesRegex(ValueError,'symlink'):inventory(root)
            (root/'alias').symlink_to(root,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'symlink'):inventory(root/'alias')
if __name__=='__main__':unittest.main()
