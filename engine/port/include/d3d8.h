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

typedef void (*GeneralsVitaTextureRelease)(void *context, uint32_t native_texture);

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
  friend IDirect3DSurface8 *GeneralsVitaCreateSurface(
      UINT, UINT, D3DFORMAT, UINT);
  friend struct IDirect3DTexture8;
  friend IDirect3DTexture8 *GeneralsVitaCreateTexture(
      UINT, UINT, D3DFORMAT, UINT, GeneralsVitaTextureUpload, void *,
      GeneralsVitaTextureRelease);
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
  uint32_t pool_;
  ULONG reference_count_;
  IDirect3DTexture8 *owner_;
  DWORD lock_flags_;
  bool locked_;
};

// The original wrapper retains textures through their base interface. Keep
// reference operations dynamically dispatched to the actual texture owner.
struct IDirect3DBaseTexture8 {
  virtual ULONG AddRef() = 0;
  virtual ULONG Release() = 0;
 protected:
  virtual ~IDirect3DBaseTexture8() {}
};

struct IDirect3DTexture8 : IDirect3DBaseTexture8 {
  ULONG AddRef() override;
  ULONG Release() override;
  UINT GetLevelCount() const;
  HRESULT GetLevelDesc(UINT level, D3DSURFACE_DESC *description);
  HRESULT GetSurfaceLevel(UINT level, IDirect3DSurface8 **surface);
  HRESULT LockRect(UINT level, D3DLOCKED_RECT *locked, const RECT *rectangle,
                   DWORD flags);
  HRESULT UnlockRect(UINT level);
  uint32_t GetNativeTexture() const { return native_texture_; }

 private:
  friend IDirect3DTexture8 *GeneralsVitaCreateTexture(
      UINT, UINT, D3DFORMAT, UINT, GeneralsVitaTextureUpload, void *,
      GeneralsVitaTextureRelease);
  friend struct IDirect3DSurface8;
  IDirect3DTexture8(UINT width, UINT height, D3DFORMAT format,
                    GeneralsVitaTextureUpload upload, void *upload_context,
                    GeneralsVitaTextureRelease release);
  ~IDirect3DTexture8();

  UINT width_;
  UINT height_;
  D3DFORMAT format_;
  ULONG reference_count_;
  IDirect3DSurface8 *surface_;
  GeneralsVitaTextureUpload upload_;
  void *upload_context_;
  uint32_t native_texture_;
  GeneralsVitaTextureRelease release_;
};

IDirect3DTexture8 *GeneralsVitaCreateTexture(
    UINT width, UINT height, D3DFORMAT format, UINT pitch_alignment,
    GeneralsVitaTextureUpload upload, void *upload_context,
    GeneralsVitaTextureRelease release = NULL);

IDirect3DSurface8 *GeneralsVitaCreateSurface(
    UINT width, UINT height, D3DFORMAT format, UINT pitch_alignment);

static_assert(sizeof(HRESULT) == 4, "DX8 HRESULT must remain 32-bit");
static_assert(sizeof(DWORD) == 4, "DX8 DWORD must remain 32-bit");
static_assert(sizeof(D3DSURFACE_DESC) == 32,
              "DX8 surface description layout must remain stable");

// Original DX8 FVF bit encoding; texture coordinate sizes occupy two bits each.
static const DWORD D3DFVF_XYZ = 0x002U;
static const DWORD D3DFVF_XYZRHW = 0x004U;
static const DWORD D3DFVF_NORMAL = 0x010U;
static const DWORD D3DFVF_DIFFUSE = 0x040U;
static const DWORD D3DFVF_SPECULAR = 0x080U;
static const DWORD D3DFVF_TEX0 = 0x000U;
static const DWORD D3DFVF_TEX1 = 0x100U;
static const DWORD D3DFVF_TEX2 = 0x200U;
static const DWORD D3DFVF_TEX3 = 0x300U;
static const DWORD D3DFVF_TEX4 = 0x400U;
static const DWORD D3DFVF_TEX5 = 0x500U;
static const DWORD D3DFVF_TEX6 = 0x600U;
static const DWORD D3DFVF_TEX7 = 0x700U;
static const DWORD D3DFVF_TEX8 = 0x800U;
#define D3DFVF_TEXCOORDSIZE1(index) (3U << (16U + 2U * (index)))
#define D3DFVF_TEXCOORDSIZE2(index) (0U)
#define D3DFVF_TEXCOORDSIZE3(index) (1U << (16U + 2U * (index)))
#define D3DFVF_TEXCOORDSIZE4(index) (2U << (16U + 2U * (index)))
static const UINT D3DDP_MAXTEXCOORD = 8U;

