# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_renderer_boundary import scan,category

class RendererBoundary(unittest.TestCase):
    def test_comments_literals_and_boundaries(self):
        rows=scan('// D3DFMT_FAKE\n"D3DRS_FAKE"; D3DFMT_DXT1; prefixD3DFMT_FAKE;')
        self.assertEqual([(r['symbol'],r['line']) for r in rows],[('D3DFMT_DXT1',2)])
    def test_wrapper_and_device_macros(self):
        rows=scan('DX8Wrapper :: Draw_Triangles(x); DX8CALL(DrawIndexedPrimitive(x)); DX8CALL_HRES(Reset(x),hr); DX8CALL_D3D(GetDeviceCaps(x));')
        self.assertEqual({r['symbol'] for r in rows},{'DX8Wrapper::Draw_Triangles','DX8CALL::DrawIndexedPrimitive','DX8CALL_HRES::Reset','DX8CALL_D3D::GetDeviceCaps'})
    def test_categories(self):
        for name,kind in [('D3DTSS_COLOROP','texture_stage_state'),('D3DRS_ZENABLE','render_state'),('D3DFVF_XYZ','vertex_layout'),('D3DXMatrixInverse','d3dx_helper'),('IDirect3DDevice8','device_interface'),('CLASSID_MESH','render_class_id')]:
            self.assertEqual(category(name),kind)
    def test_repeated_sites_retained(self):
        self.assertEqual(len(scan('D3DRS_ZENABLE; D3DRS_ZENABLE;')),2)
if __name__=='__main__':unittest.main()
