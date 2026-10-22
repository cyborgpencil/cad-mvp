#include "box.hpp"
#include "export_files.hpp"
#include "fixtures.hpp"
#include "part.hpp"
#include "repair.hpp"
#include "shapes.hpp"
#include "sketch.hpp"
#include "stl.hpp"
#include "units.hpp"
#include "watertight.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

namespace {

int g_failures = 0;

void expect(const char* name, bool ok) {
    if (ok) {
        return;
    }
    std::cerr << name << " failed\n";
    ++g_failures;
}

void expect_pass(const char* name, const MeshSolid& mesh) {
    const WatertightResult result = check_watertight(mesh);
    if (result.pass) {
        return;
    }
    std::cerr << name << " " << result.message << "\n";
    ++g_failures;
}

void bounds(const MeshSolid& mesh, double& min_x, double& min_y, double& min_z, double& max_x, double& max_y,
            double& max_z) {
    min_x = max_x = mesh.vertices[0].x;
    min_y = max_y = mesh.vertices[0].y;
    min_z = max_z = mesh.vertices[0].z;
    for (const Vec3& vertex : mesh.vertices) {
        min_x = std::min(min_x, vertex.x);
        min_y = std::min(min_y, vertex.y);
        min_z = std::min(min_z, vertex.z);
        max_x = std::max(max_x, vertex.x);
        max_y = std::max(max_y, vertex.y);
        max_z = std::max(max_z, vertex.z);
    }
}

}  // namespace

