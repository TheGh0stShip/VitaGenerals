# SPDX-License-Identifier: GPL-3.0-or-later
cmake_minimum_required(VERSION 3.16)
project(GeneralsNativeClusters LANGUAGES CXX)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
get_filename_component(VG_PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)
set(GENERALS_STAGED_CODE "" CACHE PATH "Verified complete staged engine Code directory")
if(NOT EXISTS "${GENERALS_STAGED_CODE}/Libraries/Source/WWVegas/WWLib/always.h")
  message(FATAL_ERROR "A verified complete engine stage is required")
endif()
get_filename_component(VG_ORIGINAL "${GENERALS_STAGED_CODE}" ABSOLUTE)
get_filename_component(VG_STAGE "${VG_ORIGINAL}/.." ABSOLUTE)
execute_process(COMMAND ${Python3_EXECUTABLE}
  ${VG_PROJECT_ROOT}/tools/verify_engine_stage.py --stage ${VG_STAGE}
  RESULT_VARIABLE VG_STAGE_RESULT)
if(NOT VG_STAGE_RESULT EQUAL 0)
  message(FATAL_ERROR "Complete engine stage does not match current source and patch pins")
endif()
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
  ${VG_STAGE}/receipt.json ${VG_PROJECT_ROOT}/tools/source-lock.json
  ${VG_PROJECT_ROOT}/vendor/ea/manifest.json
  ${VG_PROJECT_ROOT}/tools/verify_engine_stage.py
  ${VG_PROJECT_ROOT}/tools/stage_engine_tree.py)
add_custom_target(verify_engine_stage
  COMMAND ${Python3_EXECUTABLE} ${VG_PROJECT_ROOT}/tools/verify_engine_stage.py --stage ${VG_STAGE}
  VERBATIM)
set(GENERALS_MEMORY_POOL_CONFIG_PATH "" CACHE STRING "Explicit bootstrap configuration path")
if(GENERALS_MEMORY_POOL_CONFIG_PATH STREQUAL "")
  message(FATAL_ERROR "An explicit memory pool configuration path is required")
endif()
set(GENERALS_LEGACY_ENCODING "CP1252" CACHE STRING
  "Installation ANSI encoding used by original narrow/wide string conversion")
if(GENERALS_LEGACY_ENCODING STREQUAL "")
  message(FATAL_ERROR "An explicit installation ANSI encoding is required")
endif()
if(NOT EXISTS "${GENERALS_ICONV_PREFIX}/library/include/iconv.h" OR
   NOT EXISTS "${GENERALS_ICONV_PREFIX}/library/lib/.libs/libiconv.a")
  message(FATAL_ERROR "The native string cluster requires the verified GNU libiconv build")
endif()
if(CMAKE_CROSSCOMPILING)
  execute_process(COMMAND ${CMAKE_CXX_COMPILER} -dumpmachine
    OUTPUT_VARIABLE VG_COMPILER_TARGET OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE VG_COMPILER_TARGET_RESULT)
  if(NOT VG_COMPILER_TARGET_RESULT EQUAL 0 OR NOT VG_COMPILER_TARGET STREQUAL "arm-vita-eabi")
    message(FATAL_ERROR "The native cluster requires the checked ARMv7 Vita toolchain")
  endif()
  if(NOT EXISTS "${VITASDK}/version_info.txt")
    message(FATAL_ERROR "SDK identity is required for the private descriptor interface")
  endif()
  file(STRINGS "${VITASDK}/version_info.txt" VG_NEWLIB_IDENTITY
    REGEX "^newlib[ \t]+2e428297c0b6aefd830c5a75a7daa7e774562a42$")
  if(NOT VG_NEWLIB_IDENTITY)
    message(FATAL_ERROR "The descriptor adapter requires the reviewed newlib revision")
  endif()
endif()
add_library(generals_allocator_cluster STATIC
  ${VG_ORIGINAL}/GameEngine/Source/Common/System/GameMemory.cpp
  port/src/MemoryBacking.cpp
  ${VG_ORIGINAL}/GameEngine/Source/Common/System/MemoryInit.cpp
  ${VG_ORIGINAL}/GameEngine/Source/Common/System/AsciiString.cpp
  ${VG_ORIGINAL}/GameEngine/Source/Common/System/UnicodeString.cpp
  port/src/utf16-format.cpp
  port/src/bootstrap-pool-path.cpp
  ${VG_ORIGINAL}/GameEngine/Source/Common/System/CriticalSection.cpp)
target_compile_definitions(generals_allocator_cluster PUBLIC
  NDEBUG __cdecl= __forceinline=inline
  GENERALS_WIDE_CRT_ENCODING="${GENERALS_LEGACY_ENCODING}"
  GENERALS_MEMORY_POOL_CONFIG_PATH="${GENERALS_MEMORY_POOL_CONFIG_PATH}")
