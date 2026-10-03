# SPDX-License-Identifier: GPL-3.0-or-later
import tempfile
from pathlib import Path
import unittest
from tools.audit_original_projects import parse_dsp, parse_dsw, inventory

class OriginalProjectsTests(unittest.TestCase):
    def fixture(self,body):
        return '# Name "P - Debug"\n# Name "P - Release"\n'+body
    def test_exclusion_is_configuration_specific(self):
        parsed=parse_dsp(self.fixture('SOURCE=.\\a.cpp\n!IF "$(CFG)" == "P - Debug"\n# PROP Exclude_From_Build 1\n!ENDIF\n# End Source File\n'))
        row=parsed['rows'][0]
        self.assertTrue(row['configurations']['P - Debug']['excluded'])
        self.assertFalse(row['configurations']['P - Release']['excluded'])
    def test_unknown_branch_not_silently_included(self):
        parsed=parse_dsp(self.fixture('SOURCE=a.cpp\n!IF "$(PLATFORM)" == "other"\n# PROP Exclude_From_Build 1\n!ENDIF\n'))
        self.assertIsNone(parsed['rows'][0]['configurations']['P - Debug']['excluded'])
        self.assertEqual(len(parsed['unresolved_conditions']),2)
    def test_nested_else_chain(self):
        parsed=parse_dsp(self.fixture('!IF "$(CFG)" == "P - Debug"\nSOURCE=debug.cpp\n!ELSEIF "$(CFG)" == "P - Release"\nSOURCE=release.cpp\n!ENDIF\n'))
        self.assertFalse(parsed['rows'][0]['configurations']['P - Release']['present'])
        self.assertTrue(parsed['rows'][1]['configurations']['P - Release']['present'])
    def test_unbalanced_condition_is_fatal(self):
        for text in ['!ENDIF','!ELSEIF "$(CFG)" == "P - Debug"','!IF "$(CFG)" == "P - Debug"']:
            with self.subTest(text=text), self.assertRaises(ValueError): parse_dsp(self.fixture(text))
    def test_custom_build_input_is_not_a_source_declaration(self):
        parsed=parse_dsp(self.fixture('SOURCE=real.cpp\n# Begin Custom Build\nSOURCE=$(InputPath)\n# End Custom Build\n# End Source File\n'))
        self.assertEqual(len(parsed['rows']),1)
        self.assertEqual(parsed['rows'][0]['source_expression'],'real.cpp')
        self.assertEqual(len(parsed['build_hook_candidates']),1)
    def test_workspace_dependencies(self):
        rows=parse_dsw('Project: "RTS"=.\\RTS.dsp - Package Owner=<4>\n Project_Dep_Name Engine\nProject: "Engine"=.\\E\\e.dsp - Package Owner=<4>\n')
        self.assertEqual(rows[0]['dependencies'],['Engine'])
        self.assertEqual(rows[1]['dependencies'],[])
    def test_case_collision_missing_and_unprojected_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'p.dsp').write_text(self.fixture('SOURCE=a.cpp\n# End Source File\nSOURCE=missing.cpp\n'))
            (root/'A.cpp').write_text(''); (root/'a.cpp').write_text(''); (root/'orphan.cpp').write_text('')
            result=inventory(root)
            self.assertEqual(result['summary']['source_reference_resolutions'],{'case_collision':1,'missing':1})
            self.assertEqual(result['summary']['units_without_original_project_reference'],1)
if __name__=='__main__': unittest.main()
