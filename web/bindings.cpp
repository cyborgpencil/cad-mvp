#include "box.hpp"
#include "fixtures.hpp"
#include "gate.hpp"
#include "repair.hpp"
#include "stl.hpp"
#include "threemf.hpp"
#include "watertight.hpp"

#include <emscripten.h>
#include <emscripten/bind.h>

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace {

// Create > Box is centred on XY with z from 0 to 20. box_mm() stays
// corner-at-origin in src/. This translation is the web default only.
MeshSolid centred_box_20() {
    MeshSolid mesh = box_mm(20.0, 20.0, 20.0);
    for (Vec3& vertex : mesh.vertices) {
        vertex.x -= 10.0;
        vertex.y -= 10.0;
    }
    return mesh;
}

MeshSolid g_mesh = centred_box_20();
UnitLock g_lock;
std::string g_fixture = "default_box";

emscripten::val copy_bytes(const std::string& bytes) {
    emscripten::val view(emscripten::typed_memory_view(bytes.size(), reinterpret_cast<const unsigned char*>(bytes.data())));
    return emscripten::val::global("Uint8Array").new_(view);
}

std::string read_bytes(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        return {};
    }
    std::ostringstream buffer;
    buffer << in.rdbuf();
    return buffer.str();
}

emscripten::val export_file(bool stl, bool lay_on_bed) {
    const GateReport report = evaluate_export_gate(g_mesh, g_lock);
    // Units plus a non-empty, positive-volume mesh. Watertight stays informational.
    // console.warn, not console.error: smoke tests treat console errors as failures.
    if (!report.export_allowed) {
        EM_ASM({ console.warn(UTF8ToString($0)); }, report.block_reason.c_str());
        return emscripten::val::null();
    }
    const char* path = stl ? "/cadcam_export.stl" : "/cadcam_export.3mf";
    const bool wrote = stl ? write_binary_stl(path, g_mesh, lay_on_bed) : write_3mf(path, g_mesh, lay_on_bed);
    if (!wrote) {
        return emscripten::val::null();
    }
    const std::string bytes = read_bytes(path);
    std::error_code error;
    std::filesystem::remove(path, error);
    if (bytes.empty()) {
        return emscripten::val::null();
    }
    return copy_bytes(bytes);
}

}  // namespace

GateReport gate() {
    return evaluate_export_gate(g_mesh, g_lock);
}

bool load_fixture(const std::string& name) {
    if (name == "closed_box") {
        g_mesh = closed_box();
    } else if (name == "open_box") {
        g_mesh = open_box();
    } else if (name == "box20") {
        g_mesh = box_mm(20.0, 20.0, 20.0);
    } else if (name == "flipped_box") {
        g_mesh = flipped_box();
    } else {
        return false;
    }
    g_fixture = name;
    return true;
}

std::string fixture_name() {
    return g_fixture;
}

bool replace_mesh(const emscripten::val& positions, const emscripten::val& indices, const std::string& name) {
    if (positions.isNull() || positions.isUndefined() || indices.isNull() || indices.isUndefined()) {
        return false;
    }
    const unsigned length = positions["length"].as<unsigned>();
    const unsigned index_length = indices["length"].as<unsigned>();
    if (length % 3 != 0 || index_length % 3 != 0 || index_length == 0) {
        return false;
    }
    MeshSolid mesh;
    mesh.vertices.reserve(length / 3);
    for (unsigned i = 0; i + 2 < length; i += 3) {
        mesh.vertices.push_back({
            positions[i].as<double>(),
            positions[i + 1].as<double>(),
            positions[i + 2].as<double>(),
        });
    }
    mesh.triangles.reserve(index_length / 3);
    for (unsigned i = 0; i + 2 < index_length; i += 3) {
        mesh.triangles.push_back({
            indices[i].as<std::uint32_t>(),
            indices[i + 1].as<std::uint32_t>(),
            indices[i + 2].as<std::uint32_t>(),
        });
    }
    g_mesh = std::move(mesh);
    g_fixture = name.empty() ? std::string("mesh") : name;
    return true;
}

