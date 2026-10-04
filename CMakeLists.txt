cmake_minimum_required(VERSION 3.16)
project(VitaGenerals LANGUAGES C CXX)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
find_package(Python3 REQUIRED COMPONENTS Interpreter)

option(VG_HOST_SANITIZERS "Enable address and undefined behavior host probes" OFF)
if(VG_HOST_SANITIZERS)
  if(CMAKE_CROSSCOMPILING)
    message(FATAL_ERROR "Host sanitizers cannot validate Vita")
  endif()
  add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
  add_link_options(-fsanitize=address,undefined)
endif()

# Input and output hashes make stale or approximate patches a configure failure.
execute_process(COMMAND ${Python3_EXECUTABLE}
  ${CMAKE_CURRENT_SOURCE_DIR}/tools/stage_original.py --output ${CMAKE_BINARY_DIR}/staged
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} RESULT_VARIABLE VG_STAGE_RESULT)
if(NOT VG_STAGE_RESULT EQUAL 0)
  message(FATAL_ERROR "Original source staging failed")
endif()
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
  vendor/ea/manifest.json tools/stage_original.py)
execute_process(COMMAND ${Python3_EXECUTABLE} -c
  "import json; m=json.load(open('vendor/ea/manifest.json')); print(';'.join(['vendor/ea/'+r['path'] for r in m['files']]+[r['path'] for r in m['patches']]))"
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
  OUTPUT_VARIABLE VG_STAGE_INPUTS OUTPUT_STRIP_TRAILING_WHITESPACE
  RESULT_VARIABLE VG_STAGE_INPUT_RESULT)
if(NOT VG_STAGE_INPUT_RESULT EQUAL 0)
  message(FATAL_ERROR "Cannot enumerate pinned staging inputs")
endif()
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${VG_STAGE_INPUTS})

add_library(vg_archive STATIC src/big_header.c)
target_include_directories(vg_archive PUBLIC src)
target_compile_options(vg_archive PRIVATE -Wall -Wextra -Werror)
add_library(vg_original_crc STATIC ${CMAKE_BINARY_DIR}/staged/wwlib/realcrc.cpp)
target_include_directories(vg_original_crc PUBLIC ${CMAKE_BINARY_DIR}/staged/wwlib)
target_compile_options(vg_original_crc PRIVATE -Wall -Wextra -Werror)
add_executable(original_crc_probe tests/original_crc_test.cpp)
target_link_libraries(original_crc_probe PRIVATE vg_original_crc)
target_compile_options(original_crc_probe PRIVATE -Wall -Wextra -Werror)
add_executable(big_header_test tests/big_header_test.c)
target_link_libraries(big_header_test PRIVATE vg_archive)
target_compile_options(big_header_test PRIVATE -Wall -Wextra -Werror)
add_executable(original_math_validity_probe tests/original_math_validity_test.cpp)
target_include_directories(original_math_validity_probe SYSTEM PRIVATE
  ${CMAKE_BINARY_DIR}/staged/wwmath ${CMAKE_BINARY_DIR}/staged/wwlib)
# Use the actual standard allocation declarations in this focused header probe.
target_compile_definitions(original_math_validity_probe PRIVATE _OPERATOR_NEW_DEFINED_ __cdecl=)
target_compile_options(original_math_validity_probe PRIVATE -Wall -Wextra -Werror -Wno-unknown-pragmas)

if(CMAKE_CROSSCOMPILING)
  add_library(vg_vita_abi OBJECT src/vita_abi.c)
  foreach(VG_TARGET vg_archive vg_original_crc original_crc_probe big_header_test vg_vita_abi original_math_validity_probe)
    target_compile_options(${VG_TARGET} PRIVATE -mcpu=cortex-a9 -mthumb -mfpu=neon -mfloat-abi=hard)
  endforeach()
  target_compile_options(vg_vita_abi PRIVATE -Wall -Wextra -Werror)
  target_sources(original_crc_probe PRIVATE $<TARGET_OBJECTS:vg_vita_abi>)
  target_sources(big_header_test PRIVATE $<TARGET_OBJECTS:vg_vita_abi>)
  target_sources(original_math_validity_probe PRIVATE $<TARGET_OBJECTS:vg_vita_abi>)
  target_link_libraries(original_math_validity_probe PRIVATE SceLibKernel_stub)
  target_link_options(original_math_validity_probe PRIVATE -Wl,-Map,${CMAKE_BINARY_DIR}/original_math_validity_probe.map)
  add_custom_command(TARGET original_math_validity_probe POST_BUILD
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/check_vita_abi.py
      $<TARGET_FILE:original_math_validity_probe> VERBATIM)
  target_link_libraries(big_header_test PRIVATE SceLibKernel_stub)
  target_link_options(big_header_test PRIVATE -Wl,-Map,${CMAKE_BINARY_DIR}/big_header_test.map)
  target_link_libraries(original_crc_probe PRIVATE SceLibKernel_stub)
  target_link_options(original_crc_probe PRIVATE -Wl,-Map,${CMAKE_BINARY_DIR}/original_crc_probe.map)
  add_dependencies(vg_archive vg_vita_abi)
  add_custom_command(TARGET vg_archive POST_BUILD
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/check_vita_abi.py
      $<TARGET_OBJECTS:vg_vita_abi> $<TARGET_FILE:vg_archive>
    COMMAND_EXPAND_LISTS VERBATIM)
  add_custom_command(TARGET original_crc_probe POST_BUILD
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/check_vita_abi.py
      $<TARGET_FILE:vg_original_crc> $<TARGET_FILE:original_crc_probe>
    VERBATIM)
  add_custom_command(TARGET big_header_test POST_BUILD
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/check_vita_abi.py
      $<TARGET_FILE:big_header_test>
    VERBATIM)
else()
  add_executable(vita_audio_output_buffers_test
    tests/vita_audio_output_buffers_test.cpp)
  target_include_directories(vita_audio_output_buffers_test PRIVATE
    engine/port/include)
  target_compile_options(vita_audio_output_buffers_test PRIVATE
    -Wall -Wextra -Werror)
  enable_testing()
  add_test(NAME big_header_boundary COMMAND big_header_test)
  add_test(NAME original_crc_boundary COMMAND original_crc_probe)
  add_test(NAME original_math_validity COMMAND original_math_validity_probe)
  add_test(NAME vita_audio_output_buffers COMMAND vita_audio_output_buffers_test)
endif()
