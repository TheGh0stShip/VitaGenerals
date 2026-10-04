#pragma once

// SPDX-License-Identifier: GPL-3.0-or-later

// Minimal Direct3D 8 data contract used beneath the original WW3D texture and
// surface owners. Native rendering is supplied by the platform upload callback.

#include <stddef.h>
#include <stdint.h>

typedef int32_t HRESULT;
typedef uint32_t DWORD;
typedef uint32_t UINT;
typedef uint32_t ULONG;
typedef uint32_t D3DFORMAT;

struct RECT {
  int32_t left;
  int32_t top;
  int32_t right;
  int32_t bottom;
};

struct D3DLOCKED_RECT {
  int32_t Pitch;
  void *pBits;
};

struct D3DSURFACE_DESC {
  D3DFORMAT Format;
  uint32_t Type;
  DWORD Usage;
  uint32_t Pool;
  UINT Size;
  uint32_t MultiSampleType;
  UINT Width;
  UINT Height;
};

static const HRESULT D3D_OK = 0;
static const HRESULT D3DERR_INVALIDCALL = (HRESULT)0x8876086cU;
static const HRESULT D3DERR_OUTOFVIDEOMEMORY = (HRESULT)0x8876017cU;

static const DWORD D3DLOCK_READONLY = 0x10U;
static const DWORD D3DLOCK_NOSYSLOCK = 0x800U;
static const DWORD D3DLOCK_NO_DIRTY_UPDATE = 0x8000U;

static const D3DFORMAT D3DFMT_UNKNOWN = 0U;
static const D3DFORMAT D3DFMT_R8G8B8 = 20U;
static const D3DFORMAT D3DFMT_X8R8G8B8 = 22U;
static const D3DFORMAT D3DFMT_R5G6B5 = 23U;
static const D3DFORMAT D3DFMT_X1R5G5B5 = 24U;

struct IDirect3DTexture8;

typedef HRESULT (*GeneralsVitaTextureUpload)(
    void *context, uint32_t *native_texture, UINT width, UINT height,
    D3DFORMAT format, const void *pixels, UINT pitch);

// Upload callbacks receive the complete logical surface on every writable
// unlock. The pitch may include padding beyond width * bytes-per-pixel.

struct IDirect3DSurface8 {
  ULONG AddRef();
  ULONG Release();
  HRESULT GetDesc(D3DSURFACE_DESC *description);
  HRESULT LockRect(D3DLOCKED_RECT *locked, const RECT *rectangle, DWORD flags);
  HRESULT UnlockRect();

  const uint8_t *GetData() const { return storage_; }
  uint8_t *GetData() { return storage_; }
  UINT GetPitch() const { return pitch_; }
  UINT GetStorageSize() const { return storage_size_; }

 private:
  friend struct IDirect3DTexture8;
  friend IDirect3DTexture8 *GeneralsVitaCreateTexture(
      UINT, UINT, D3DFORMAT, UINT, GeneralsVitaTextureUpload, void *);
  IDirect3DSurface8(UINT width, UINT height, D3DFORMAT format,
                   UINT pitch_alignment);
  ~IDirect3DSurface8();
  HRESULT UploadOwner();

  uint8_t *storage_;
  UINT storage_size_;
  UINT width_;
  UINT height_;
  UINT pitch_;
  D3DFORMAT format_;
  ULONG reference_count_;
  IDirect3DTexture8 *owner_;
  DWORD lock_flags_;
  bool locked_;
};

struct IDirect3DTexture8 {
  ULONG AddRef();
  ULONG Release();
  UINT GetLevelCount() const;
  HRESULT GetLevelDesc(UINT level, D3DSURFACE_DESC *description);
  HRESULT GetSurfaceLevel(UINT level, IDirect3DSurface8 **surface);
  HRESULT LockRect(UINT level, D3DLOCKED_RECT *locked, const RECT *rectangle,
                   DWORD flags);
  HRESULT UnlockRect(UINT level);
  uint32_t GetNativeTexture() const { return native_texture_; }

 private:
  friend IDirect3DTexture8 *GeneralsVitaCreateTexture(
      UINT, UINT, D3DFORMAT, UINT, GeneralsVitaTextureUpload, void *);
  friend struct IDirect3DSurface8;
  IDirect3DTexture8(UINT width, UINT height, D3DFORMAT format,
                    GeneralsVitaTextureUpload upload, void *upload_context);
  ~IDirect3DTexture8();

  UINT width_;
  UINT height_;
  D3DFORMAT format_;
  ULONG reference_count_;
  IDirect3DSurface8 *surface_;
  GeneralsVitaTextureUpload upload_;
  void *upload_context_;
  uint32_t native_texture_;
};

IDirect3DTexture8 *GeneralsVitaCreateTexture(
    UINT width, UINT height, D3DFORMAT format, UINT pitch_alignment,
    GeneralsVitaTextureUpload upload, void *upload_context);

static_assert(sizeof(HRESULT) == 4, "DX8 HRESULT must remain 32-bit");
static_assert(sizeof(DWORD) == 4, "DX8 DWORD must remain 32-bit");
static_assert(sizeof(D3DSURFACE_DESC) == 32,
              "DX8 surface description layout must remain stable");
