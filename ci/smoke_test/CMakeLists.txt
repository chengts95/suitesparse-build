cmake_minimum_required(VERSION 3.20)
project(klu_smoke C)

# Allow passing install prefix via CMAKE_PREFIX_PATH
find_package(SuiteSparse CONFIG QUIET COMPONENTS KLU)

if(TARGET SuiteSparse::KLU)
    message(STATUS "Found SuiteSparse::KLU target via CMake config")
    add_executable(klu_smoke_shared klu_smoke.c)
    target_link_libraries(klu_smoke_shared PRIVATE SuiteSparse::KLU)
    if(UNIX AND NOT APPLE)
        target_link_libraries(klu_smoke_shared PRIVATE m)
    endif()
endif()

if(TARGET SuiteSparse::KLU_static)
    message(STATUS "Found SuiteSparse::KLU_static target via CMake config")
    add_executable(klu_smoke_static klu_smoke.c)
    target_link_libraries(klu_smoke_static PRIVATE SuiteSparse::KLU_static)
    if(UNIX AND NOT APPLE)
        target_link_libraries(klu_smoke_static PRIVATE m)
    endif()
endif()

# Fallback: direct library search
find_path(KLU_INC NAMES klu.h PATHS "${CMAKE_PREFIX_PATH}/include" "${CMAKE_PREFIX_PATH}/include/suitesparse" NO_DEFAULT_PATH)

if(WIN32)
    find_library(KLU_STATIC_LIB NAMES klu_static klu PATHS "${CMAKE_PREFIX_PATH}/lib" NO_DEFAULT_PATH)
    find_library(BTF_STATIC_LIB NAMES btf_static btf PATHS "${CMAKE_PREFIX_PATH}/lib" NO_DEFAULT_PATH)
    find_library(COLAMD_STATIC_LIB NAMES colamd_static colamd PATHS "${CMAKE_PREFIX_PATH}/lib" NO_DEFAULT_PATH)
    find_library(AMD_STATIC_LIB NAMES amd_static amd PATHS "${CMAKE_PREFIX_PATH}/lib" NO_DEFAULT_PATH)
    find_library(CONFIG_STATIC_LIB NAMES suitesparseconfig_static suitesparseconfig PATHS "${CMAKE_PREFIX_PATH}/lib" NO_DEFAULT_PATH)
else()
    find_library(KLU_STATIC_LIB NAMES libklu.a klu PATHS "${CMAKE_PREFIX_PATH}/lib" NO_DEFAULT_PATH)
    find_library(BTF_STATIC_LIB NAMES libbtf.a btf PATHS "${CMAKE_PREFIX_PATH}/lib" NO_DEFAULT_PATH)
    find_library(COLAMD_STATIC_LIB NAMES libcolamd.a colamd PATHS "${CMAKE_PREFIX_PATH}/lib" NO_DEFAULT_PATH)
    find_library(AMD_STATIC_LIB NAMES libamd.a amd PATHS "${CMAKE_PREFIX_PATH}/lib" NO_DEFAULT_PATH)
    find_library(CONFIG_STATIC_LIB NAMES libsuitesparseconfig.a suitesparseconfig PATHS "${CMAKE_PREFIX_PATH}/lib" NO_DEFAULT_PATH)
endif()

if(KLU_STATIC_LIB AND KLU_INC)
    message(STATUS "Configuring direct static test with ${KLU_STATIC_LIB}")
    add_executable(klu_smoke_direct klu_smoke.c)
    target_include_directories(klu_smoke_direct PRIVATE ${KLU_INC})
    target_link_libraries(klu_smoke_direct PRIVATE
        ${KLU_STATIC_LIB}
        ${BTF_STATIC_LIB}
        ${COLAMD_STATIC_LIB}
        ${AMD_STATIC_LIB}
        ${CONFIG_STATIC_LIB}
    )
    if(UNIX AND NOT APPLE)
        target_link_libraries(klu_smoke_direct PRIVATE m)
    endif()
endif()
