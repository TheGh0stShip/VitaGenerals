# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_system_ownership import analyze, candidate_graph
from audit_source_structure import parser

class SystemOwnership(unittest.TestCase):
    def scan(self, text):
        return analyze(text.encode(), parser())
    def test_namespace_ambiguity_and_independent_seeds(self):
        classes, _, _ = self.scan('class Snapshot {}; class SubsystemInterface {}; namespace A {class M: Snapshot {}; } namespace B {class M: SubsystemInterface {}; } class D: M {}; class E: A::M {};')
        closure = candidate_graph(classes)
        d = next(c for c in classes if c['name'] == 'D')
        e = next(c for c in classes if c['name'] == 'E')
        self.assertTrue(d['bases'][0]['ambiguous'])
        self.assertEqual(d['seed_candidates'], ['Snapshot', 'SubsystemInterface'])
        self.assertEqual(e['seed_candidates'], ['Snapshot'])
        self.assertEqual(len(closure['Snapshot']), 4)
    def test_explicit_global_qualification(self):
        classes, _, _ = self.scan("class Snapshot {}; namespace N {class Snapshot {}; } class D: ::Snapshot {};")
        candidate_graph(classes)
        self.assertEqual(classes[2]["bases"][0]["class_candidates"], [0])
    def test_template_commas_do_not_create_base_edges(self):
        classes, _, _ = self.scan('class Snapshot {}; class C: Foo<int, Snapshot, X> {};')
        candidate_graph(classes)
        self.assertIsNone(classes[1]['bases'][0]['simple_name_candidate'])
        self.assertEqual(classes[1]['seed_candidates'], [])
    def test_registration_and_lambda_owner(self):
        _, calls, _ = self.scan('void f(){addSnapshotBlock("a", p, SAVE); auto l=[](){p->xfer(q);};}')
        self.assertEqual(calls[0]['argument_node_candidates'], ['"a"', 'p', 'SAVE'])
        self.assertEqual(calls[1]['callable']['kind'], 'lambda_expression')
        self.assertEqual(calls[0]['receiver_binding'], 'unresolved')
    def test_comments_strings_and_conditional_provenance(self):
        _, calls, _ = self.scan('#ifndef A\nvoid f(){/* p->reset(); */ const char *s="xfer()"; p->reset();}\n#endif\n')
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['guards'][0]['directive'], 'ifndef')
        self.assertEqual(calls[0]['guards'][0]['reachability'], 'unknown')
    def test_forward_declarations_are_not_seed_definitions(self):
        classes, _, _ = self.scan("class Snapshot; class Snapshot {}; class D: Snapshot {};")
        closure = candidate_graph(classes)
        self.assertFalse(classes[0]["has_body"])
        self.assertEqual(closure["Snapshot"], [1, 2])
        self.assertTrue(classes[2]["bases"][0]["ambiguous"])
    def test_cycles_terminate_without_inventing_membership(self):
        classes, _, _ = self.scan('class A: B {}; class B: A {}; class Snapshot {};')
        closure = candidate_graph(classes)
        self.assertEqual(closure['Snapshot'], [2])
    def test_base_comments_are_not_type_candidates(self):
        classes, _, _ = self.scan("class D: public /*comment*/ Snapshot {};")
        self.assertEqual([b["spelling"] for b in classes[0]["bases"]], ["Snapshot"])
    def test_parse_recoveries_retained(self):
        _, _, errors = self.scan('class Broken: { void f( ;')
        self.assertTrue(errors)
if __name__ == '__main__':
    unittest.main()
