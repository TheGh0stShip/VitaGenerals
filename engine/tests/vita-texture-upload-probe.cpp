// SPDX-License-Identifier: GPL-3.0-or-later
#include "VitaW3DTextureUpload.h"
#include <vitaGL.h>
#include <assert.h>
#include <string.h>
#include <vector>
static GLuint binding = 19;
static GLint alignment = 8;
static GLenum error = 0;
static bool fail = false;
static unsigned images = 0, updates = 0, deletes = 0, invalidations = 0;
static std::vector<uint8_t> captured;
void glGetIntegerv(GLenum name, GLint *p) { *p = name == GL_UNPACK_ALIGNMENT ? alignment : binding; }
GLenum glGetError() { GLenum result = error; error = 0; return result; }
void glGenTextures(GLint, GLuint *p) { *p = 42; }
void glDeleteTextures(GLint, const GLuint *p) { assert(*p == 42); ++deletes; }
void glBindTexture(GLenum, GLuint p) { binding = p; }
void glPixelStorei(GLenum, GLint p) { alignment = p; }
void glTexParameteri(GLenum, GLenum, GLint) {}
static void Capture(GLint w, GLint h, const void *p) {
  assert(binding == 42 && alignment == 1);
  const uint8_t *bytes = static_cast<const uint8_t *>(p);
  captured.assign(bytes, bytes + w * h * 4);
  if (fail) error = GL_OUT_OF_MEMORY;
}
void glTexImage2D(GLenum, GLint, GLint, GLint w, GLint h, GLint, GLenum, GLenum, const void *p) { ++images; Capture(w,h,p); }
void glTexSubImage2D(GLenum, GLint, GLint, GLint, GLint w, GLint h, GLenum, GLenum, const void *p) { ++updates; Capture(w,h,p); }
static void Invalidate(void *) { ++invalidations; }
int main() {
  GeneralsVitaTextureUploadContext context = {Invalidate, NULL};
  const D3DFORMAT formats[] = {D3DFMT_X8R8G8B8,D3DFMT_R8G8B8,D3DFMT_R5G6B5,D3DFMT_X1R5G5B5};
  for (unsigned f = 0; f < 4; ++f) {
    uint8_t pixels[32]; memset(pixels, 0xa5, sizeof(pixels));
    unsigned bpp = f == 0 ? 4 : f == 1 ? 3 : 2;
    for (unsigned y = 0; y < 2; ++y) {
      for (unsigned x = 0; x < 3; ++x) {
        uint8_t *p = pixels + y * 16 + x * bpp;
        if (bpp >= 3) {
          p[0] = x == 2 ? 255 : 0;
          p[1] = x == 1 ? 255 : 0;
          p[2] = x == 0 ? 255 : 0;
        } else {
          const uint16_t value = x == 0 ? (f == 2 ? 0xf800 : 0x7c00) :
                                 x == 1 ? (f == 2 ? 0x07e0 : 0x03e0) : 0x001f;
          p[0] = value & 255; p[1] = value >> 8;
        }
      }
    }
    uint32_t native = 0;
    assert(GeneralsVitaUploadTexture(&context,&native,3,2,formats[f],pixels,16)==D3D_OK);
    assert(native==42 && binding==19 && alignment==8);
    const uint8_t expected[] = {255,0,0,255,0,255,0,255,0,0,255,255,
                                255,0,0,255,0,255,0,255,0,0,255,255};
    assert(captured.size()==sizeof(expected) &&
           memcmp(captured.data(),expected,sizeof(expected))==0);
    assert(GeneralsVitaUploadTexture(&context,&native,3,2,formats[f],pixels,16)==D3D_OK);
    assert(binding==19 && alignment==8);
    GeneralsVitaReleaseTexture(&context,native);
  }
  assert(images==4 && updates==4 && deletes==4 && invalidations==12);
  uint32_t native = 0; uint8_t pixels[4] = {};
  fail=true;
  assert(GeneralsVitaUploadTexture(&context,&native,1,1,D3DFMT_X8R8G8B8,pixels,4)==D3DERR_OUTOFVIDEOMEMORY);
  assert(native==0 && deletes==5 && binding==19 && alignment==8);
  assert(GeneralsVitaUploadTexture(&context,&native,1,1,D3DFMT_X8R8G8B8,pixels,3)==D3DERR_INVALIDCALL);
  assert(images==5);
  // A failed replacement must retain the existing handle for later retry.
  native = 42;
  assert(GeneralsVitaUploadTexture(&context,&native,1,1,D3DFMT_X8R8G8B8,pixels,4)==D3DERR_OUTOFVIDEOMEMORY);
  assert(native==42 && deletes==5 && binding==19 && alignment==8);
  fail = false;
  assert(GeneralsVitaUploadTexture(&context,&native,1,1,D3DFMT_X8R8G8B8,pixels,4)==D3D_OK);
  const uint8_t black[] = {0,0,0,255};
  assert(captured.size()==4 && memcmp(captured.data(),black,4)==0);
  GeneralsVitaReleaseTexture(&context,native);
  assert(deletes==6);

  // Exercise the actual surface owner and upload/release callbacks together.
  IDirect3DTexture8 *texture = GeneralsVitaCreateTexture(
      3, 2, D3DFMT_R8G8B8, 16, GeneralsVitaUploadTexture, &context,
      GeneralsVitaReleaseTexture);
  assert(texture != NULL);
  IDirect3DSurface8 *surface = NULL;
  assert(texture->GetSurfaceLevel(0, &surface) == D3D_OK);
  D3DLOCKED_RECT locked = {};
  assert(surface->LockRect(&locked, NULL, 0) == D3D_OK);
  assert(locked.Pitch == 16);
  memset(locked.pBits, 0, 32);
  static_cast<uint8_t *>(locked.pBits)[2] = 255;
  assert(surface->UnlockRect() == D3D_OK);
  assert(texture->GetNativeTexture() == 42 && captured[0] == 255);
  unsigned before_release = deletes;
  assert(texture->Release() == 0);
  assert(deletes == before_release + 1);
  assert(surface->LockRect(&locked, NULL, D3DLOCK_READONLY) == D3D_OK);
  assert(surface->UnlockRect() == D3D_OK);
  assert(surface->Release() == 0);
  assert(deletes == before_release + 1);
}
