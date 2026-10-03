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
  vendor/ea/manifest.json vendor/ea/wwlib/realcrc.cpp vendor/ea/wwlib/realcrc.h
  port/patches/realcrc-width.patch tools/stage_original.py)

add_library(vg_archive STATIC src/big_header.c)
target_include_directories(vg_archive PUBLIC src)
target_compile_options(vg_archive PRIVATE -Wall -Wextra -Werror)
add_library(vg_original_crc STATIC ${CMAKE_BINARY_DIR}/staged/wwlib/realcrc.cpp)
target_include_directories(vg_original_crc PUBLIC ${CMAKE_BINARY_DIR}/staged/wwlib)
target_compile_options(vg_original_crc PRIVATE -Wall -Wextra -Werror)
add_executable(original_crc_probe tests/original_crc_test.cpp)
target_link_libraries(original_crc_probe PRIVATE vg_original_crc)
target_compile_options(original_crc_probe PRIVATE -Wall -Wextra -Werror)

if(CMAKE_CROSSCOMPILING)
  add_library(vg_vita_abi OBJECT src/vita_abi.c)
  foreach(VG_TARGET vg_archive vg_original_crc original_crc_probe vg_vita_abi)
    target_compile_options(${VG_TARGET} PRIVATE -mcpu=cortex-a9 -mthumb -mfpu=neon -mfloat-abi=hard)
  endforeach()
  target_compile_options(vg_vita_abi PRIVATE -Wall -Wextra -Werror)
  target_sources(original_crc_probe PRIVATE $<TARGET_OBJECTS:vg_vita_abi>)
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
else()
  enable_testing()
  add_executable(big_header_test tests/big_header_test.c)
  target_link_libraries(big_header_test PRIVATE vg_archive)
  target_compile_options(big_header_test PRIVATE -Wall -Wextra -Werror)
  add_test(NAME big_header_boundary COMMAND big_header_test)
  add_test(NAME original_crc_boundary COMMAND original_crc_probe)
endif()
