# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_runtime_providers import link_options,provider_matches,workspace_provider

class RuntimeProviders(unittest.TestCase):
    def test_excluded_default_is_not_input(self):
        r=link_options('# ADD LINK32 game.lib /nodefaultlib:"debug.lib" /out:"RTS.exe"')
        self.assertEqual(r['library_inputs'],['game.lib'])
        self.assertEqual(r['excluded_default_libraries'],['debug.lib'])
        self.assertEqual(r['outputs'],['RTS.exe'])
    def test_quoted_paths_and_import_library(self):
        r=link_options('# ADD LINK32 "some dir/a.lib" /out:"run dir/a.dll" /implib:"lib dir/a.lib" /libpath:"library dir"')
        self.assertEqual(r['library_inputs'],['some dir/a.lib'])
        self.assertEqual(r['import_libraries'],['lib dir/a.lib'])
        self.assertEqual(r['outputs'],['run dir/a.dll'])
        self.assertEqual(r['library_search_paths'],['library dir'])
    def test_case_and_ambiguous_providers_preserved(self):
        providers=[{'output':'Lib/WWMath.lib','project':'a'},{'output':'Other\\wwmath.LIB','project':'b'}]
        self.assertEqual(provider_matches('WWMATH.lib',providers),providers)
    def test_workspace_uses_resolved_case_and_rejects_ambiguity(self):
        project={'path':'Libraries/Benchmark.dsp'}
        row={'resolution':'found','path':'LIBRARIES/Benchmark.dsp','candidates':['Libraries/Benchmark.dsp']}
        self.assertEqual(workspace_provider(row,[project]),project)
        row['resolution']='case_collision'
        self.assertIsNone(workspace_provider(row,[project]))
    def test_base_directives_not_silently_accepted(self):
        with self.assertRaises(ValueError):link_options('# ADD BASE LINK32 a.lib')
if __name__=='__main__':unittest.main()
