// SPDX-License-Identifier: GPL-3.0-or-later
#include "VitaW3DTextureUpload.h"
#include <vitaGL.h>
#include <limits.h>
#include <new>

namespace {
void Invalidate(void *opaque) {
  GeneralsVitaTextureUploadContext *context =
      static_cast<GeneralsVitaTextureUploadContext *>(opaque);
  if (context && context->invalidate_texture_cache)
    context->invalidate_texture_cache(context->context);
}
}

HRESULT GeneralsVitaUploadTexture(void *context, uint32_t *native, UINT width,
                                 UINT height, D3DFORMAT format,
                                 const void *pixels, UINT pitch) {
  UINT bpp = format == D3DFMT_X8R8G8B8 ? 4U :
             format == D3DFMT_R8G8B8 ? 3U :
             (format == D3DFMT_R5G6B5 || format == D3DFMT_X1R5G5B5) ? 2U : 0U;
  if (!native || !pixels || !bpp || !width || !height ||
      width > (UINT)INT_MAX || height > (UINT)INT_MAX ||
      width > UINT32_MAX / 4U || pitch < width * bpp ||
      height > UINT32_MAX / (width * 4U) || height > UINT32_MAX / pitch)
    return D3DERR_INVALIDCALL;
  uint8_t *rgba = new (std::nothrow) uint8_t[width * height * 4U];
  if (!rgba) return D3DERR_OUTOFVIDEOMEMORY;
  const uint8_t *source = static_cast<const uint8_t *>(pixels);
  for (UINT y = 0; y < height; ++y) {
    for (UINT x = 0; x < width; ++x) {
      const uint8_t *p = source + (size_t)y * pitch + (size_t)x * bpp;
      uint8_t *q = rgba + ((size_t)y * width + x) * 4U;
      if (bpp >= 3U) {
        q[0] = p[2]; q[1] = p[1]; q[2] = p[0];
      } else {
        const uint32_t value = p[0] | ((uint32_t)p[1] << 8U);
        const bool rgb565 = format == D3DFMT_R5G6B5;
        q[0] = (uint8_t)(((value >> (rgb565 ? 11U : 10U)) & 31U) * 255U / 31U);
        q[1] = (uint8_t)(((value >> 5U) & (rgb565 ? 63U : 31U)) *
                         255U / (rgb565 ? 63U : 31U));
        q[2] = (uint8_t)((value & 31U) * 255U / 31U);
      }
      q[3] = 255U;
    }
  }
  GLint binding = 0, alignment = 0;
  glGetIntegerv(GL_TEXTURE_BINDING_2D, &binding);
  glGetIntegerv(GL_UNPACK_ALIGNMENT, &alignment);
  if (glGetError() != GL_NO_ERROR) { delete[] rgba; return D3DERR_INVALIDCALL; }
  GLuint texture = *native;
  const bool created = texture == 0U;
  if (created) glGenTextures(1, &texture);
  if (!texture) { delete[] rgba; return D3DERR_OUTOFVIDEOMEMORY; }
  glBindTexture(GL_TEXTURE_2D, texture);
  glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
  if (created) {
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, rgba);
  } else {
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height,
                    GL_RGBA, GL_UNSIGNED_BYTE, rgba);
  }
  const GLenum error = glGetError();
  if (created && error != GL_NO_ERROR) glDeleteTextures(1, &texture);
  glPixelStorei(GL_UNPACK_ALIGNMENT, alignment);
  glBindTexture(GL_TEXTURE_2D, (GLuint)binding);
  Invalidate(context);
  delete[] rgba;
  if (error != GL_NO_ERROR) return D3DERR_OUTOFVIDEOMEMORY;
  *native = texture;
  return D3D_OK;
}

void GeneralsVitaReleaseTexture(void *context, uint32_t native) {
  if (native) {
    const GLuint texture = native;
    glDeleteTextures(1, &texture);
    Invalidate(context);
  }
}
