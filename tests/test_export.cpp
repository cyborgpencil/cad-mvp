#include "box.hpp"
#include "export_files.hpp"
#include "fixtures.hpp"
#include "stl.hpp"

#include <algorithm>
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

std::filesystem::path fresh_dir(const char* name) {
    const std::filesystem::path dir =
        std::filesystem::temp_directory_path() / "cadcam-mvp-export" / name;
    std::error_code error;
    std::filesystem::remove_all(dir, error);
    return dir;
}

bool contains_unit(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    std::ostringstream buffer;
    buffer << in.rdbuf();
    return buffer.str().find("unit=\"millimeter\"") != std::string::npos;
}

void expect_extent(const MeshSolid& mesh) {
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
    expect("stl extent x", max_x - min_x == 20.0);
    expect("stl extent y", max_y - min_y == 20.0);
    expect("stl extent z", max_z - min_z == 20.0);
}

}  // namespace

int main() {
    const MeshSolid box = box_mm(20.0, 20.0, 20.0);
    const WatertightResult built = check_watertight(box);
    expect("20 mm box passes", built.pass);

    const std::filesystem::path ok_dir = fresh_dir("ok");
    const ExportAttempt wrote = export_mesh_if_closed(box, ok_dir);
    expect("export wrote", wrote.wrote && wrote.check.pass);
    expect("stl exists", std::filesystem::is_regular_file(wrote.stl_path));
    expect("3mf exists", std::filesystem::is_regular_file(wrote.threemf_path));

    MeshSolid loaded;
    expect("stl reads", read_binary_stl(wrote.stl_path, loaded));
    expect("stl triangle count", loaded.triangles.size() == 12);
    if (!loaded.vertices.empty()) {
        expect_extent(loaded);
    } else {
        expect("stl has vertices", false);
    }
    expect("3mf unit", contains_unit(wrote.threemf_path));

    // box_mm rejects a non-positive size and returns no triangles.
    const std::filesystem::path bad_dir = fresh_dir("bad-size");
    const ExportAttempt bad_size = export_mesh_if_closed(box_mm(0.0, 20.0, 20.0), bad_dir);
    expect("bad size check fails", !bad_size.check.pass);
    expect("bad size does not write", !bad_size.wrote);
    expect("bad size stl absent", !std::filesystem::is_regular_file(bad_size.stl_path));
    expect("bad size 3mf absent", !std::filesystem::is_regular_file(bad_size.threemf_path));

    MeshSolid flat;
    flat.vertices = {{0, 0, 0}, {20, 0, 0}, {20, 20, 0}, {0, 20, 0}};
    flat.triangles = {{0, 1, 2}, {0, 2, 3}};
    const std::filesystem::path flat_dir = fresh_dir("flat");
    const ExportAttempt flat_export = export_mesh_if_closed(flat, flat_dir);
    expect("flat has triangles", flat.triangles.size() == 2);
    expect("flat does not write", !flat_export.wrote);
    expect("flat stl absent", !std::filesystem::is_regular_file(flat_export.stl_path));
    expect("flat 3mf absent", !std::filesystem::is_regular_file(flat_export.threemf_path));

    const std::filesystem::path open_dir = fresh_dir("open");
    const ExportAttempt open = export_mesh_if_closed(open_box(), open_dir);
    expect("open box check fails", !open.check.pass);
    expect("open box writes", open.wrote);
    expect("open box stl exists", std::filesystem::is_regular_file(open.stl_path));
    expect("open box 3mf exists", std::filesystem::is_regular_file(open.threemf_path));

    // One reversed face on z = 0 keeps a positive volume, so the file is written.
    const std::filesystem::path flipped_dir = fresh_dir("flipped");
    const ExportAttempt flipped = export_mesh_if_closed(flipped_box(), flipped_dir);
    expect("flipped box check fails", !flipped.check.pass);
    expect("flipped box writes", flipped.wrote);
    expect("flipped box stl exists", std::filesystem::is_regular_file(flipped.stl_path));
    expect("flipped box 3mf exists", std::filesystem::is_regular_file(flipped.threemf_path));

    MeshSolid inside_out = closed_box();
    for (auto& triangle : inside_out.triangles) {
        const auto saved = triangle[1];
        triangle[1] = triangle[2];
        triangle[2] = saved;
    }
    const std::filesystem::path inward_dir = fresh_dir("inside-out");
    const ExportAttempt inward = export_mesh_if_closed(inside_out, inward_dir);
    expect("inside-out check fails", !inward.check.pass);
    expect("inside-out does not write", !inward.wrote);
    expect("inside-out stl absent", !std::filesystem::is_regular_file(inward.stl_path));
    expect("inside-out 3mf absent", !std::filesystem::is_regular_file(inward.threemf_path));

    std::error_code error;
    std::filesystem::remove_all(std::filesystem::temp_directory_path() / "cadcam-mvp-export", error);

    if (g_failures != 0) {
        std::cerr << g_failures << " failed\n";
        return EXIT_FAILURE;
    }
    std::cout << "ok\n";
    return EXIT_SUCCESS;
}
