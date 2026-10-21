#include "watertight.hpp"

#include <cstdint>
#include <map>
#include <string>
#include <utility>

namespace {

using Edge = std::pair<std::uint32_t, std::uint32_t>;

std::string fail_edge_count(std::uint32_t a, std::uint32_t b, int count) {
    return "FAIL: edge (" + std::to_string(a) + "," + std::to_string(b) +
           ") is shared by " + std::to_string(count) + " triangle" +
           (count == 1 ? "" : "s") + " (need 2).";
}

std::string fail_winding(std::uint32_t a, std::uint32_t b) {
    return "FAIL: edge (" + std::to_string(a) + "," + std::to_string(b) +
           ") is wound the same way by two triangles.";
}

// Unscaled triple sum. Sign matches signed volume. Skipping /6 keeps an
// exact zero exact, because 1/6 is not a binary fraction.
double triple_sum(const MeshSolid& mesh) {
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
    return sum;
}

}  // namespace

WatertightResult check_watertight(const MeshSolid& mesh) {
    if (mesh.triangles.empty()) {
        return {false, "FAIL: mesh has no triangles."};
    }

    const auto vertex_count = mesh.vertices.size();
    for (std::size_t i = 0; i < mesh.triangles.size(); ++i) {
        const auto& triangle = mesh.triangles[i];
        for (std::uint32_t index : triangle) {
            if (static_cast<std::size_t>(index) >= vertex_count) {
                return {false, "FAIL: triangle " + std::to_string(i) +
                                   " uses vertex index " + std::to_string(index) +
                                   ", which is outside the " +
                                   std::to_string(vertex_count) + "-vertex mesh."};
            }
        }
        if (triangle[0] == triangle[1] || triangle[1] == triangle[2] ||
            triangle[0] == triangle[2]) {
            return {false, "FAIL: triangle " + std::to_string(i) +
                               " has a repeated vertex index."};
        }
        const Vec3& a = mesh.vertices[triangle[0]];
        const Vec3& b = mesh.vertices[triangle[1]];
        const Vec3& c = mesh.vertices[triangle[2]];
        if (exact_zero_area(a, b, c)) {
            return {false, "FAIL: triangle " + std::to_string(i) + " has zero area."};
        }
    }

    std::map<Edge, int> undirected;
    std::map<Edge, int> directed;
    for (const auto& triangle : mesh.triangles) {
        for (int corner = 0; corner < 3; ++corner) {
            const std::uint32_t from = triangle[static_cast<std::size_t>(corner)];
            const std::uint32_t to = triangle[static_cast<std::size_t>((corner + 1) % 3)];
            directed[{from, to}] += 1;
            if (from < to) {
                undirected[{from, to}] += 1;
            } else {
                undirected[{to, from}] += 1;
            }
        }
    }

    for (const auto& entry : undirected) {
        if (entry.second != 2) {
            return {false, fail_edge_count(entry.first.first, entry.first.second, entry.second)};
        }
    }

    for (const auto& entry : directed) {
        if (entry.second != 1) {
            return {false, fail_winding(entry.first.first, entry.first.second)};
        }
    }

    const double sum = triple_sum(mesh);
    if (sum == 0.0) {
        return {false, "FAIL: signed volume is zero."};
    }
    if (sum < 0.0) {
        return {false, "FAIL: winding is inward (signed volume is negative)."};
    }

    return {true,
            "PASS: closed triangle mesh, every edge shared by two triangles, "
            "outward winding, no zero-area triangles."};
}
