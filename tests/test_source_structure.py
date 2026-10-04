# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_source_structure import analyze,parser

class SourceStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.engine=parser()
    def scan(self,text):return analyze(text.encode('latin1'),self.engine)
    def test_inline_class_and_constant_returns(self):
        r=self.scan('class X { bool f() { if (x) return false; return true; } };')
        self.assertFalse(r['parse_has_error']);self.assertEqual(len(r['functions']),1)
        self.assertEqual(r['functions'][0]['class_context'],['X'])
        self.assertEqual([v['literal_candidate'] for v in r['returns']],['false','true'])
    def test_lambda_owns_its_returns(self):
        r=self.scan('int f(){ auto fn=[](){return 1;}; return fn(); }')
        self.assertEqual([v['function_index'] for v in r['returns']],[1,0])
        self.assertEqual(r['functions'][1]['kind'],'lambda_expression')
    def test_empty_and_single_return_are_candidates(self):
        r=self.scan('void f(){ /* nothing */ } bool g(){ return false; }')
        self.assertTrue(r['functions'][0]['body_empty_candidate'])
        self.assertTrue(r['functions'][1]['sole_return_candidate'])
        self.assertFalse(r['functions'][1]['behavior_verified'])
    def test_guard_branches_not_evaluated(self):
        r=self.scan('#ifdef VITA\nvoid f(){}\n#else\nvoid g(){}\n#endif')
        self.assertEqual(len(r['functions']),2)
        self.assertEqual(len(r['guards']),2)
        self.assertEqual(r['guards'][0]['directive'],'#ifdef')
        self.assertTrue(all(g['reachability']=='unknown' for g in r['guards']))
    def test_ifndef_preserved(self):
        r=self.scan('#ifndef X\nvoid f(){}\n#endif')
        self.assertEqual(r['guards'][0]['directive'],'#ifndef')
    def test_nested_guard_ancestry(self):
        r=self.scan('#if X\n#ifndef Y\nvoid f(){}\n#elif Z\nvoid g(){}\n#else\nvoid h(){}\n#endif\n#endif')
        self.assertEqual([g['directive'] for g in r['guards']],['#if','#ifndef','#elif','#else'])
        self.assertTrue(all(f['guard_indices'][0]==0 for f in r['functions']))
    def test_default_lambda_and_extern_c(self):
        r=self.scan('extern "C" { int f(int n=[](){return 2;}()){return n;} }')
        self.assertFalse(r['parse_has_error'])
        self.assertEqual([v['function_index'] for v in r['returns']],[1,0])
    def test_parse_recovery_not_silenced(self):
        r=self.scan('void broken( { return false;')
        self.assertTrue(r['parse_has_error']);self.assertTrue(r['parse_recoveries'])
    def test_legacy_encoding_and_raw_literal(self):
        r=self.scan('// caf\xe9\nvoid f(){ auto x=R"(return false;)"; return; }')
        self.assertFalse(r['parse_has_error']);self.assertEqual(r['returns'][0]['line'],2)
        self.assertEqual(len(r['returns']),1);self.assertTrue(r['returns'][0]['void_return'])
if __name__=='__main__':unittest.main()
