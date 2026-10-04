# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_movie_routes import ROUTES, inventory
from audit_system_ownership import analyze
from audit_source_structure import parser

class MovieRoutes(unittest.TestCase):
    def test_wrappers_and_dynamic_arguments(self):
        _,rows,_=analyze(b'void f(){ display->playLogoMovie("Logo",5000,3000); PlayMovieAndBlock(campaign->getFinalVictoryMovie()); }',parser(),ROUTES)
        self.assertEqual([r['route'] for r in rows],['playLogoMovie','PlayMovieAndBlock'])
        self.assertEqual(rows[1]['argument_node_candidates'],['campaign->getFinalVictoryMovie()'])
        self.assertEqual(rows[0]['receiver_binding'],'unresolved')
    def test_unrelated_open_load_retained(self):
        _,rows,_=analyze(b'void f(){ files.open(path); ini.load(config); TheVideoPlayer->open(title); }',parser(),ROUTES)
        self.assertEqual([r['call'] for r in rows],['files.open','ini.load','TheVideoPlayer->open'])
    def test_comments_strings_and_guard(self):
        _,rows,_=analyze(b'#if MOVIES\nvoid f(){/* BinkOpen(x); */ const char*s="playMovie()"; BinkOpen(path, flags);}\n#endif',parser(),ROUTES)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['argument_node_candidates'],['path','flags'])
        self.assertEqual(rows[0]['guards'][0]['condition'],'MOVIES')
    def test_lambda_and_errors_retained(self):
        _,rows,_=analyze(b'void f(){auto cb=[](){ ui->playCameoMovie(title); };}',parser(),ROUTES)
        self.assertEqual(rows[0]['callable']['kind'],'lambda_expression')
        _,_,errors=analyze(b'void broken( ;',parser(),ROUTES)
        self.assertTrue(errors)
    def test_symlink_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'real.cpp').write_text('void f(){}');(root/'link.cpp').symlink_to(root/'real.cpp')
            with self.assertRaisesRegex(ValueError,'symlink'):inventory(root)
    def test_unpinned_input_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'x.cpp').write_text('void f(){}')
            with self.assertRaisesRegex(ValueError,'pinned baseline'):inventory(root)
if __name__=='__main__':unittest.main()
