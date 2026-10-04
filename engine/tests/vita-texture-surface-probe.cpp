// SPDX-License-Identifier: GPL-3.0-or-later
#include "d3d8.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

struct UploadRecord {
  unsigned calls;
  UINT width;
  UINT height;
  UINT pitch;
  D3DFORMAT format;
  uint8_t first;
  bool fail;
};

struct ReentrantRecord {
  IDirect3DTexture8 *texture;
  unsigned calls;
};

static HRESULT RecordUpload(void *opaque, uint32_t *native_texture, UINT width,
                            UINT height, D3DFORMAT format, const void *pixels,
                            UINT pitch) {
  UploadRecord *record = static_cast<UploadRecord *>(opaque);
  ++record->calls;
  record->width = width;
  record->height = height;
  record->pitch = pitch;
  record->format = format;
  record->first = static_cast<const uint8_t *>(pixels)[0];
  if (record->fail) return D3DERR_OUTOFVIDEOMEMORY;
  *native_texture = 0x1234U;
  return D3D_OK;
}

static HRESULT ReleaseTextureDuringUpload(void *opaque, uint32_t *native_texture,
                                          UINT, UINT, D3DFORMAT, const void *,
                                          UINT) {
  ReentrantRecord *record = static_cast<ReentrantRecord *>(opaque);
  ++record->calls;
  *native_texture = 7U;
  record->texture->Release();
  record->texture = NULL;
  return D3D_OK;
}

static UINT BytesPerPixel(D3DFORMAT format) {
  if (format == D3DFMT_X8R8G8B8) return 4U;
  if (format == D3DFMT_R8G8B8) return 3U;
  return 2U;
}

static void Exercise(D3DFORMAT format) {
  UploadRecord record = {};
  IDirect3DTexture8 *texture =
      GeneralsVitaCreateTexture(5U, 3U, format, 16U, RecordUpload, &record);
  assert(texture != NULL);
  assert(texture->GetLevelCount() == 1U);

  IDirect3DSurface8 *surface = NULL;
  assert(texture->GetSurfaceLevel(0U, &surface) == D3D_OK);
  assert(surface != NULL);
  D3DSURFACE_DESC description = {};
  assert(surface->GetDesc(&description) == D3D_OK);
  assert(description.Width == 5U && description.Height == 3U);
  assert(description.Format == format);
  const UINT row_bytes = 5U * BytesPerPixel(format);
  assert(surface->GetPitch() >= row_bytes);
  assert((surface->GetPitch() & 15U) == 0U);
  assert(surface->GetStorageSize() == surface->GetPitch() * 3U);

  D3DLOCKED_RECT locked = {};
  assert(surface->LockRect(&locked, NULL, 0U) == D3D_OK);
  assert(surface->LockRect(&locked, NULL, 0U) == D3DERR_INVALIDCALL);
  for (UINT y = 0; y < 3U; ++y) {
    uint8_t *row = static_cast<uint8_t *>(locked.pBits) + y * locked.Pitch;
    memset(row, (int)(0x20U + y), row_bytes);
    for (UINT x = row_bytes; x < (UINT)locked.Pitch; ++x) assert(row[x] == 0U);
  }
  assert(surface->UnlockRect() == D3D_OK);
  assert(record.calls == 1U && record.first == 0x20U);
  assert(record.pitch == surface->GetPitch() && record.format == format);
  assert(texture->GetNativeTexture() == 0x1234U);
  assert(surface->UnlockRect() == D3DERR_INVALIDCALL);

  assert(surface->LockRect(&locked, NULL, D3DLOCK_READONLY) == D3D_OK);
  assert(surface->UnlockRect() == D3D_OK);
  assert(record.calls == 1U);
  assert(surface->LockRect(&locked, NULL, D3DLOCK_NO_DIRTY_UPDATE) == D3D_OK);
  assert(surface->UnlockRect() == D3D_OK);
  assert(record.calls == 2U);
  assert(surface->LockRect(&locked, NULL, 0x400U) == D3DERR_INVALIDCALL);

  RECT invalid = {4, 0, 6, 1};
  assert(surface->LockRect(&locked, &invalid, 0U) == D3DERR_INVALIDCALL);
  RECT sub = {1, 1, 3, 3};
  assert(surface->LockRect(&locked, &sub, 0U) == D3D_OK);
  assert(locked.pBits == surface->GetData() + surface->GetPitch() +
                             BytesPerPixel(format));
  record.fail = true;
  assert(surface->UnlockRect() == D3DERR_OUTOFVIDEOMEMORY);
  assert(record.calls == 3U);
  assert(surface->LockRect(&locked, NULL, D3DLOCK_READONLY) == D3D_OK);
  assert(surface->UnlockRect() == D3D_OK);

  assert(texture->Release() == 0U);
  D3DSURFACE_DESC retained = {};
  assert(surface->GetDesc(&retained) == D3D_OK);
  assert(surface->LockRect(&locked, NULL, 0U) == D3D_OK);
  assert(surface->UnlockRect() == D3D_OK);
  assert(record.calls == 3U);
  assert(surface->Release() == 0U);
}

