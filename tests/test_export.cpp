#include "box.hpp"
#include "export_files.hpp"
#include "fixtures.hpp"
#include "stl.hpp"
#include "threemf.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <utility>

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

    MeshSolid exploded;
    for (const auto& triangle : box.triangles) {
        const std::uint32_t base = static_cast<std::uint32_t>(exploded.vertices.size());
        exploded.vertices.push_back(box.vertices[triangle[0]]);
        exploded.vertices.push_back(box.vertices[triangle[1]]);
        exploded.vertices.push_back(box.vertices[triangle[2]]);
        exploded.triangles.push_back({base, base + 1, base + 2});
    }
    if (!exploded.triangles.empty()) {
        auto& first = exploded.triangles[0];
        const auto saved = first[1];
        first[1] = first[2];
        first[2] = saved;
    }
    const MeshSolid welded = weld_mesh(exploded);
    expect("weld drops duplicate vertices", welded.vertices.size() == 8);
    {
        std::map<std::array<long long, 3>, int> seen;
        bool dup = false;
        for (const Vec3& vertex : welded.vertices) {
            const std::array<long long, 3> key = {
                std::llround(vertex.x / 1e-6),
                std::llround(vertex.y / 1e-6),
                std::llround(vertex.z / 1e-6),
            };
            if (seen[key] > 0) {
                dup = true;
            }
            seen[key] += 1;
        }
        expect("weld no coincident vertices", !dup && !welded.vertices.empty());
    }
    {
        std::map<std::pair<std::uint32_t, std::uint32_t>, int> directed;
        bool twice = false;
        double sum = 0.0;
        for (const auto& triangle : welded.triangles) {
            for (int corner = 0; corner < 3; ++corner) {
                const std::uint32_t from = triangle[static_cast<std::size_t>(corner)];
                const std::uint32_t to = triangle[static_cast<std::size_t>((corner + 1) % 3)];
                directed[{from, to}] += 1;
                if (directed[{from, to}] > 1) {
                    twice = true;
                }
            }
            const Vec3& a = welded.vertices[triangle[0]];
            const Vec3& b = welded.vertices[triangle[1]];
            const Vec3& c = welded.vertices[triangle[2]];
            const double cx = b.y * c.z - b.z * c.y;
            const double cy = b.z * c.x - b.x * c.z;
            const double cz = b.x * c.y - b.y * c.x;
            sum += a.x * cx + a.y * cy + a.z * cz;
        }
        expect("weld no directed edge twice", !twice && !welded.triangles.empty());
        expect("weld positive signed volume", sum > 0.0);
    }

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
