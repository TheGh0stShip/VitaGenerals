// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <stdint.h>
typedef uint32_t GLenum;
typedef uint32_t GLuint;
typedef int32_t GLint;
#define GL_TEXTURE_BINDING_2D 0x8069
#define GL_UNPACK_ALIGNMENT 0x0cf5
#define GL_TEXTURE_2D 0x0de1
#define GL_NO_ERROR 0
#define GL_OUT_OF_MEMORY 0x0505
#define GL_RGBA 0x1908
#define GL_UNSIGNED_BYTE 0x1401
#define GL_TEXTURE_MIN_FILTER 0x2801
#define GL_TEXTURE_MAG_FILTER 0x2800
#define GL_TEXTURE_WRAP_S 0x2802
#define GL_TEXTURE_WRAP_T 0x2803
#define GL_LINEAR 0x2601
#define GL_CLAMP_TO_EDGE 0x812f
void glGetIntegerv(GLenum, GLint *);
GLenum glGetError();
void glGenTextures(GLint, GLuint *);
void glDeleteTextures(GLint, const GLuint *);
void glBindTexture(GLenum, GLuint);
void glPixelStorei(GLenum, GLint);
void glTexParameteri(GLenum, GLenum, GLint);
void glTexImage2D(GLenum, GLint, GLint, GLint, GLint, GLint, GLenum, GLenum, const void *);
void glTexSubImage2D(GLenum, GLint, GLint, GLint, GLint, GLint, GLenum, GLenum, const void *);
