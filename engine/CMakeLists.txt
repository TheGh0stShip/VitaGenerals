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
  port/src/bootstrap-pool-path.cpp
  ${VG_ORIGINAL}/GameEngine/Source/Common/System/CriticalSection.cpp)
target_compile_definitions(generals_allocator_cluster PUBLIC
  NDEBUG __cdecl= __forceinline=inline
  GENERALS_MEMORY_POOL_CONFIG_PATH="${GENERALS_MEMORY_POOL_CONFIG_PATH}")
if(NOT CMAKE_CROSSCOMPILING)
  target_compile_options(generals_allocator_cluster PUBLIC
    -include mutex -fsanitize=address,undefined -fno-omit-frame-pointer)
  target_link_options(generals_allocator_cluster PUBLIC -fsanitize=address,undefined)
  target_link_libraries(generals_allocator_cluster PUBLIC pthread)
endif()
target_include_directories(generals_allocator_cluster PUBLIC
  port/include
  ${VG_ORIGINAL}/GameEngine/Include/Precompiled
  ${VG_ORIGINAL}/GameEngine/Include ${VG_ORIGINAL}/Libraries/Include
  ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath
  ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib
  ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWDebug
  ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad)
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
if(NOT CMAKE_CROSSCOMPILING)
  enable_testing()
  add_test(NAME allocator_alignment COMMAND allocator_alignment)
  add_test(NAME ascii_allocator COMMAND ascii_allocator)
  add_test(NAME ascii_reference COMMAND ascii_reference)
endif()

include(wwmath-cluster.cmake)

include(file-cluster-host.cmake)
foreach(VG_CLUSTER generals_allocator_cluster generals_file_cluster generals_wwmath generals_wwmath_providers)
  if(TARGET ${VG_CLUSTER})
    add_dependencies(${VG_CLUSTER} verify_engine_stage)
  endif()
endforeach()