// DX8 capability data layout, adapted from the reviewed WW3D Vita boundary.
struct D3DCAPS8 {
	uint32_t DeviceType;
	UINT AdapterOrdinal;
	DWORD Caps, Caps2, Caps3, PresentationIntervals;
	DWORD CursorCaps, DevCaps;
	DWORD PrimitiveMiscCaps, RasterCaps, ZCmpCaps;
	DWORD SrcBlendCaps, DestBlendCaps, AlphaCmpCaps, ShadeCaps;
	DWORD TextureCaps, TextureFilterCaps, CubeTextureFilterCaps;
	DWORD VolumeTextureFilterCaps, TextureAddressCaps, VolumeTextureAddressCaps;
	DWORD LineCaps;
	DWORD MaxTextureWidth, MaxTextureHeight, MaxVolumeExtent;
	DWORD MaxTextureRepeat, MaxTextureAspectRatio, MaxAnisotropy;
	float MaxVertexW;
	float GuardBandLeft, GuardBandTop, GuardBandRight, GuardBandBottom;
	float ExtentsAdjust;
	DWORD StencilCaps, FVFCaps, TextureOpCaps;
	DWORD MaxTextureBlendStages, MaxSimultaneousTextures;
	DWORD VertexProcessingCaps, MaxActiveLights, MaxUserClipPlanes;
	DWORD MaxVertexBlendMatrices, MaxVertexBlendMatrixIndex;
	float MaxPointSize;
	DWORD MaxPrimitiveCount, MaxVertexIndex, MaxStreams, MaxStreamStride;
	DWORD VertexShaderVersion, MaxVertexShaderConst, PixelShaderVersion;
	float MaxPixelShaderValue;
};
static_assert(sizeof(D3DCAPS8) == 212, "DX8 capability scalar layout");

// Adapter fields follow the published DX8 contract. Version words are explicit
// so LP64 hosts preserve the original Windows 32-bit word access.
struct alignas(8) GeneralsDX8DriverVersion {
  uint32_t LowPart;
  int32_t HighPart;
};
struct GeneralsDX8DeviceIdentifier {
  uint32_t Data1;
  uint16_t Data2, Data3;
  uint8_t Data4[8];
};
struct D3DADAPTER_IDENTIFIER8 {
  char Driver[512];
  char Description[512];
  GeneralsDX8DriverVersion DriverVersion;
  DWORD VendorId, DeviceId, SubSysId, Revision;
  GeneralsDX8DeviceIdentifier DeviceIdentifier;
  DWORD WHQLLevel;
};
static_assert(offsetof(D3DADAPTER_IDENTIFIER8, DriverVersion) == 1024,
              "DX8 adapter version offset");
static_assert(offsetof(D3DADAPTER_IDENTIFIER8, DeviceIdentifier) == 1048,
              "DX8 adapter identifier offset");
static_assert(offsetof(D3DADAPTER_IDENTIFIER8, WHQLLevel) == 1064,
              "DX8 adapter certification offset");
static_assert(sizeof(D3DADAPTER_IDENTIFIER8) == 1072,
              "DX8 adapter layout retains 8-byte version alignment");

struct IDirect3D8;
struct IDirect3DDevice8;
struct IDirect3DVolumeTexture8;
struct IDirect3DCubeTexture8;
struct IDirect3DVertexBuffer8;
struct IDirect3DIndexBuffer8;
struct IDirect3DSwapChain8;
typedef uint32_t D3DPOOL;
typedef uint32_t D3DTRANSFORMSTATETYPE;
typedef uint32_t D3DRENDERSTATETYPE;
typedef uint32_t D3DTEXTURESTAGESTATETYPE;
typedef uint32_t D3DPRIMITIVETYPE;
typedef uint32_t D3DCOLOR;
struct D3DMATRIX { float m[4][4]; };
struct D3DVIEWPORT8 { UINT X, Y, Width, Height; float MinZ, MaxZ; };
static const D3DPOOL D3DPOOL_DEFAULT = 0U;
static const D3DPOOL D3DPOOL_MANAGED = 1U;
static const D3DPOOL D3DPOOL_SYSTEMMEM = 2U;
static_assert(sizeof(D3DMATRIX) == 64, "DX8 matrix layout");
static_assert(sizeof(D3DVIEWPORT8) == 24, "DX8 viewport layout");

