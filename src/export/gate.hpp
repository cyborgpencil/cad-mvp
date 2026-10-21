#pragma once

#include "mesh.hpp"
#include "units.hpp"

#include <string>

// Export gate for the WASM page and the native test.
// Watertight PASS/FAIL is check_watertight, unchanged.
// Volume is the documented triple sum divided by 6 (mvp/solid-check.md).
// The export unit comes from ExportUnitRecord and stays millimeter.

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

// First failing rule wins: the watertight sentence, else the units sentence.
// Empty when both pass.
std::string export_block_reason(bool watertight_pass, const std::string& watertight_message,
                                bool units_pass, const std::string& units_message);

GateReport evaluate_export_gate(const MeshSolid& mesh, const UnitLock& lock);
