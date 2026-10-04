// SPDX-License-Identifier: GPL-3.0-or-later
#include "d3d8.h"

#include <limits.h>
#include <new>
#include <string.h>

namespace {

UINT BytesPerPixel(D3DFORMAT format) {
  switch (format) {
    case D3DFMT_X8R8G8B8:
      return 4U;
    case D3DFMT_R8G8B8:
      return 3U;
    case D3DFMT_R5G6B5:
    case D3DFMT_X1R5G5B5:
      return 2U;
    default:
      return 0U;
  }
}

bool AlignPitch(UINT row_bytes, UINT alignment, UINT *pitch) {
  if (pitch == NULL || alignment == 0U ||
      (alignment & (alignment - 1U)) != 0U) {
    return false;
  }
  const UINT mask = alignment - 1U;
  if (row_bytes > UINT32_MAX - mask) return false;
  *pitch = (row_bytes + mask) & ~mask;
  return true;
}

}  // namespace

IDirect3DSurface8::IDirect3DSurface8(UINT width, UINT height,
                                     D3DFORMAT format, UINT pitch_alignment)
    : storage_(NULL),
      storage_size_(0U),
      width_(width),
      height_(height),
      pitch_(0U),
      format_(format),
      reference_count_(1U),
      owner_(NULL),
      lock_flags_(0U),
      locked_(false) {
  const UINT bytes_per_pixel = BytesPerPixel(format);
  if (width == 0U || height == 0U || bytes_per_pixel == 0U ||
      width > UINT32_MAX / bytes_per_pixel) {
    return;
  }
  if (!AlignPitch(width * bytes_per_pixel, pitch_alignment, &pitch_) ||
      pitch_ == 0U || pitch_ > (UINT)INT32_MAX ||
      height > UINT32_MAX / pitch_) {
    pitch_ = 0U;
    return;
  }
  storage_size_ = pitch_ * height;
  storage_ = new (std::nothrow) uint8_t[storage_size_];
  if (storage_ == NULL) {
    storage_size_ = 0U;
    pitch_ = 0U;
    return;
  }
  memset(storage_, 0, storage_size_);
}

IDirect3DSurface8::~IDirect3DSurface8() { delete[] storage_; }

ULONG IDirect3DSurface8::AddRef() { return ++reference_count_; }

ULONG IDirect3DSurface8::Release() {
  if (reference_count_ == 0U) return 0U;
  const ULONG remaining = --reference_count_;
  if (remaining == 0U) delete this;
  return remaining;
}

HRESULT IDirect3DSurface8::GetDesc(D3DSURFACE_DESC *description) {
  if (description == NULL || storage_ == NULL) return D3DERR_INVALIDCALL;
  memset(description, 0, sizeof(*description));
  description->Format = format_;
  description->Size = storage_size_;
  description->Width = width_;
  description->Height = height_;
  return D3D_OK;
}

HRESULT IDirect3DSurface8::LockRect(D3DLOCKED_RECT *locked,
                                    const RECT *rectangle, DWORD flags) {
  const DWORD supported_flags =
      D3DLOCK_READONLY | D3DLOCK_NOSYSLOCK | D3DLOCK_NO_DIRTY_UPDATE;
  if (locked == NULL || storage_ == NULL || locked_ ||
      (flags & ~supported_flags) != 0U) {
    return D3DERR_INVALIDCALL;
  }
  UINT left = 0U;
  UINT top = 0U;
  if (rectangle != NULL) {
    if (rectangle->left < 0 || rectangle->top < 0 ||
        rectangle->right <= rectangle->left ||
        rectangle->bottom <= rectangle->top ||
        (UINT)rectangle->right > width_ ||
        (UINT)rectangle->bottom > height_) {
      return D3DERR_INVALIDCALL;
    }
    left = (UINT)rectangle->left;
    top = (UINT)rectangle->top;
  }
  locked->Pitch = (int32_t)pitch_;
  locked->pBits = storage_ + (size_t)top * pitch_ +
                  (size_t)left * BytesPerPixel(format_);
  lock_flags_ = flags;
  locked_ = true;
  return D3D_OK;
}