// Original light/material scalar layouts from the reviewed WW3D boundary.
struct D3DCOLORVALUE { float r, g, b, a; };
struct D3DVECTOR { float x, y, z; };
enum D3DLIGHTTYPE {
	D3DLIGHT_POINT = 1,
	D3DLIGHT_SPOT = 2,
	D3DLIGHT_DIRECTIONAL = 3,
	D3DLIGHT_FORCE_DWORD = 0x7fffffff
};
struct D3DLIGHT8 {
	uint32_t Type;
	D3DCOLORVALUE Diffuse;
	D3DCOLORVALUE Specular;
	D3DCOLORVALUE Ambient;
	D3DVECTOR Position;
	D3DVECTOR Direction;
	float Range;
	float Falloff;
	float Attenuation0;
	float Attenuation1;
	float Attenuation2;
	float Theta;
	float Phi;
};
static_assert(sizeof(D3DLIGHT8) == 104, "DX8 light layout must retain 32-bit fields");
struct _D3DMATERIAL8 {
	D3DCOLORVALUE Diffuse;
	D3DCOLORVALUE Ambient;
	D3DCOLORVALUE Specular;
	D3DCOLORVALUE Emissive;
	float Power;
};
typedef struct _D3DMATERIAL8 D3DMATERIAL8;

#ifndef CONST
#define CONST const
#endif
typedef void *HWND;
static const D3DTRANSFORMSTATETYPE D3DTS_WORLD = 256U;
static const D3DTRANSFORMSTATETYPE D3DTS_VIEW = 2U;
static const D3DTRANSFORMSTATETYPE D3DTS_PROJECTION = 3U;

static const D3DRENDERSTATETYPE D3DRS_FOGSTART = 36U;
static const D3DRENDERSTATETYPE D3DRS_FOGEND = 37U;
static const D3DRENDERSTATETYPE D3DRS_ZBIAS = 47U;
static const D3DRENDERSTATETYPE D3DRS_AMBIENT = 139U;
static const D3DRENDERSTATETYPE D3DRS_TEXTUREFACTOR = 60U;
static const D3DTEXTURESTAGESTATETYPE D3DTSS_COLOROP = 1U;
static const D3DTEXTURESTAGESTATETYPE D3DTSS_COLORARG1 = 2U;
static const D3DTEXTURESTAGESTATETYPE D3DTSS_COLORARG2 = 3U;
static const D3DTEXTURESTAGESTATETYPE D3DTSS_COLORARG0 = 26U;
static const DWORD D3DTA_CURRENT = 1U;
static const DWORD D3DTA_TEXTURE = 2U;
static const DWORD D3DTA_TFACTOR = 3U;
static const DWORD D3DTA_ALPHAREPLICATE = 0x20U;
static const DWORD D3DTOP_MODULATE = 4U;
static const DWORD D3DTOP_DOTPRODUCT3 = 24U;
static const DWORD D3DTOP_MULTIPLYADD = 25U;
struct POINT { int32_t x, y; };
struct IDirect3DBaseTexture8;

// Declarations consumed by original DX8Wrapper inline state setters. Backend
// definitions must supply real rendering behavior; no success stubs live here.
struct IDirect3DDevice8 {
  HRESULT CreateImageSurface(UINT, UINT, D3DFORMAT, IDirect3DSurface8 **);
  HRESULT SetTransform(D3DTRANSFORMSTATETYPE, const D3DMATRIX *);
  HRESULT GetTransform(D3DTRANSFORMSTATETYPE, D3DMATRIX *);
  HRESULT SetRenderState(D3DRENDERSTATETYPE, DWORD);
  HRESULT SetTextureStageState(DWORD, D3DTEXTURESTAGESTATETYPE, DWORD);
  HRESULT SetTexture(DWORD, IDirect3DBaseTexture8 *);
  HRESULT SetMaterial(const D3DMATERIAL8 *);
  HRESULT SetLight(DWORD, const D3DLIGHT8 *);
  HRESULT LightEnable(DWORD, int32_t);
  HRESULT SetClipPlane(DWORD, const float *);
  HRESULT SetVertexShader(DWORD);
  HRESULT SetPixelShader(DWORD);
  HRESULT SetVertexShaderConstant(DWORD, const void *, DWORD);
  HRESULT SetPixelShaderConstant(DWORD, const void *, DWORD);
  HRESULT CopyRects(IDirect3DSurface8 *, const RECT *, UINT,
                    IDirect3DSurface8 *, const POINT *);
};
