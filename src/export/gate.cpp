#include "gate.hpp"

#include "watertight.hpp"

#include <algorithm>
#include <string>

bool export_units_pass(const char* storage, const char* threemf, const char* stl) {
    if (storage == nullptr || threemf == nullptr || stl == nullptr) {
        return false;
    }
    const std::string storage_unit(storage);
    const std::string threemf_unit(threemf);
    const std::string stl_unit(stl);
    return storage_unit == "millimeter" && threemf_unit == "millimeter" && stl_unit == "millimeter";
}

double mesh_volume_mm3(const MeshSolid& mesh) {
    double sum = 0.0;
    const auto count = mesh.vertices.size();
    for (const auto& triangle : mesh.triangles) {
        if (triangle[0] >= count || triangle[1] >= count || triangle[2] >= count) {
            continue;
        }
        const Vec3& a = mesh.vertices[triangle[0]];
        const Vec3& b = mesh.vertices[triangle[1]];
        const Vec3& c = mesh.vertices[triangle[2]];
        const double cx = b.y * c.z - b.z * c.y;
        const double cy = b.z * c.x - b.x * c.z;
        const double cz = b.x * c.y - b.y * c.x;
        sum += a.x * cx + a.y * cy + a.z * cz;
    }
    return sum / 6.0;
}

std::string export_block_reason(bool /*watertight_pass*/, const std::string& /*watertight_message*/,
                                bool units_pass, const std::string& units_message) {
    if (!units_pass) {
        return units_message;
    }
    return {};
}

namespace {

void mesh_extents(const MeshSolid& mesh, double& width, double& depth, double& height) {
    width = 0.0;
    depth = 0.0;
    height = 0.0;
    if (mesh.vertices.empty()) {
        return;
    }
    double min_x = mesh.vertices[0].x;
    double min_y = mesh.vertices[0].y;
    double min_z = mesh.vertices[0].z;
    double max_x = min_x;
    double max_y = min_y;
    double max_z = min_z;
    for (const Vec3& vertex : mesh.vertices) {
        min_x = std::min(min_x, vertex.x);
        min_y = std::min(min_y, vertex.y);
        min_z = std::min(min_z, vertex.z);
        max_x = std::max(max_x, vertex.x);
        max_y = std::max(max_y, vertex.y);
        max_z = std::max(max_z, vertex.z);
    }
    width = max_x - min_x;
    depth = max_y - min_y;
    height = max_z - min_z;
}

}  // namespace

GateReport evaluate_export_gate(const MeshSolid& mesh, const UnitLock& lock) {
    GateReport report;
    const WatertightResult check = check_watertight(mesh);
    report.watertight_pass = check.pass;
    report.watertight_message = check.message;

    const ExportUnitRecord record = export_units(lock);
    report.export_unit = record.storage;
    report.units_pass = export_units_pass(record.storage, record.threemf_unit, record.stl_coordinate_unit);
    report.units_message = report.units_pass ? "PASS: export unit is millimeter."
                                             : "FAIL: export unit is not millimeter.";
    report.display_unit = lock.display() == DisplayUnit::Inch ? "in" : "mm";
    report.volume_mm3 = mesh_volume_mm3(mesh);
    mesh_extents(mesh, report.width_mm, report.depth_mm, report.height_mm);
    report.block_reason = export_block_reason(report.watertight_pass, report.watertight_message,
                                              report.units_pass, report.units_message);
    report.export_allowed = report.units_pass;
    return report;
}
