# SPDX-License-Identifier: GPL-3.0-or-later
if(NOT CMAKE_CROSSCOMPILING)
  set(GENERALS_ICONV_PREFIX "" CACHE PATH "Verified host GNU libiconv recipe output")
  if(NOT EXISTS "${GENERALS_ICONV_PREFIX}/library/include/iconv.h" OR NOT EXISTS "${GENERALS_ICONV_PREFIX}/library/lib/.libs/libiconv.a")
    message(FATAL_ERROR "Host file probes require the verified host libiconv build")
  endif()
  add_library(generals_file_cluster STATIC
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/rawfile.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/bufffile.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/ffactory.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/chunkio.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/wwstring.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/mutex.cpp
    port/src/ansi-conversion.cpp tests/thread-yield-host.cpp)
  target_include_directories(generals_file_cluster PUBLIC
    ${GENERALS_ICONV_PREFIX}/library/include port/include
    ${VG_ORIGINAL}/GameEngine/Include/Precompiled
    ${VG_ORIGINAL}/GameEngine/Include ${VG_ORIGINAL}/Libraries/Include
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWDebug
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad)
  target_compile_definitions(generals_file_cluster PUBLIC GENERALS_PLATFORM_VITA
    __DYNAMIC_REENT__ NDEBUG __cdecl= __forceinline=inline _OPERATOR_NEW_DEFINED_
    GENERALS_WWLIB_STDIO GENERALS_WWLIB_ANSI_ENCODING="CP1252"
    GENERALS_MEMORY_POOL_CONFIG_PATH="${GENERALS_MEMORY_POOL_CONFIG_PATH}")
  target_compile_options(generals_file_cluster PUBLIC -fsanitize=address,undefined -fno-omit-frame-pointer)
  target_link_options(generals_file_cluster PUBLIC -fsanitize=address,undefined)
  target_link_libraries(generals_file_cluster PUBLIC pthread ${GENERALS_ICONV_PREFIX}/library/lib/.libs/libiconv.a)
  foreach(probe rawfile factory chunk-file)
    add_executable(${probe}_probe tests/${probe}-probe.cpp)
    target_link_libraries(${probe}_probe PRIVATE generals_file_cluster)
    add_test(NAME ${probe}_probe COMMAND ${probe}_probe)
  endforeach()
endif()
