cmake_minimum_required(VERSION 3.16)
project(cadcam_web LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Single-threaded Emscripten build. Do not pass -pthread.
# GitHub Pages cannot send COOP/COEP, which threads would need.
if(NOT EMSCRIPTEN)
    message(FATAL_ERROR "Configure this directory with emcmake. See web/BUILD.md.")
endif()

add_executable(cadcam
    bindings.cpp
    ../src/solid/mesh.cpp
    ../src/solid/watertight.cpp
    ../src/units/units.cpp
    ../src/export/box.cpp
    ../src/export/stl.cpp
    ../src/export/threemf.cpp
    ../src/export/bed_orient.cpp
    ../src/export/gate.cpp
    ../src/model/shapes.cpp
    ../src/model/repair.cpp
)
target_include_directories(cadcam PRIVATE
    ../src/solid
    ../src/units
    ../src/export
    ../src/model
)

# Glue and wasm land next to index.html. Both are gitignored.
set_target_properties(cadcam PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    OUTPUT_NAME "cadcam"
    SUFFIX ".js"
)

target_link_options(cadcam PRIVATE
    "--bind"
    "SHELL:-sMODULARIZE=1"
    "SHELL:-sEXPORT_NAME=createCadcam"
    "SHELL:-sALLOW_MEMORY_GROWTH=1"
    "SHELL:-sENVIRONMENT=web"
    "SHELL:-sFORCE_FILESYSTEM=1"
    "SHELL:-sNO_EXIT_RUNTIME=1"
    "SHELL:-sNO_DISABLE_EXCEPTION_CATCHING=1"
)