if(GENERALS_LEGACY_ENCODING STREQUAL "CP932")
  target_compile_definitions(generals_allocator_cluster PUBLIC
    GENERALS_LEGACY_ENCODING_CP932=1)
elseif(GENERALS_LEGACY_ENCODING STREQUAL "CP1252")
  target_compile_definitions(generals_allocator_cluster PUBLIC
    GENERALS_LEGACY_ENCODING_CP1252=1)
endif()
if(NOT CMAKE_CROSSCOMPILING)
  target_compile_options(generals_allocator_cluster PUBLIC
    -include mutex -fsanitize=address,undefined -fno-omit-frame-pointer)
  target_link_options(generals_allocator_cluster PUBLIC -fsanitize=address,undefined)
  target_link_libraries(generals_allocator_cluster PUBLIC pthread)
endif()
target_include_directories(generals_allocator_cluster PUBLIC
  port/include
  ${GENERALS_ICONV_PREFIX}/library/include
  ${VG_ORIGINAL}/GameEngine/Include/Precompiled
  ${VG_ORIGINAL}/GameEngine/Include ${VG_ORIGINAL}/Libraries/Include
  ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath
  ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib
  ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWDebug
  ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad)
target_link_libraries(generals_allocator_cluster PUBLIC
  ${GENERALS_ICONV_PREFIX}/library/lib/.libs/libiconv.a)
if(CMAKE_CROSSCOMPILING)
  target_sources(generals_allocator_cluster PRIVATE port/src/native-thread-yield.cpp)
  target_compile_definitions(generals_allocator_cluster PUBLIC __DYNAMIC_REENT__ GENERALS_PLATFORM_VITA)
  target_compile_options(generals_allocator_cluster PUBLIC
    -mcpu=cortex-a9 -mthumb -mfpu=neon -mfloat-abi=hard)
  target_link_libraries(generals_allocator_cluster PUBLIC SceLibKernel_stub)
  add_custom_command(TARGET generals_allocator_cluster POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E env VITASDK=${VITASDK}
      ${Python3_EXECUTABLE} ${VG_PROJECT_ROOT}/tools/check_vita_abi.py
      $<TARGET_FILE:generals_allocator_cluster> VERBATIM)
endif()
foreach(VG_PROBE allocator_alignment ascii_allocator ascii_reference)
  if(VG_PROBE STREQUAL "allocator_alignment")
    set(VG_ENTRY allocator-alignment-entry.cpp)
  elseif(VG_PROBE STREQUAL "ascii_allocator")
    set(VG_ENTRY ascii-allocator-entry.cpp)
  else()
    set(VG_ENTRY ascii-reference-entry.cpp)
  endif()
  add_executable(${VG_PROBE} ${VG_ENTRY})
  target_link_libraries(${VG_PROBE} PRIVATE generals_allocator_cluster)
  if(CMAKE_CROSSCOMPILING)
    target_link_options(${VG_PROBE} PRIVATE
      -Wl,-Map,${CMAKE_CURRENT_BINARY_DIR}/${VG_PROBE}.map)
    add_custom_command(TARGET ${VG_PROBE} POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E env VITASDK=${VITASDK}
        ${Python3_EXECUTABLE} ${VG_PROJECT_ROOT}/tools/check_vita_abi.py
        $<TARGET_FILE:${VG_PROBE}> VERBATIM)
  endif()
endforeach()
add_executable(unicode_reference unicode-entry.cpp)
target_link_libraries(unicode_reference PRIVATE generals_allocator_cluster)
if(CMAKE_CROSSCOMPILING)
  target_link_options(unicode_reference PRIVATE
    -Wl,-Map,${CMAKE_CURRENT_BINARY_DIR}/unicode_reference.map)
  add_custom_command(TARGET unicode_reference POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E env VITASDK=${VITASDK}
      ${Python3_EXECUTABLE} ${VG_PROJECT_ROOT}/tools/check_vita_abi.py
      $<TARGET_FILE:unicode_reference> VERBATIM)
endif()
if(NOT CMAKE_CROSSCOMPILING)
  enable_testing()
  add_test(NAME allocator_alignment COMMAND allocator_alignment)
  add_test(NAME ascii_allocator COMMAND ascii_allocator)
  add_test(NAME ascii_reference COMMAND ascii_reference)
  add_test(NAME unicode_reference COMMAND unicode_reference)
endif()

include(wwmath-cluster.cmake)

include(file-cluster-host.cmake)

set(GENERALS_FFMPEG_PREFIX "" CACHE PATH
  "Pinned Vita FFmpeg Bink dependency installation")
if(NOT CMAKE_CROSSCOMPILING)
  add_library(generals_retail_path STATIC port/src/GeneralsRetailPath.cpp)
  target_include_directories(generals_retail_path PUBLIC port/include)
  target_compile_options(generals_retail_path PRIVATE -Wall -Wextra -Werror)
  target_compile_definitions(generals_retail_path PRIVATE GENERALS_RETAIL_ROOT="test-root")
  add_executable(retail_path_probe tests/retail-path-probe.cpp)
  target_link_libraries(retail_path_probe PRIVATE generals_retail_path)
  target_compile_options(retail_path_probe PRIVATE -Wall -Wextra -Werror)
  add_test(NAME retail_path_boundary COMMAND retail_path_probe)
