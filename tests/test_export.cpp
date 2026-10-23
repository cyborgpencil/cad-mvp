#include "bed_orient.hpp"
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

bool near_mm(double a, double b, double tol) {
    return std::isfinite(a) && std::isfinite(b) && std::abs(a - b) <= tol;
}

struct Extents {
    double xmin = 0;
    double ymin = 0;
    double zmin = 0;
    double xmax = 0;
    double ymax = 0;
    double zmax = 0;
};

Extents extents_of(const MeshSolid& mesh) {
    Extents box;
    box.xmin = mesh.vertices[0].x;
    box.ymin = mesh.vertices[0].y;
    box.zmin = mesh.vertices[0].z;
    box.xmax = box.xmin;
    box.ymax = box.ymin;
    box.zmax = box.zmin;
    for (const Vec3& vertex : mesh.vertices) {
        box.xmin = std::min(box.xmin, vertex.x);
        box.ymin = std::min(box.ymin, vertex.y);
        box.zmin = std::min(box.zmin, vertex.z);
        box.xmax = std::max(box.xmax, vertex.x);
        box.ymax = std::max(box.ymax, vertex.y);
        box.zmax = std::max(box.zmax, vertex.z);
    }
    return box;
}

double signed_volume(const MeshSolid& mesh) {
    double sum = 0.0;
    for (const auto& triangle : mesh.triangles) {
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

// Profile in XZ, 6 mm thick in Y. The profile is the unique largest face.
MeshSolid l_prism() {
    const double profile[6][2] = {
        {0, 0}, {30, 0}, {30, 10}, {10, 10}, {10, 24}, {0, 24},
    };
    MeshSolid mesh;
    mesh.vertices.reserve(12);
    for (const auto& point : profile) {
        mesh.vertices.push_back({point[0], 0.0, point[1]});
    }
    for (const auto& point : profile) {
        mesh.vertices.push_back({point[0], 6.0, point[1]});
    }
    mesh.triangles = {
        {0, 1, 2}, {0, 2, 3}, {0, 3, 4}, {0, 4, 5},
        {6, 8, 7}, {6, 9, 8}, {6, 10, 9}, {6, 11, 10},
    };
    for (int i = 0; i < 6; ++i) {
        const std::uint32_t i0 = static_cast<std::uint32_t>(i);
        const std::uint32_t j0 = static_cast<std::uint32_t>((i + 1) % 6);
        const std::uint32_t i1 = i0 + 6;
        const std::uint32_t j1 = j0 + 6;
        mesh.triangles.push_back({i0, j1, j0});
        mesh.triangles.push_back({i0, i1, j1});
    }
    return mesh;
}

struct FaceArea {
    double nx = 0;
    double ny = 0;
    double nz = 0;
    double offset = 0;
    double area = 0;
    double zmin = 0;
    double zmax = 0;
};

bool flat_on_bed(const MeshSolid& mesh, const char* label) {
    if (mesh.vertices.empty()) {
        expect(label, false);
        return false;
    }
    const Extents box = extents_of(mesh);
    expect(label, near_mm(box.zmin, 0.0, 1e-4));
    expect(label, near_mm(box.zmax - box.zmin, 6.0, 1e-3));
    expect(label, near_mm(box.xmax - box.xmin, 30.0, 1e-3));
    expect(label, near_mm(box.ymax - box.ymin, 24.0, 1e-3));

    std::vector<FaceArea> faces;
    double down_on_bed = 0.0;
    bool supported = true;
    for (const auto& triangle : mesh.triangles) {
        const Vec3& a = mesh.vertices[triangle[0]];
        const Vec3& b = mesh.vertices[triangle[1]];
        const Vec3& c = mesh.vertices[triangle[2]];
        const double ux = b.x - a.x;
        const double uy = b.y - a.y;
        const double uz = b.z - a.z;
        const double vx = c.x - a.x;
        const double vy = c.y - a.y;
        const double vz = c.z - a.z;
        const double cx = uy * vz - uz * vy;
        const double cy = uz * vx - ux * vz;
        const double cz = ux * vy - uy * vx;
        const double len = std::sqrt(cx * cx + cy * cy + cz * cz);
        if (!(len > 1e-12)) {
            continue;
        }
        const double nz = cz / len;
        const double zmin = std::min(a.z, std::min(b.z, c.z));
        const double zmax = std::max(a.z, std::max(b.z, c.z));
        if (nz <= -0.999 && zmin > 0.05) {
            supported = false;
        }
        FaceArea* found = nullptr;
        const double nx = cx / len;
        const double ny = cy / len;
        const double offset = nx * a.x + ny * a.y + nz * a.z;
        for (FaceArea& face : faces) {
            const double dot = face.nx * nx + face.ny * ny + face.nz * nz;
            if (dot >= 0.999 && std::abs(face.offset - offset) <= 0.05) {
                found = &face;
                break;
            }
        }
        if (found == nullptr) {
            FaceArea face;
            face.nx = nx;
            face.ny = ny;
            face.nz = nz;
            face.offset = offset;
            face.area = len * 0.5;
            face.zmin = zmin;
            face.zmax = zmax;
            faces.push_back(face);
        } else {
            found->area += len * 0.5;
            found->zmin = std::min(found->zmin, zmin);
            found->zmax = std::max(found->zmax, zmax);
        }
    }
    double largest = 0.0;
    for (const FaceArea& face : faces) {
        largest = std::max(largest, face.area);
        if (face.nz <= -0.999 && face.zmax <= 0.05 && face.zmin <= 1e-4) {
            down_on_bed = std::max(down_on_bed, face.area);
        }
    }
    expect(label, supported);
    expect(label, largest > 400.0 && down_on_bed + 1e-3 >= largest);
    return true;
}

void expect_z_span(const std::filesystem::path& path, double* zmin, double* zmax) {
    std::ifstream in(path, std::ios::binary);
    std::ostringstream buffer;
    buffer << in.rdbuf();
    const std::string text = buffer.str();
    double lo = 0.0;
    double hi = 0.0;
    bool any = false;
    const std::string key = "z=\"";
    for (std::size_t pos = text.find(key); pos != std::string::npos; pos = text.find(key, pos + key.size())) {
        const double z = std::strtod(text.c_str() + pos + key.size(), nullptr);
        if (!any) {
            lo = z;
            hi = z;
            any = true;
        } else {
            lo = std::min(lo, z);
            hi = std::max(hi, z);
        }
    }
    expect("3mf has vertex z", any);
    if (zmin != nullptr) {
        *zmin = lo;
    }
    if (zmax != nullptr) {
        *zmax = hi;
    }
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

    // A cube already seated on z = 0 stays put, including its XY shift.
    MeshSolid seated = box_mm(20.0, 20.0, 20.0);
    for (Vec3& vertex : seated.vertices) {
        vertex.x -= 10.0;
        vertex.y -= 10.0;
    }
    const MeshSolid seated_laid = lay_single_body_on_bed(seated);
    bool seated_same = seated_laid.vertices.size() == seated.vertices.size() &&
                       seated_laid.triangles.size() == seated.triangles.size();
    for (std::size_t i = 0; seated_same && i < seated.vertices.size(); ++i) {
        seated_same = seated_laid.vertices[i].x == seated.vertices[i].x &&
                      seated_laid.vertices[i].y == seated.vertices[i].y &&
                      seated_laid.vertices[i].z == seated.vertices[i].z;
    }
    expect("on-bed cube is unchanged", seated_same);

    // 3 x 5 x 7. The short axis is X. The largest face is 5 x 7.
    const MeshSolid brick = lay_single_body_on_bed(box_mm(3.0, 5.0, 7.0));
    if (!brick.vertices.empty()) {
        const Extents brick_box = extents_of(brick);
        expect("brick zmin", near_mm(brick_box.zmin, 0.0, 1e-6));
        expect("brick height", near_mm(brick_box.zmax - brick_box.zmin, 3.0, 1e-6));
        expect("brick dx", near_mm(brick_box.xmax - brick_box.xmin, 7.0, 1e-6));
        expect("brick dy", near_mm(brick_box.ymax - brick_box.ymin, 5.0, 1e-6));
    } else {
        expect("brick has vertices", false);
    }

    // Synthetic L from a 30 x 24 profile, 6 mm thick. Not a fixture part.
    const MeshSolid prism = l_prism();
    expect("L prism volume", near_mm(signed_volume(prism), 2640.0, 1e-4));
    const MeshSolid prism_laid = lay_single_body_on_bed(prism);
    flat_on_bed(prism_laid, "L prism on bed");

    const std::filesystem::path l_dir = fresh_dir("l-prism");
    std::filesystem::create_directories(l_dir);
    const std::filesystem::path l_stl = l_dir / "l.stl";
    const std::filesystem::path l_3mf = l_dir / "l.3mf";
    expect("L stl writes", write_binary_stl(l_stl, prism));
    expect("L 3mf writes", write_3mf(l_3mf, prism));
    MeshSolid l_loaded;
    expect("L stl reads", read_binary_stl(l_stl, l_loaded));
    if (!l_loaded.vertices.empty()) {
        flat_on_bed(l_loaded, "L stl on bed");
    } else {
        expect("L stl has vertices", false);
    }
    double l_zmin = 1.0;
    double l_zmax = 0.0;
    expect_z_span(l_3mf, &l_zmin, &l_zmax);
    expect("L 3mf zmin", near_mm(l_zmin, 0.0, 1e-4));
    expect("L 3mf height", near_mm(l_zmax - l_zmin, 6.0, 1e-3));

    const std::filesystem::path l_raw = l_dir / "raw.stl";
    expect("L raw stl writes", write_binary_stl(l_raw, prism, false));
    MeshSolid l_upright;
    expect("L raw stl reads", read_binary_stl(l_raw, l_upright));
    if (!l_upright.vertices.empty()) {
        const Extents upright = extents_of(l_upright);
        expect("lay off keeps the arm", near_mm(upright.zmax - upright.zmin, 24.0, 1e-3));
    } else {
        expect("L raw stl has vertices", false);
    }

    std::error_code error;
    std::filesystem::remove_all(std::filesystem::temp_directory_path() / "cadcam-mvp-export", error);

    if (g_failures != 0) {
        std::cerr << g_failures << " failed\n";
        return EXIT_FAILURE;
    }
    std::cout << "ok\n";
    return EXIT_SUCCESS;
}
