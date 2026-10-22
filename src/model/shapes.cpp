#include "shapes.hpp"

#include "box.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <map>
#include <tuple>
#include <utility>
#include <vector>

namespace {

struct Weld {
    MeshSolid mesh;
    std::map<std::tuple<long long, long long, long long>, std::uint32_t> index;

    std::uint32_t add(double x, double y, double z) {
        const auto key = std::make_tuple(std::llround(x * 1000000.0), std::llround(y * 1000000.0),
                                          std::llround(z * 1000000.0));
        const auto found = index.find(key);
        if (found != index.end()) {
            return found->second;
        }
        const auto id = static_cast<std::uint32_t>(mesh.vertices.size());
        mesh.vertices.push_back({x, y, z});
        index.emplace(key, id);
        return id;
    }

    void tri(double ax, double ay, double az, double bx, double by, double bz, double cx, double cy,
             double cz) {
        const std::uint32_t a = add(ax, ay, az);
        const std::uint32_t b = add(bx, by, bz);
        const std::uint32_t c = add(cx, cy, cz);
        if (a == b || b == c || a == c) {
            return;
        }
        if (exact_zero_area(mesh.vertices[a], mesh.vertices[b], mesh.vertices[c])) {
            return;
        }
        mesh.triangles.push_back({a, b, c});
    }

