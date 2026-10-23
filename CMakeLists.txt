cmake_minimum_required(VERSION 3.16)
project(cadcam_mvp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(solid
    src/solid/mesh.cpp
    src/solid/watertight.cpp
)
target_include_directories(solid PUBLIC src/solid)

add_executable(check_solid src/check_solid.cpp)
target_link_libraries(check_solid PRIVATE solid)

add_executable(test_watertight tests/test_watertight.cpp)
target_link_libraries(test_watertight PRIVATE solid)

enable_testing()
add_test(NAME watertight COMMAND test_watertight)

add_library(units
    src/units/units.cpp
)
target_include_directories(units PUBLIC src/units)

add_executable(test_units tests/test_units.cpp)
target_link_libraries(test_units PRIVATE units)
add_test(NAME units COMMAND test_units)

add_library(export_mesh
    src/export/box.cpp
    src/export/stl.cpp
    src/export/threemf.cpp
    src/export/export_files.cpp
    src/export/gate.cpp
)
target_include_directories(export_mesh PUBLIC src/export)
target_link_libraries(export_mesh PUBLIC solid units)

add_executable(export_box src/export_box.cpp)
target_link_libraries(export_box PRIVATE export_mesh)

add_executable(test_export tests/test_export.cpp)
target_link_libraries(test_export PRIVATE export_mesh)
add_test(NAME export COMMAND test_export)

add_executable(test_gate tests/test_gate.cpp)
target_link_libraries(test_gate PRIVATE export_mesh)
add_test(NAME gate COMMAND test_gate)

# OCCT gate is JS-side libcascade (BRepCheck_Analyzer + ShapeAnalysis_FreeBounds).
# Always register it when Node exists. tests/test_occt_gate.mjs exits 1 when
# libcascade is missing and CI or GITHUB_ACTIONS is set, and exits 77 otherwise.
# CTest treats 77 as a skip. Missing Node fails configure in CI and is a local skip.
find_program(CADCAM_NODE node
    PATHS
        "${CMAKE_SOURCE_DIR}/builds/emsdk/node/24.19.0_64bit"
        "${CMAKE_SOURCE_DIR}/builds/emsdk/node/24.19.0_64bit/bin"
        "${CMAKE_SOURCE_DIR}/../cadcam-mvp/builds/emsdk/node/24.19.0_64bit"
    NO_DEFAULT_PATH
)
if(NOT CADCAM_NODE)
    find_program(CADCAM_NODE node)
endif()
if(CADCAM_NODE)
    add_test(NAME occt_gate COMMAND "${CADCAM_NODE}" "${CMAKE_SOURCE_DIR}/tests/test_occt_gate.mjs")
    set_tests_properties(occt_gate PROPERTIES
        TIMEOUT 180
        SKIP_RETURN_CODE 77
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    )
elseif(DEFINED ENV{CI} OR DEFINED ENV{GITHUB_ACTIONS})
    message(FATAL_ERROR
        "occt_gate requires Node. CI must not skip this test when libcascade or Node is missing.")
else()
    message(STATUS
        "occt_gate skipped locally: Node was not found (would be SKIP_RETURN_CODE 77).")
endif()

# Face and fillet delete. tests/test_delete.mjs builds its own 40x20x10 mm
# box with a 6 mm hole. Exit 77 when libcascade is missing and CI is unset.
if(CADCAM_NODE)
    add_test(NAME delete_shape COMMAND "${CADCAM_NODE}" "${CMAKE_SOURCE_DIR}/tests/test_delete.mjs")
    set_tests_properties(delete_shape PROPERTIES
        TIMEOUT 180
        SKIP_RETURN_CODE 77
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    )
elseif(DEFINED ENV{CI} OR DEFINED ENV{GITHUB_ACTIONS})
    message(FATAL_ERROR
        "delete_shape requires Node. CI must not skip this test when libcascade or Node is missing.")
else()
    message(STATUS
        "delete_shape skipped locally: Node was not found (would be SKIP_RETURN_CODE 77).")
endif()

# Flat parts list, Combine, and one 3MF object per part.
# tests/test_assemblies.mjs exits 77 when libcascade is missing and CI is unset.
if(CADCAM_NODE)
    add_test(NAME assemblies COMMAND "${CADCAM_NODE}" "${CMAKE_SOURCE_DIR}/tests/test_assemblies.mjs")
    set_tests_properties(assemblies PROPERTIES
        TIMEOUT 180
        SKIP_RETURN_CODE 77
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    )
elseif(DEFINED ENV{CI} OR DEFINED ENV{GITHUB_ACTIONS})
    message(FATAL_ERROR
        "assemblies requires Node. CI must not skip this test when libcascade or Node is missing.")
else()
    message(STATUS
        "assemblies skipped locally: Node was not found (would be SKIP_RETURN_CODE 77).")
endif()

# View-cube swipe face table and tap threshold. Pure JS, no libcascade.
if(CADCAM_NODE)
    add_test(NAME view_cube COMMAND "${CADCAM_NODE}" "${CMAKE_SOURCE_DIR}/tests/test_view_cube.mjs")
    set_tests_properties(view_cube PROPERTIES
        TIMEOUT 30
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    )
elseif(DEFINED ENV{CI} OR DEFINED ENV{GITHUB_ACTIONS})
    message(FATAL_ERROR
        "view_cube requires Node. CI must not skip this test when Node is missing.")
else()
    message(STATUS "view_cube skipped locally: Node was not found.")
endif()

# Pages file set in headless Edge/Chromium. The script exits 77 only when
# the browser or libcascade is missing and CI is unset. CI must not skip.
# gizmo_drag_smoke exits 77 when Playwright cannot be imported. Prefer the
# sibling pwvenv when it exists so a local run is not that skip. CI without
# that tree still finds python3 and treats exit 77 as a skip.
if(NOT CADCAM_PYTHON)
    set(_cadcam_pwvenv "${CMAKE_SOURCE_DIR}/../cadcam-mvp/builds/pwvenv/Scripts/python.exe")
    if(EXISTS "${_cadcam_pwvenv}")
        set(CADCAM_PYTHON "${_cadcam_pwvenv}" CACHE FILEPATH "Python interpreter for smoke tests")
    endif()
endif()
if(NOT CADCAM_PYTHON)
    find_program(CADCAM_PYTHON NAMES python3 python py)
endif()
if(CADCAM_PYTHON)
    add_test(
        NAME deploy_smoke
        COMMAND "${CADCAM_PYTHON}" "${CMAKE_SOURCE_DIR}/tests/deploy_smoke.py"
    )
    set_tests_properties(deploy_smoke PROPERTIES
        TIMEOUT 600
        SKIP_RETURN_CODE 77
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    )
    add_test(
        NAME gizmo_drag_smoke
        COMMAND "${CADCAM_PYTHON}" "${CMAKE_SOURCE_DIR}/tests/gizmo_drag_smoke.py"
    )
    set_tests_properties(gizmo_drag_smoke PROPERTIES
        TIMEOUT 600
        SKIP_RETURN_CODE 77
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    )
    add_test(
        NAME view_cube_swipe_smoke
        COMMAND "${CADCAM_PYTHON}" "${CMAKE_SOURCE_DIR}/tests/view_cube_swipe_smoke.py"
    )
    set_tests_properties(view_cube_swipe_smoke PROPERTIES
        TIMEOUT 600
        SKIP_RETURN_CODE 77
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    )
elseif(DEFINED ENV{CI})
    message(FATAL_ERROR "deploy_smoke, gizmo_drag_smoke, and view_cube_swipe_smoke require Python; CI must not skip them")
else()
    message(STATUS "deploy_smoke, gizmo_drag_smoke, and view_cube_swipe_smoke not added: Python was not found")
endif()

add_library(model
    src/model/shapes.cpp
    src/model/sketch.cpp
    src/model/repair.cpp
    src/model/part.cpp
)
target_include_directories(model PUBLIC src/model)
target_link_libraries(model PUBLIC solid export_mesh)

add_executable(test_create tests/test_create.cpp)
target_link_libraries(test_create PRIVATE model)
add_test(NAME create COMMAND test_create)

add_executable(export_part src/export_part.cpp)
target_link_libraries(export_part PRIVATE model)

find_package(Qt6 QUIET COMPONENTS Widgets OpenGLWidgets)
if(Qt6_FOUND)
    add_executable(solid_view
        src/gui/main.cpp
        src/gui/main_window.cpp
        src/gui/mesh_view.cpp
    )
    target_link_libraries(solid_view PRIVATE model Qt6::Widgets Qt6::OpenGLWidgets)
    if(WIN32)
        target_link_libraries(solid_view PRIVATE opengl32)
    endif()
endif()