int main() {
    const MeshSolid box = box_mm(40.0, 30.0, 20.0);
    expect_pass("box", box);
    double min_x, min_y, min_z, max_x, max_y, max_z;
    bounds(box, min_x, min_y, min_z, max_x, max_y, max_z);
    expect("box size", max_x - min_x == 40.0 && max_y - min_y == 30.0 && max_z - min_z == 20.0);

    const MeshSolid cylinder = cylinder_mm(0.0, 0.0, 5.0, 12.0, 16);
    expect_pass("cylinder", cylinder);
    bounds(cylinder, min_x, min_y, min_z, max_x, max_y, max_z);
    expect("cylinder size", std::fabs((max_x - min_x) - 10.0) < 1e-6 && std::fabs((max_y - min_y) - 10.0) < 1e-6 &&
                                max_z - min_z == 12.0);

    Sketch sketch;
    sketch.add_rectangle(0.0, 0.0, 40.0, 30.0);
    const int spur = sketch.add_line(60.0, 4.0, 66.0, 9.0);
    sketch.add_horizontal(spur);
    sketch.add_distance(sketch.lines[static_cast<std::size_t>(spur)].a,
                        sketch.lines[static_cast<std::size_t>(spur)].b, 8.0);
    const int other = sketch.add_line(70.0, 1.0, 74.0, 3.0);
    sketch.add_coincident(sketch.lines[static_cast<std::size_t>(spur)].a,
                          sketch.lines[static_cast<std::size_t>(other)].a);
    sketch.add_vertical(other);
    const int circle = sketch.add_circle(55.0, 15.0, 4.0);
    sketch.add_radius(circle, 5.0);
    sketch.solve();
    const Sketch::Line& spur_line = sketch.lines[static_cast<std::size_t>(spur)];
    const double spur_dx = sketch.points[static_cast<std::size_t>(spur_line.b)].x -
                           sketch.points[static_cast<std::size_t>(spur_line.a)].x;
    const double spur_dy = sketch.points[static_cast<std::size_t>(spur_line.b)].y -
                           sketch.points[static_cast<std::size_t>(spur_line.a)].y;
    expect("horizontal distance", std::fabs(spur_dy) < 1e-9 && std::fabs(std::fabs(spur_dx) - 8.0) < 1e-9);
    expect("coincident", sketch.points[static_cast<std::size_t>(spur_line.a)].x ==
                                 sketch.points[static_cast<std::size_t>(sketch.lines[static_cast<std::size_t>(other)].a)].x &&
                             sketch.points[static_cast<std::size_t>(spur_line.a)].y ==
                                 sketch.points[static_cast<std::size_t>(sketch.lines[static_cast<std::size_t>(other)].a)].y);
    expect("vertical", std::fabs(sketch.points[static_cast<std::size_t>(sketch.lines[static_cast<std::size_t>(other)].a)].x -
                            sketch.points[static_cast<std::size_t>(sketch.lines[static_cast<std::size_t>(other)].b)].x) < 1e-9);
    expect("radius", sketch.circles[static_cast<std::size_t>(circle)].radius == 5.0);
    const ExtrudeResult extruded = extrude_sketch(sketch, 20.0);
    expect("extrude ok", extruded.ok);
    expect_pass("extrude", extruded.mesh);
    bounds(extruded.mesh, min_x, min_y, min_z, max_x, max_y, max_z);
    expect("extrude mm extent", std::fabs(min_x) < 1e-6 && std::fabs(min_y) < 1e-6 && std::fabs(min_z) < 1e-6 &&
                                    std::fabs(max_x - 60.0) < 1e-6 && std::fabs(max_y - 30.0) < 1e-6 &&
                                    std::fabs(max_z - 20.0) < 1e-6);

    const MeshSolid extruded_union = mesh_union(extruded.mesh, cylinder);
    expect_pass("extrude union cylinder", extruded_union);
    bounds(extruded_union, min_x, min_y, min_z, max_x, max_y, max_z);
    expect("extrude union mm extent", std::fabs(min_x - (-5.0)) < 1e-6 && std::fabs(min_y - (-5.0)) < 1e-6 &&
                                          std::fabs(min_z) < 1e-6 && std::fabs(max_x - 60.0) < 1e-6 &&
                                          std::fabs(max_y - 30.0) < 1e-6 && std::fabs(max_z - 20.0) < 1e-6);

    const MeshSolid beside = translate_mesh(box_mm(10.0, 10.0, 10.0), 50.0, 0.0, 0.0);
    const MeshSolid united = mesh_union(box, beside);
    expect_pass("union", united);
    bounds(united, min_x, min_y, min_z, max_x, max_y, max_z);
    expect("union mm extent", min_x == 0.0 && min_y == 0.0 && min_z == 0.0 && max_x == 60.0 && max_y == 30.0 &&
                                  max_z == 20.0);
    const MeshSolid overlap = translate_mesh(box_mm(10.0, 10.0, 10.0), 30.0, 0.0, 0.0);
    expect_pass("union overlap", mesh_union(box, overlap));

    const auto box_unchanged = [](const MeshSolid& mesh) {
        double bmin_x, bmin_y, bmin_z, bmax_x, bmax_y, bmax_z;
        bounds(mesh, bmin_x, bmin_y, bmin_z, bmax_x, bmax_y, bmax_z);
        return mesh.vertices.size() == 8 && mesh.triangles.size() == 12 && bmin_x == 0.0 && bmin_y == 0.0 &&
               bmin_z == 0.0 && bmax_x == 40.0 && bmax_y == 30.0 && bmax_z == 20.0;
    };
    const FilletResult edge12 = fillet_box_edge(box, 1, 2, 3.0);
    expect("edge 1-2 rejected", !edge12.ok && edge12.mesh.triangles.empty() &&
                                    edge12.message.find("cannot fillet:") == 0);
    expect("edge 1-2 leaves box", box_unchanged(box));
    const FilletResult edge37 = fillet_box_edge(box, 3, 7, 3.0);
    expect("edge 3-7 rejected", !edge37.ok && edge37.mesh.triangles.empty() &&
                                    edge37.message.find("cannot fillet:") == 0);
    expect("edge 3-7 leaves box", box_unchanged(box));

    const FilletResult filleted = fillet_box_edge(box, 4, 5, 3.0);
    if (!filleted.ok) {
        std::cerr << "fillet " << filleted.message << "\n";
    }
    expect("fillet ok", filleted.ok);
    expect_pass("fillet", filleted.mesh);
    const MeshSolid cutter = translate_mesh(box_mm(8.0, 8.0, 6.0), 16.0, 12.0, 7.0);
    const CutResult cut = mesh_cut(filleted.mesh, cutter);
    if (!cut.ok) {
        std::cerr << "cut " << cut.message << "\n";
    }
    expect("cut ok", cut.ok);
    expect_pass("fillet then cut", cut.mesh);
    const double stored_x = cut.mesh.vertices[0].x;
    UnitLock units;
    units.toggle();
    expect("display inches", units.to_display(stored_x) == stored_x / 25.4);
    expect("stored mm", cut.mesh.vertices[0].x == stored_x);
    expect("back to mm", units.to_millimeters(units.to_display(25.4)) == 25.4);

    const RepairResult open = repair_manifold(open_box());
    expect("open cannot repair", !open.pass && open.message.find("cannot repair:") == 0);
    const std::filesystem::path blocked =
        std::filesystem::temp_directory_path() / "cadcam-mvp-create-blocked";
    std::error_code error;
    std::filesystem::remove_all(blocked, error);
    const ExportAttempt blocked_export = export_mesh_if_closed(open.mesh, blocked);
    expect("failed repair does not write", !blocked_export.wrote && !std::filesystem::exists(blocked));

    MeshSolid inward = box;
    for (auto& triangle : inward.triangles) {
        std::swap(triangle[1], triangle[2]);
    }
    const RepairResult flipped = repair_manifold(inward);
    expect("inward repairs", flipped.pass && flipped.changed);

    const MeshSolid demo = build_demo_part();
    expect_pass("demo", demo);
    const std::filesystem::path exported =
        std::filesystem::temp_directory_path() / "cadcam-mvp-create-export";
    std::filesystem::remove_all(exported, error);
    const ExportAttempt wrote = export_mesh_if_closed(demo, exported);
    expect("demo export", wrote.wrote && wrote.check.pass);
    MeshSolid loaded;
    expect("demo stl", read_binary_stl(wrote.stl_path, loaded));
    bounds(demo, min_x, min_y, min_z, max_x, max_y, max_z);
    double l_min_x, l_min_y, l_min_z, l_max_x, l_max_y, l_max_z;
    bounds(loaded, l_min_x, l_min_y, l_min_z, l_max_x, l_max_y, l_max_z);
    expect("stl extent", std::fabs((l_max_x - l_min_x) - (max_x - min_x)) < 1e-4 &&
                             std::fabs((l_max_y - l_min_y) - (max_y - min_y)) < 1e-4 &&
                             std::fabs((l_max_z - l_min_z) - (max_z - min_z)) < 1e-4);
    std::ifstream threemf(wrote.threemf_path, std::ios::binary);
    std::ostringstream buffer;
    buffer << threemf.rdbuf();
    expect("3mf unit", buffer.str().find("unit=\"millimeter\"") != std::string::npos);
    std::filesystem::remove_all(exported, error);

    if (g_failures != 0) {
        std::cerr << g_failures << " failed\n";
        return EXIT_FAILURE;
    }
    std::cout << "ok\n";
    return EXIT_SUCCESS;
}