    void quad(double ax, double ay, double az, double bx, double by, double bz, double cx, double cy,
              double cz, double dx, double dy, double dz) {
        tri(ax, ay, az, bx, by, bz, cx, cy, cz);
        tri(ax, ay, az, cx, cy, cz, dx, dy, dz);
    }
};

bool bounds_of(const MeshSolid& mesh, double& min_x, double& min_y, double& min_z, double& max_x,
               double& max_y, double& max_z) {
    if (mesh.vertices.empty()) {
        return false;
    }
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
    return true;
}

bool near(double a, double b) {
    return std::fabs(a - b) <= 1e-6;
}

bool is_box_corners(const MeshSolid& mesh, double min_x, double min_y, double min_z, double max_x,
                    double max_y, double max_z) {
    if (mesh.vertices.size() != 8 || mesh.triangles.size() != 12) {
        return false;
    }
    const double xs[2] = {min_x, max_x};
    const double ys[2] = {min_y, max_y};
    const double zs[2] = {min_z, max_z};
    for (const Vec3& vertex : mesh.vertices) {
        const bool x_ok = near(vertex.x, xs[0]) || near(vertex.x, xs[1]);
        const bool y_ok = near(vertex.y, ys[0]) || near(vertex.y, ys[1]);
        const bool z_ok = near(vertex.z, zs[0]) || near(vertex.z, zs[1]);
        if (!x_ok || !y_ok || !z_ok) {
            return false;
        }
    }
    return true;
}

std::vector<double> unique_sorted(std::vector<double> values) {
    std::sort(values.begin(), values.end());
    std::vector<double> out;
    for (double value : values) {
        if (out.empty() || !near(out.back(), value)) {
            out.push_back(value);
        }
    }
    return out;
}

bool point_in_box(double x, double y, double z, double min_x, double min_y, double min_z, double max_x,
                  double max_y, double max_z) {
    return x > min_x + 1e-9 && x < max_x - 1e-9 && y > min_y + 1e-9 && y < max_y - 1e-9 &&
           z > min_z + 1e-9 && z < max_z - 1e-9;
}

MeshSolid cells_to_mesh(const std::vector<double>& xs, const std::vector<double>& ys,
                        const std::vector<double>& zs, const std::vector<char>& filled) {
    const int nx = static_cast<int>(xs.size()) - 1;
    const int ny = static_cast<int>(ys.size()) - 1;
    const int nz = static_cast<int>(zs.size()) - 1;
    auto at = [&](int i, int j, int k) -> bool {
        if (i < 0 || j < 0 || k < 0 || i >= nx || j >= ny || k >= nz) {
            return false;
        }
        return filled[static_cast<std::size_t>((i * ny + j) * nz + k)] != 0;
    };
    Weld weld;
    for (int i = 0; i < nx; ++i) {
        for (int j = 0; j < ny; ++j) {
            for (int k = 0; k < nz; ++k) {
                if (!at(i, j, k)) {
                    continue;
                }
                const double x0 = xs[static_cast<std::size_t>(i)];
                const double x1 = xs[static_cast<std::size_t>(i + 1)];
                const double y0 = ys[static_cast<std::size_t>(j)];
                const double y1 = ys[static_cast<std::size_t>(j + 1)];
                const double z0 = zs[static_cast<std::size_t>(k)];
                const double z1 = zs[static_cast<std::size_t>(k + 1)];
                if (!(x1 > x0) || !(y1 > y0) || !(z1 > z0)) {
                    continue;
                }
                if (!at(i - 1, j, k)) {
                    weld.quad(x0, y0, z0, x0, y0, z1, x0, y1, z1, x0, y1, z0);
                }
                if (!at(i + 1, j, k)) {
                    weld.quad(x1, y0, z0, x1, y1, z0, x1, y1, z1, x1, y0, z1);
                }
                if (!at(i, j - 1, k)) {
                    weld.quad(x0, y0, z0, x1, y0, z0, x1, y0, z1, x0, y0, z1);
                }
                if (!at(i, j + 1, k)) {
                    weld.quad(x0, y1, z0, x0, y1, z1, x1, y1, z1, x1, y1, z0);
                }
                if (!at(i, j, k - 1)) {
                    weld.quad(x0, y0, z0, x0, y1, z0, x1, y1, z0, x1, y0, z0);
                }
                if (!at(i, j, k + 1)) {
                    weld.quad(x0, y0, z1, x1, y0, z1, x1, y1, z1, x0, y1, z1);
                }
            }
        }
    }
    return weld.mesh;
}

MeshSolid boolean_boxes(const MeshSolid& a, const MeshSolid& b, bool as_union) {
    double a_min_x, a_min_y, a_min_z, a_max_x, a_max_y, a_max_z;
    double b_min_x, b_min_y, b_min_z, b_max_x, b_max_y, b_max_z;
    bounds_of(a, a_min_x, a_min_y, a_min_z, a_max_x, a_max_y, a_max_z);
    bounds_of(b, b_min_x, b_min_y, b_min_z, b_max_x, b_max_y, b_max_z);
    const std::vector<double> xs = unique_sorted({a_min_x, a_max_x, b_min_x, b_max_x});
    const std::vector<double> ys = unique_sorted({a_min_y, a_max_y, b_min_y, b_max_y});
    const std::vector<double> zs = unique_sorted({a_min_z, a_max_z, b_min_z, b_max_z});
    const int nx = static_cast<int>(xs.size()) - 1;
    const int ny = static_cast<int>(ys.size()) - 1;
    const int nz = static_cast<int>(zs.size()) - 1;
    std::vector<char> filled(static_cast<std::size_t>(nx * ny * nz), 0);
    for (int i = 0; i < nx; ++i) {
        for (int j = 0; j < ny; ++j) {
            for (int k = 0; k < nz; ++k) {
                const double x = (xs[static_cast<std::size_t>(i)] + xs[static_cast<std::size_t>(i + 1)]) * 0.5;
                const double y = (ys[static_cast<std::size_t>(j)] + ys[static_cast<std::size_t>(j + 1)]) * 0.5;
                const double z = (zs[static_cast<std::size_t>(k)] + zs[static_cast<std::size_t>(k + 1)]) * 0.5;
                const bool in_a = point_in_box(x, y, z, a_min_x, a_min_y, a_min_z, a_max_x, a_max_y, a_max_z);
                const bool in_b = point_in_box(x, y, z, b_min_x, b_min_y, b_min_z, b_max_x, b_max_y, b_max_z);
                filled[static_cast<std::size_t>((i * ny + j) * nz + k)] =
                    (as_union ? (in_a || in_b) : (in_a && !in_b)) ? 1 : 0;
            }
        }
    }
    return cells_to_mesh(xs, ys, zs, filled);
}

bool strictly_inside(const MeshSolid& inner, const MeshSolid& outer) {
    double min_x, min_y, min_z, max_x, max_y, max_z;
    double i_min_x, i_min_y, i_min_z, i_max_x, i_max_y, i_max_z;
    if (!bounds_of(outer, min_x, min_y, min_z, max_x, max_y, max_z) ||
        !bounds_of(inner, i_min_x, i_min_y, i_min_z, i_max_x, i_max_y, i_max_z)) {
        return false;
    }
    return i_min_x > min_x + 1e-6 && i_max_x < max_x - 1e-6 && i_min_y > min_y + 1e-6 &&
           i_max_y < max_y - 1e-6 && i_min_z > min_z + 1e-6 && i_max_z < max_z - 1e-6;
}

int axis_of_edge(const Vec3& a, const Vec3& b) {
    const bool x = near(a.x, b.x);
    const bool y = near(a.y, b.y);
    const bool z = near(a.z, b.z);
    if (!x && y && z) {
        return 0;
    }
    if (x && !y && z) {
        return 1;
    }
    if (x && y && !z) {
        return 2;
    }
    return -1;
}

void emit_local_fillet(Weld& weld, double length, double depth, double height, double radius, int segments) {
    const double y_inset = radius;
    const double z_top = height - radius;
    std::vector<std::pair<double, double>> arc;
    arc.push_back({0.0, z_top});
    for (int step = 1; step < segments; ++step) {
        const double t = static_cast<double>(step) / static_cast<double>(segments);
        const double theta = 3.14159265358979323846 * (1.0 - 0.5 * t);
        arc.push_back({radius + radius * std::cos(theta), z_top + radius * std::sin(theta)});
    }
    arc.push_back({radius, height});

    auto side = [&](double x, bool positive_x) {
        std::vector<std::pair<double, double>> loop;
        loop.push_back({0.0, 0.0});
        loop.push_back({depth, 0.0});
        loop.push_back({depth, height});
        loop.push_back({radius, height});
        for (int i = static_cast<int>(arc.size()) - 2; i >= 1; --i) {
            loop.push_back(arc[static_cast<std::size_t>(i)]);
        }
        loop.push_back({0.0, z_top});
        const int count = static_cast<int>(loop.size());
        for (int i = 1; i + 1 < count; ++i) {
            const auto& p0 = loop[0];
            const auto& p1 = loop[static_cast<std::size_t>(positive_x ? i : i + 1)];
            const auto& p2 = loop[static_cast<std::size_t>(positive_x ? i + 1 : i)];
            weld.tri(x, p0.first, p0.second, x, p1.first, p1.second, x, p2.first, p2.second);
        }
    };

    weld.quad(0, 0, 0, 0, depth, 0, length, depth, 0, length, 0, 0);
    weld.quad(0, 0, 0, length, 0, 0, length, 0, z_top, 0, 0, z_top);
    weld.quad(0, radius, height, length, radius, height, length, depth, height, 0, depth, height);
    weld.quad(0, depth, 0, 0, depth, height, length, depth, height, length, depth, 0);
    side(0.0, false);
    side(length, true);
    for (int i = 0; i + 1 < static_cast<int>(arc.size()); ++i) {
        const auto& p0 = arc[static_cast<std::size_t>(i)];
        const auto& p1 = arc[static_cast<std::size_t>(i + 1)];
        weld.quad(0, p0.first, p0.second, length, p0.first, p0.second, length, p1.first, p1.second, 0,
                  p1.first, p1.second);
    }
}

}  // namespace

