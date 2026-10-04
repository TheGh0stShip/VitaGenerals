// SPDX-License-Identifier: GPL-3.0-or-later
#include "dx8wrapper.h"
#include "dx8webbrowser.h"
#include "dx8renderer.h"
#include "render2d.h"
#include "rddesc.h"
#include "registry.h"
static_assert(sizeof(WCHAR) == 2, "Original W3D UTF-16 code unit");
static_assert(sizeof(LONG) == 4, "Browser option word must remain 32-bit");
#undef NDEBUG
#include <assert.h>
#include <stdint.h>
#include <string.h>
int main() {
 assert(DX8Wrapper::Convert_Color(Vector4(1,0,0,1))==0xffff0000U);
 assert(DX8Wrapper::Convert_Color(Vector4(0,1,0,1))==0xff00ff00U);
 assert(DX8Wrapper::Convert_Color(Vector4(0,0,1,1))==0xff0000ffU);
 assert(DX8Wrapper::Convert_Color(Vector4(.5f,.5f,.5f,.5f))==0x7f7f7f7fU);
 uint32_t bits[4]={0x80000000U,0x7fc00000U,0xffc00000U,0x40000000U};
 Vector4 v; memcpy(&v,bits,sizeof(bits)); DX8Wrapper::Clamp_Color(v);
 memcpy(bits,&v,sizeof(bits)); assert(bits[0]==0 && bits[1]==0x3f800000U && bits[2]==0 && bits[3]==0x3f800000U);
 return 0;
}
