# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_ini_dispatch import table_rows,definitions

class IniDispatch(unittest.TestCase):
    def test_tokens_and_comments(self):
        rows=table_rows('static X theTypeTable[] = { /* ignored */ {"Object", INI::parseObject}, {NULL,NULL}, };')
        self.assertEqual([(r['token'],r['handler']) for r in rows],[('Object','INI::parseObject')])
    def test_invalid_tables(self):
        for body in ['{"A",P}', '{NULL,P}', '{NULL,NULL},{"A",P}', '{"A",P},{"A",P},{NULL,NULL}', '{"A",P(x)},{NULL,NULL}']:
            with self.assertRaises(ValueError):table_rows('X theTypeTable[] = {'+body+'};')
    def test_definition_not_declaration_or_literal(self):
        text='void INI::parse(INI*); "INI::parse(){}"; /* INI::parse(){} */\nvoid INI::parse(INI* ini) { }'
        self.assertEqual(definitions(text,'INI::parse'),[2])
    def test_qualified_boundaries(self):
        self.assertEqual(definitions('void Other::INI::parse() {}','INI::parse'),[])
if __name__=='__main__':unittest.main()