MeshSolid translate_mesh(const MeshSolid& mesh, double dx, double dy, double dz) {
    MeshSolid moved = mesh;
    for (Vec3& vertex : moved.vertices) {
        vertex.x += dx;
        vertex.y += dy;
        vertex.z += dz;
    }
    return moved;
}

MeshSolid flip_winding(const MeshSolid& mesh) {
    MeshSolid flipped = mesh;
    for (auto& triangle : flipped.triangles) {
        std::swap(triangle[1], triangle[2]);
    }
    return flipped;
}

MeshSolid mesh_append(const MeshSolid& a, const MeshSolid& b) {
    MeshSolid joined = a;
    const auto offset = static_cast<std::uint32_t>(joined.vertices.size());
    joined.vertices.insert(joined.vertices.end(), b.vertices.begin(), b.vertices.end());
    for (auto triangle : b.triangles) {
        triangle[0] += offset;
        triangle[1] += offset;
        triangle[2] += offset;
        joined.triangles.push_back(triangle);
    }
    return joined;
}

MeshSolid cylinder_mm(double cx, double cy, double radius, double height, int segments) {
    if (!(radius > 0.0) || !(height > 0.0) || segments < 3) {
        return {};
    }
    Weld weld;
    constexpr double kPi = 3.14159265358979323846;
    std::vector<std::pair<double, double>> rim;
    rim.reserve(static_cast<std::size_t>(segments));
    for (int i = 0; i < segments; ++i) {
        const double angle = kPi * 2.0 * static_cast<double>(i) / static_cast<double>(segments);
        rim.push_back({cx + radius * std::cos(angle), cy + radius * std::sin(angle)});
    }
    for (int i = 0; i < segments; ++i) {
        const int next = (i + 1) % segments;
        const double x0 = rim[static_cast<std::size_t>(i)].first;
        const double y0 = rim[static_cast<std::size_t>(i)].second;
        const double x1 = rim[static_cast<std::size_t>(next)].first;
        const double y1 = rim[static_cast<std::size_t>(next)].second;
        weld.tri(cx, cy, 0, x1, y1, 0, x0, y0, 0);
        weld.tri(cx, cy, height, x0, y0, height, x1, y1, height);
        weld.quad(x0, y0, 0, x1, y1, 0, x1, y1, height, x0, y0, height);
    }
    return weld.mesh;
}

