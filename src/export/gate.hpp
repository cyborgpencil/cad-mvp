#pragma once

#include "mesh.hpp"
#include "units.hpp"

#include <string>

// Export gate for the WASM page and the native test.
// Watertight PASS/FAIL is check_watertight, still computed and reported.
// Volume is the documented triple sum divided by 6 (mvp/solid-check.md).
// Export is allowed when the export unit is millimeter (Erik, 2026-10-22).

struct GateReport {
    bool watertight_pass = false;
    std::string watertight_message;
    bool units_pass = false;
    std::string units_message;
    std::string export_unit;
    std::string display_unit;
    double volume_mm3 = 0.0;
    double width_mm = 0.0;
    double depth_mm = 0.0;
    double height_mm = 0.0;
    bool export_allowed = false;
    std::string block_reason;
};

// True only when storage, the 3MF unit, and the STL coordinate unit are all "millimeter".
bool export_units_pass(const char* storage, const char* threemf, const char* stl);

// Signed tetrahedron volume in the same coordinates as the mesh (millimeters).
double mesh_volume_mm3(const MeshSolid& mesh);

// Units sentence when units fail. Empty when units pass.
// Watertight arguments stay on the signature and are ignored.
std::string export_block_reason(bool watertight_pass, const std::string& watertight_message,
                                bool units_pass, const std::string& units_message);

GateReport evaluate_export_gate(const MeshSolid& mesh, const UnitLock& lock);