HRESULT IDirect3DSurface8::UnlockRect() {
  if (!locked_) return D3DERR_INVALIDCALL;
  const DWORD flags = lock_flags_;
  lock_flags_ = 0U;
  locked_ = false;
  if ((flags & D3DLOCK_READONLY) != 0U) return D3D_OK;
  return UploadOwner();
}

HRESULT IDirect3DSurface8::UploadOwner() {
  if (owner_ == NULL || owner_->surface_ != this || owner_->upload_ == NULL) {
    return owner_ == NULL ? D3D_OK : D3DERR_INVALIDCALL;
  }
  IDirect3DTexture8 *owner = owner_;
  owner->AddRef();
  const HRESULT result = owner->upload_(
      owner->upload_context_, &owner->native_texture_, width_, height_, format_,
      storage_, pitch_);
  owner->Release();
  return result;
}

IDirect3DTexture8::IDirect3DTexture8(UINT width, UINT height, D3DFORMAT format,
                                     GeneralsVitaTextureUpload upload,
                                     void *upload_context,
                                     GeneralsVitaTextureRelease release)
    : width_(width),
      height_(height),
      format_(format),
      reference_count_(1U),
      surface_(NULL),
      upload_(upload),
      upload_context_(upload_context),
      native_texture_(0U),
      release_(release) {}

IDirect3DTexture8::~IDirect3DTexture8() {
  if (native_texture_ != 0U && release_ != NULL) {
    release_(upload_context_, native_texture_);
    native_texture_ = 0U;
  }
  if (surface_ != NULL) {
    surface_->owner_ = NULL;
    surface_->Release();
  }
}

ULONG IDirect3DTexture8::AddRef() { return ++reference_count_; }

ULONG IDirect3DTexture8::Release() {
  if (reference_count_ == 0U) return 0U;
  const ULONG remaining = --reference_count_;
  if (remaining == 0U) delete this;
  return remaining;
}

UINT IDirect3DTexture8::GetLevelCount() const { return 1U; }

HRESULT IDirect3DTexture8::GetLevelDesc(UINT level,
                                        D3DSURFACE_DESC *description) {
  if (level != 0U || surface_ == NULL) return D3DERR_INVALIDCALL;
  return surface_->GetDesc(description);
}

HRESULT IDirect3DTexture8::GetSurfaceLevel(UINT level,
                                           IDirect3DSurface8 **surface) {
  if (surface != NULL) *surface = NULL;
  if (level != 0U || surface == NULL || surface_ == NULL) {
    return D3DERR_INVALIDCALL;
  }
  surface_->AddRef();
  *surface = surface_;
  return D3D_OK;
}

HRESULT IDirect3DTexture8::LockRect(UINT level, D3DLOCKED_RECT *locked,
                                    const RECT *rectangle, DWORD flags) {
  if (level != 0U || surface_ == NULL) return D3DERR_INVALIDCALL;
  return surface_->LockRect(locked, rectangle, flags);
}

HRESULT IDirect3DTexture8::UnlockRect(UINT level) {
  if (level != 0U || surface_ == NULL) return D3DERR_INVALIDCALL;
  return surface_->UnlockRect();
}

IDirect3DTexture8 *GeneralsVitaCreateTexture(
    UINT width, UINT height, D3DFORMAT format, UINT pitch_alignment,
    GeneralsVitaTextureUpload upload, void *upload_context,
    GeneralsVitaTextureRelease release) {
  IDirect3DTexture8 *texture = new (std::nothrow)
      IDirect3DTexture8(width, height, format, upload, upload_context, release);
  if (texture == NULL) return NULL;
  texture->surface_ =
      new (std::nothrow) IDirect3DSurface8(width, height, format,
                                          pitch_alignment);
  if (texture->surface_ == NULL || texture->surface_->GetData() == NULL) {
    texture->Release();
    return NULL;
  }
  texture->surface_->owner_ = texture;
  return texture;
}
