# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ini_declarations import scan

class IniDeclarations(unittest.TestCase):
    def test_case_comments_duplicates_and_offsets(self):
        data=b'; Object Hidden\r\nObject A\r\nObject A; comment\nObject a\nobject ignored\n'
        rows,directives,issues=scan(data)
        self.assertEqual([r['name'] for r in rows],['A','A','a'])
        self.assertEqual([r['offset'] for r in rows],[17,27,45])
        self.assertTrue(all(r['scope']=='unresolved' for r in rows))
        self.assertFalse(directives or issues)
    def test_controls_are_separators_not_new_lines(self):
        for value in range(1,32):
            if value==10:continue
            with self.subTest(value=value):
                rows,_,_=scan(b'Object'+bytes([value])+b'A\n')
                self.assertEqual((rows[0]['name'],rows[0]['line']),('A',1))
        self.assertEqual(scan(b'Object=A\n')[0][0]['name'],'A')
    def test_nul_and_line_size_are_explicit_issues(self):
        rows,_,issues=scan(b'Object A\0Object B\n')
        self.assertEqual(rows[0]['name'],'A')
        self.assertEqual(issues,[{'line':1,'reason':'embedded_nul'}])
        self.assertFalse(scan(b'Object '+b'A'*1020)[2])
        self.assertEqual(scan(b'Object '+b'A'*1021)[2][0]['reason'],'original_line_buffer_boundary')
    def test_reskin_missing_name_and_extra_tokens(self):
        rows,_,issues=scan(b'ObjectReskin New Base Extra\nObject\nObjectReskin New\n')
        self.assertEqual((rows[0]['reskin_from'],rows[0]['extra_tokens']),('Base',['Extra']))
        self.assertIsNone(rows[1]['name'])
        self.assertIsNone(rows[2]['reskin_from'])
        self.assertEqual([i['line'] for i in issues],[2,3])
    def test_custom_named_kinds_and_directives(self):
        rows,directives,issues=scan(b'#include "file.ini"\nAudioEvent S\nVideo V\nScience X\nObject A\n',('AudioEvent','Video','Science'))
        self.assertEqual([r['kind'] for r in rows],['AudioEvent','Video','Science'])
        self.assertEqual(directives[0]['tokens'],['#include','"file.ini"'])
        self.assertEqual(directives[0]['semantics'],'unresolved')
        self.assertFalse(issues)
    def test_quotes_and_nested_scope_not_interpreted(self):
        rows,_,_=scan(b'Object "A B"\n  Object Nested\nEnd\n')
        self.assertEqual(rows[0]['name'],'"A')
        self.assertEqual(rows[0]['extra_tokens'],['B"'])
        self.assertEqual(rows[1]['scope'],'unresolved')

if __name__=='__main__':unittest.main()