static void ExerciseLockedOwnerRelease() {
  UploadRecord record = {};
  IDirect3DTexture8 *texture = GeneralsVitaCreateTexture(
      4U, 4U, D3DFMT_X8R8G8B8, 16U, RecordUpload, &record);
  assert(texture != NULL);
  IDirect3DSurface8 *surface = NULL;
  assert(texture->GetSurfaceLevel(0U, &surface) == D3D_OK);
  D3DLOCKED_RECT locked = {};
  assert(surface->LockRect(&locked, NULL, 0U) == D3D_OK);
  assert(texture->Release() == 0U);
  assert(surface->UnlockRect() == D3D_OK);
  assert(record.calls == 0U);
  assert(surface->Release() == 0U);
}

static void ExerciseReentrantUpload() {
  ReentrantRecord record = {};
  record.texture = GeneralsVitaCreateTexture(
      4U, 4U, D3DFMT_X8R8G8B8, 16U, ReleaseTextureDuringUpload, &record);
  assert(record.texture != NULL);
  IDirect3DSurface8 *surface = NULL;
  assert(record.texture->GetSurfaceLevel(0U, &surface) == D3D_OK);
  D3DLOCKED_RECT locked = {};
  assert(surface->LockRect(&locked, NULL, 0U) == D3D_OK);
  assert(surface->UnlockRect() == D3D_OK);
  assert(record.calls == 1U && record.texture == NULL);
  assert(surface->Release() == 0U);
}

int main() {
  const D3DFORMAT formats[] = {D3DFMT_X8R8G8B8, D3DFMT_R8G8B8,
                               D3DFMT_R5G6B5, D3DFMT_X1R5G5B5};
  for (unsigned cycle = 0; cycle < 2U; ++cycle) {
    for (unsigned i = 0; i < sizeof(formats) / sizeof(formats[0]); ++i) {
      Exercise(formats[i]);
    }
  }
  ExerciseLockedOwnerRelease();
  ExerciseReentrantUpload();
  assert(GeneralsVitaCreateTexture(1U, 1U, D3DFMT_UNKNOWN, 16U, RecordUpload,
                                   NULL) == NULL);
  assert(GeneralsVitaCreateTexture(0U, 1U, D3DFMT_X8R8G8B8, 16U, RecordUpload,
                                   NULL) == NULL);
  assert(GeneralsVitaCreateTexture(1U, 0U, D3DFMT_X8R8G8B8, 16U, RecordUpload,
                                   NULL) == NULL);
  assert(GeneralsVitaCreateTexture(UINT32_MAX, 2U, D3DFMT_X8R8G8B8, 16U,
                                   RecordUpload, NULL) == NULL);
  assert(GeneralsVitaCreateTexture(4U, 4U, D3DFMT_X8R8G8B8, 3U, RecordUpload,
                                   NULL) == NULL);
  assert(GeneralsVitaCreateTexture(4U, 4U, D3DFMT_X8R8G8B8, 0U, RecordUpload,
                                   NULL) == NULL);
  return 0;
}
