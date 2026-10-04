// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "d3d8.h"

// Owned by the renderer; must outlive textures created with these callbacks.
struct GeneralsVitaTextureUploadContext {
  void (*invalidate_texture_cache)(void *context);
  void *context;
};
HRESULT GeneralsVitaUploadTexture(void *, uint32_t *, UINT, UINT,
                                 D3DFORMAT, const void *, UINT);
void GeneralsVitaReleaseTexture(void *, uint32_t);
