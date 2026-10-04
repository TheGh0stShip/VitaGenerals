# SPDX-License-Identifier: GPL-3.0-or-later
if(CMAKE_CROSSCOMPILING)
  set(GENERALS_ICONV_PREFIX "" CACHE PATH "Verified GNU libiconv recipe output")
  if(NOT EXISTS "${GENERALS_ICONV_PREFIX}/library/include/iconv.h" OR NOT EXISTS "${GENERALS_ICONV_PREFIX}/library/lib/.libs/libiconv.a")
    message(FATAL_ERROR "The full math cluster requires the verified native libiconv build")
  endif()
  add_library(generals_wwmath STATIC
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/aabox.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/aabtreecull.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/cardinalspline.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/catmullromspline.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/colmath.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/colmathaabox.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/colmathaabtri.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/colmathfrustum.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/colmathline.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/colmathobbobb.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/colmathobbox.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/colmathobbtri.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/colmathplane.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/colmathsphere.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/cullsys.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/curve.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/euler.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/frustum.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/gridcull.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/hermitespline.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/lineseg.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/lookuptable.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/matrix3.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/matrix3d.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/matrix4.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/obbox.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/ode.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/pot.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/quat.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/tcbspline.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/tri.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/v3_rnd.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/vehiclecurve.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/vp.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/wwmath.cpp
  )
  add_library(generals_wwmath_providers STATIC
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/chunkio.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/multilist.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad/persistfactory.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad/pointerremap.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/random.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/wwstring.cpp
    port/src/ansi-conversion.cpp
    port/src/native-thread-yield.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad/saveload.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/systimer.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/slnode.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad/saveloadstatus.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/mutex.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad/twiddler.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad/definition.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad/definitionfactory.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad/saveloadsubsystem.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad/definitionfactorymgr.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad/parameter.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad/definitionmgr.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/rawfile.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/bufffile.cpp
    ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib/ffactory.cpp
    port/src/native-file-time.cpp
  )
  foreach(target generals_wwmath generals_wwmath_providers)
    target_include_directories(${target} PUBLIC
      ${GENERALS_ICONV_PREFIX}/library/include
      port/include
      ${VG_ORIGINAL}/GameEngine/Include/Precompiled
      ${VG_ORIGINAL}/GameEngine/Include ${VG_ORIGINAL}/Libraries/Include
      ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath
      ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWLib
      ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWDebug
      ${VG_ORIGINAL}/Libraries/Source/WWVegas/WWSaveLoad)
    target_compile_definitions(${target} PUBLIC GENERALS_PLATFORM_VITA __DYNAMIC_REENT__
      NDEBUG __cdecl= __forceinline=inline _OPERATOR_NEW_DEFINED_ GENERALS_WWLIB_STDIO
      GENERALS_WWLIB_ANSI_ENCODING="CP1252"
      GENERALS_MEMORY_POOL_CONFIG_PATH="${GENERALS_MEMORY_POOL_CONFIG_PATH}")
    target_compile_options(${target} PUBLIC -mcpu=cortex-a9 -mthumb -mfpu=neon -mfloat-abi=hard)
    add_custom_command(TARGET ${target} POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E env VITASDK=${VITASDK}
        ${Python3_EXECUTABLE} ${VG_PROJECT_ROOT}/tools/check_vita_abi.py $<TARGET_FILE:${target}> VERBATIM)
  endforeach()
  set_source_files_properties(${VG_ORIGINAL}/Libraries/Source/WWVegas/WWMath/matrix3d.cpp
    PROPERTIES COMPILE_OPTIONS "-ffp-contract=off")
  add_executable(wwmath_link_entry wwmath-link-entry.cpp)
  target_link_libraries(wwmath_link_entry PRIVATE
    -Wl,--whole-archive generals_wwmath generals_wwmath_providers -Wl,--no-whole-archive
    ${GENERALS_ICONV_PREFIX}/library/lib/.libs/libiconv.a SceLibKernel_stub)
  target_link_options(wwmath_link_entry PRIVATE -Wl,-Map,${CMAKE_CURRENT_BINARY_DIR}/wwmath_link_entry.map)
  add_custom_command(TARGET wwmath_link_entry POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E env VITASDK=${VITASDK}
      ${Python3_EXECUTABLE} ${VG_PROJECT_ROOT}/tools/check_vita_abi.py
      $<TARGET_FILE:wwmath_link_entry> VERBATIM)
endif()