GateReport toggle_units() {
    g_lock.toggle();
    return gate();
}

std::string check_shape() {
    return check_watertight(g_mesh).message;
}

std::string find_open_edges() {
    const WatertightResult result = check_watertight(g_mesh);
    if (result.pass) {
        return "Find open edges: none. " + result.message;
    }
    if (result.message.find("shared by 1 triangle") != std::string::npos) {
        return "Find open edges: " + result.message;
    }
    return "Find open edges: no boundary edge. " + result.message;
}

std::string repair_mesh() {
    const RepairResult result = repair_manifold(g_mesh);
    if (result.pass) {
        g_mesh = result.mesh;
    }
    if (result.pass && result.changed) {
        return "Repaired. " + result.message;
    }
    return result.message;
}

emscripten::val mesh_positions() {
    std::vector<double> flat;
    flat.reserve(g_mesh.vertices.size() * 3);
    for (const Vec3& vertex : g_mesh.vertices) {
        flat.push_back(vertex.x);
        flat.push_back(vertex.y);
        flat.push_back(vertex.z);
    }
    emscripten::val view(emscripten::typed_memory_view(flat.size(), flat.data()));
    return emscripten::val::global("Float64Array").new_(view);
}

emscripten::val mesh_indices() {
    std::vector<std::uint32_t> flat;
    flat.reserve(g_mesh.triangles.size() * 3);
    for (const auto& triangle : g_mesh.triangles) {
        flat.push_back(triangle[0]);
        flat.push_back(triangle[1]);
        flat.push_back(triangle[2]);
    }
    emscripten::val view(emscripten::typed_memory_view(flat.size(), flat.data()));
    return emscripten::val::global("Uint32Array").new_(view);
}

emscripten::val export_stl() {
    return export_file(true, true);
}

emscripten::val export_stl_raw() {
    return export_file(true, false);
}

emscripten::val export_3mf() {
    return export_file(false, true);
}

emscripten::val export_3mf_raw() {
    return export_file(false, false);
}

EMSCRIPTEN_BINDINGS(cadcam) {
    emscripten::value_object<GateReport>("GateReport")
        .field("watertightPass", &GateReport::watertight_pass)
        .field("watertightMessage", &GateReport::watertight_message)
        .field("unitsPass", &GateReport::units_pass)
        .field("unitsMessage", &GateReport::units_message)
        .field("meshPass", &GateReport::mesh_pass)
        .field("meshMessage", &GateReport::mesh_message)
        .field("exportUnit", &GateReport::export_unit)
        .field("displayUnit", &GateReport::display_unit)
        .field("volumeMm3", &GateReport::volume_mm3)
        .field("widthMm", &GateReport::width_mm)
        .field("depthMm", &GateReport::depth_mm)
        .field("heightMm", &GateReport::height_mm)
        .field("exportAllowed", &GateReport::export_allowed)
        .field("blockReason", &GateReport::block_reason);

    emscripten::function("gate", &gate);
    emscripten::function("loadFixture", &load_fixture);
    emscripten::function("fixtureName", &fixture_name);
    emscripten::function("replaceMesh", &replace_mesh);
    emscripten::function("toggleUnits", &toggle_units);
    emscripten::function("checkShape", &check_shape);
    emscripten::function("findOpenEdges", &find_open_edges);
    emscripten::function("repairMesh", &repair_mesh);
    emscripten::function("meshPositions", &mesh_positions);
    emscripten::function("meshIndices", &mesh_indices);
    emscripten::function("exportStl", &export_stl);
    emscripten::function("exportStlRaw", &export_stl_raw);
    emscripten::function("export3mf", &export_3mf);
    emscripten::function("export3mfRaw", &export_3mf_raw);
}