endif()
if(CMAKE_CROSSCOMPILING AND NOT GENERALS_FFMPEG_PREFIX STREQUAL "")
  set(GENERALS_RETAIL_ROOT "" CACHE STRING
    "Vita path containing unchanged user-supplied Zero Hour retail data")
  if(GENERALS_RETAIL_ROOT STREQUAL "")
    message(FATAL_ERROR "The Bink provider requires an explicit retail-data root")
  endif()
  add_library(generals_retail_path STATIC port/src/GeneralsRetailPath.cpp)
  target_include_directories(generals_retail_path PUBLIC port/include)
  target_compile_definitions(generals_retail_path PRIVATE
    GENERALS_RETAIL_ROOT="${GENERALS_RETAIL_ROOT}")
  target_compile_options(generals_retail_path PRIVATE
    -mcpu=cortex-a9 -mthumb -mfpu=neon -mfloat-abi=hard
    -Wall -Wextra -Werror)
  foreach(VG_FFMPEG_LIBRARY avformat avcodec swscale swresample avutil)
    if(NOT EXISTS "${GENERALS_FFMPEG_PREFIX}/lib/lib${VG_FFMPEG_LIBRARY}.a")
      message(FATAL_ERROR "Incomplete Vita FFmpeg Bink dependency")
    endif()
  endforeach()
  add_library(generals_bink_video_decoder STATIC
    port/src/VitaBinkVideoDecoder.cpp
    port/src/VitaBinkAudioOutput.cpp)
  target_include_directories(generals_bink_video_decoder PUBLIC
    port/include "${GENERALS_FFMPEG_PREFIX}/include")
  target_compile_options(generals_bink_video_decoder PRIVATE
    -mcpu=cortex-a9 -mthumb -mfpu=neon -mfloat-abi=hard
    -Wall -Wextra -Werror)
  add_library(generals_bink_video_adapter STATIC
    port/src/VitaBinkVideoPlayer.cpp)
  target_include_directories(generals_bink_video_adapter PRIVATE
    port/include
    ${VG_ORIGINAL}/GameEngine/Include/Precompiled
    ${VG_ORIGINAL}/GameEngine/Include
    ${VG_ORIGINAL}/GameEngineDevice/Include
    ${VG_ORIGINAL}/Libraries/Include
    ${VG_ORIGINAL}/Libraries/Source/WWVegas
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib)
  target_compile_definitions(generals_bink_video_adapter PRIVATE
    NDEBUG __cdecl= __forceinline=inline GENERALS_PLATFORM_VITA)
  target_compile_options(generals_bink_video_adapter PRIVATE
    -mcpu=cortex-a9 -mthumb -mfpu=neon -mfloat-abi=hard
    -Wall -Wextra -Wno-error -fcheck-new -Wno-unknown-pragmas)
  target_link_libraries(generals_bink_video_adapter PUBLIC
    generals_bink_video_decoder generals_retail_path)
  add_custom_command(TARGET generals_bink_video_adapter POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E env VITASDK=${VITASDK}
      ${Python3_EXECUTABLE} ${VG_PROJECT_ROOT}/tools/check_vita_abi.py
      $<TARGET_FILE:generals_bink_video_adapter> VERBATIM)
  add_executable(bink_decoder_link bink-decoder-link-entry.cpp)
  target_link_libraries(bink_decoder_link PRIVATE generals_bink_video_decoder
    "${GENERALS_FFMPEG_PREFIX}/lib/libavformat.a"
    "${GENERALS_FFMPEG_PREFIX}/lib/libavcodec.a"
    "${GENERALS_FFMPEG_PREFIX}/lib/libswscale.a"
    "${GENERALS_FFMPEG_PREFIX}/lib/libswresample.a"
    "${GENERALS_FFMPEG_PREFIX}/lib/libavutil.a"
    pthread m SceAudio_stub SceLibKernel_stub)
  target_link_options(bink_decoder_link PRIVATE
    -Wl,-Map,${CMAKE_CURRENT_BINARY_DIR}/bink_decoder_link.map)
  add_custom_command(TARGET bink_decoder_link POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E env VITASDK=${VITASDK}
      ${Python3_EXECUTABLE} ${VG_PROJECT_ROOT}/tools/check_vita_abi.py
      $<TARGET_FILE:generals_bink_video_decoder> $<TARGET_FILE:bink_decoder_link>
    VERBATIM)
endif()
foreach(VG_CLUSTER generals_allocator_cluster generals_file_cluster generals_wwmath generals_wwmath_providers)
  if(TARGET ${VG_CLUSTER})
    add_dependencies(${VG_CLUSTER} verify_engine_stage)
  endif()
endforeach()
