// SPDX-License-Identifier: GPL-3.0-or-later
#include "VitaW3DTextureUpload.h"
// Retain both native callbacks without calling graphics APIs before initialization.
GeneralsVitaTextureUpload volatile upload_callback = GeneralsVitaUploadTexture;
GeneralsVitaTextureRelease volatile release_callback = GeneralsVitaReleaseTexture;
int main() { return upload_callback && release_callback ? 0 : 1; }
