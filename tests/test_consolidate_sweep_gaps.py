# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import json
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from consolidate_sweep_gaps import validate,pointer,consolidate,markdown

class Consolidation(unittest.TestCase):
    def setUp(self):
        self.lock={'upstream_commit':'pin','tree_sha256':'tree'}
        self.reports={'a':{'upstream_commit':'pin','source_tree_sha256':'tree','rows':[{'value':3}]}}
        self.registry={'reports':['a'],'findings':[{'id':'ONE','severity':'blocking','kind':'evidence_gap','status':'open','depends_on':[],'evidence':[{'report':'a','pointer':'/rows/0/value'}],'closure_evidence':'Verify original route.'}],'coverage_obligations':[{'scope':'game','status':'partial'}]}
    def test_reference_resolution(self):
        self.assertEqual(pointer(self.reports['a'],'/rows/0/value'),3)
        self.assertEqual(validate(self.registry,self.reports,self.lock),['ONE'])
    def test_mixed_pin_rejected(self):
        self.reports['a']['source_tree_sha256']='other'
        with self.assertRaises(ValueError):validate(self.registry,self.reports,self.lock)
    def test_duplicate_identity_rejected(self):
        self.registry['findings'].append(copy.deepcopy(self.registry['findings'][0]))
        with self.assertRaises(ValueError):validate(self.registry,self.reports,self.lock)
    def test_cycle_and_unknown_dependency_rejected(self):
        for dependency in ['ONE','UNKNOWN']:
            self.registry['findings'][0]['depends_on']=[dependency]
            with self.assertRaises(ValueError):validate(self.registry,self.reports,self.lock)
    def test_missing_evidence_rejected(self):
        self.registry['findings'][0]['evidence'][0]['pointer']='/missing'
        with self.assertRaises(KeyError):validate(self.registry,self.reports,self.lock)
    def test_unsupported_completion_claim_rejected(self):
        self.registry['coverage_obligations'][0]['status']='complete'
        with self.assertRaises(ValueError):validate(self.registry,self.reports,self.lock)
    def test_actual_ledger_is_deterministic_and_not_defect_count(self):
        result=consolidate(Path(__file__).resolve().parents[1])
        self.assertFalse(result['complete']);self.assertFalse(result['hardware_acceptance_established'])
        self.assertEqual(result['summary']['parent_evidence_gaps'],len(result['findings']))
        root=Path(__file__).resolve().parents[1]
        self.assertEqual(result,json.loads((root/'reports/generated/consolidated-gaps.json').read_text()))
        self.assertEqual(markdown(result),(root/'docs/PORT_GAPS.md').read_text())
if __name__=='__main__':unittest.main()