MeshSolid mesh_union(const MeshSolid& a, const MeshSolid& b) {
    double a_min_x, a_min_y, a_min_z, a_max_x, a_max_y, a_max_z;
    double b_min_x, b_min_y, b_min_z, b_max_x, b_max_y, b_max_z;
    if (bounds_of(a, a_min_x, a_min_y, a_min_z, a_max_x, a_max_y, a_max_z) &&
        bounds_of(b, b_min_x, b_min_y, b_min_z, b_max_x, b_max_y, b_max_z) &&
        is_box_corners(a, a_min_x, a_min_y, a_min_z, a_max_x, a_max_y, a_max_z) &&
        is_box_corners(b, b_min_x, b_min_y, b_min_z, b_max_x, b_max_y, b_max_z)) {
        return boolean_boxes(a, b, true);
    }
    return mesh_append(a, b);
}

CutResult mesh_cut(const MeshSolid& subject, const MeshSolid& cutter) {
    CutResult result;
    double s_min_x, s_min_y, s_min_z, s_max_x, s_max_y, s_max_z;
    double c_min_x, c_min_y, c_min_z, c_max_x, c_max_y, c_max_z;
    if (!bounds_of(subject, s_min_x, s_min_y, s_min_z, s_max_x, s_max_y, s_max_z) ||
        !bounds_of(cutter, c_min_x, c_min_y, c_min_z, c_max_x, c_max_y, c_max_z)) {
        result.message = "cannot cut: a mesh has no vertices.";
        return result;
    }
    if (is_box_corners(subject, s_min_x, s_min_y, s_min_z, s_max_x, s_max_y, s_max_z) &&
        is_box_corners(cutter, c_min_x, c_min_y, c_min_z, c_max_x, c_max_y, c_max_z)) {
        result.mesh = boolean_boxes(subject, cutter, false);
        result.ok = !result.mesh.triangles.empty();
        result.message = result.ok ? "cut box" : "cut removed the solid.";
        return result;
    }
    if (!is_box_corners(cutter, c_min_x, c_min_y, c_min_z, c_max_x, c_max_y, c_max_z) ||
        !strictly_inside(cutter, subject)) {
        result.message = "cannot cut: the cutter must be a box strictly inside the solid.";
        return result;
    }
    result.mesh = mesh_append(subject, flip_winding(cutter));
    result.ok = true;
    result.message = "cut interior box";
    return result;
}

FilletResult fillet_box_edge(const MeshSolid& box, std::uint32_t vertex_a, std::uint32_t vertex_b,
                             double radius_mm) {
    FilletResult result;
    if (!(radius_mm > 0.0)) {
        result.message = "cannot fillet: radius must be positive.";
        return result;
    }
    if (vertex_a >= box.vertices.size() || vertex_b >= box.vertices.size() || vertex_a == vertex_b) {
        result.message = "cannot fillet: select one edge of the box.";
        return result;
    }
    double min_x, min_y, min_z, max_x, max_y, max_z;
    if (!bounds_of(box, min_x, min_y, min_z, max_x, max_y, max_z) ||
        !is_box_corners(box, min_x, min_y, min_z, max_x, max_y, max_z)) {
        result.message = "cannot fillet: constant-radius fillet is implemented for box edges.";
        return result;
    }
    const Vec3& a = box.vertices[vertex_a];
    const Vec3& b = box.vertices[vertex_b];
    // Only the edge along X at minimum Y and maximum Z. Other edges, including
    // the Y and Z edges that used to be remapped into a swapped box, are rejected
    // before any replacement mesh is built.
    if (axis_of_edge(a, b) != 0 || !near(a.y, min_y) || !near(b.y, min_y) || !near(a.z, max_z) ||
        !near(b.z, max_z)) {
        result.message = "cannot fillet: choose the box edge along X at minimum Y and maximum Z.";
        result.mesh = {};
        return result;
    }
    const double length = max_x - min_x;
    const double depth = max_y - min_y;
    const double height = max_z - min_z;
    if (!(radius_mm < depth - 1e-9) || !(radius_mm < height - 1e-9)) {
        result.message = "cannot fillet: radius does not fit on this edge.";
        return result;
    }

    Weld weld;
    emit_local_fillet(weld, length, depth, height, radius_mm, 8);
    if (!near(min_x, 0.0) || !near(min_y, 0.0) || !near(min_z, 0.0)) {
        for (Vec3& vertex : weld.mesh.vertices) {
            vertex.x += min_x;
            vertex.y += min_y;
            vertex.z += min_z;
        }
    }
    result.mesh = std::move(weld.mesh);
    result.ok = true;
    result.message = "fillet";
    return result;
}
