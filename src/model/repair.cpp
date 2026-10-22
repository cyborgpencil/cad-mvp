#include "repair.hpp"

#include "shapes.hpp"
#include "watertight.hpp"

#include <cmath>
#include <cstddef>
#include <cstdint>
#include <map>
#include <tuple>

namespace {

MeshSolid weld_exact(const MeshSolid& mesh) {
    MeshSolid welded;
    std::map<std::tuple<long long, long long, long long>, std::uint32_t> index;
    std::vector<std::uint32_t> remap(mesh.vertices.size(), 0);
    for (std::size_t i = 0; i < mesh.vertices.size(); ++i) {
        const Vec3& vertex = mesh.vertices[i];
        const auto key = std::make_tuple(std::llround(vertex.x * 1000000.0),
                                          std::llround(vertex.y * 1000000.0),
                                          std::llround(vertex.z * 1000000.0));
        const auto found = index.find(key);
        if (found != index.end()) {
            remap[i] = found->second;
            continue;
        }
        const auto id = static_cast<std::uint32_t>(welded.vertices.size());
        index.emplace(key, id);
        welded.vertices.push_back(vertex);
        remap[i] = id;
    }
    for (const auto& triangle : mesh.triangles) {
        if (triangle[0] >= remap.size() || triangle[1] >= remap.size() || triangle[2] >= remap.size()) {
            continue;
        }
        const std::uint32_t a = remap[triangle[0]];
        const std::uint32_t b = remap[triangle[1]];
        const std::uint32_t c = remap[triangle[2]];
        if (a == b || b == c || a == c) {
            continue;
        }
        if (exact_zero_area(welded.vertices[a], welded.vertices[b], welded.vertices[c])) {
            continue;
        }
        welded.triangles.push_back({a, b, c});
    }
    return welded;
}

}  // namespace

RepairResult repair_manifold(const MeshSolid& mesh) {
    RepairResult result;
    result.mesh = mesh;
    WatertightResult check = check_watertight(result.mesh);
    if (check.pass) {
        result.pass = true;
        result.message = check.message;
        return result;
    }

    MeshSolid welded = weld_exact(result.mesh);
    const bool welded_changed = welded.vertices.size() != mesh.vertices.size() ||
                                welded.triangles.size() != mesh.triangles.size();
    if (welded_changed) {
        result.mesh = std::move(welded);
        result.changed = true;
        check = check_watertight(result.mesh);
        if (check.pass) {
            result.pass = true;
            result.message = check.message;
            return result;
        }
    }

    if (check.message.find("winding is inward") != std::string::npos) {
        result.mesh = flip_winding(result.mesh);
        result.changed = true;
        check = check_watertight(result.mesh);
        if (check.pass) {
            result.pass = true;
            result.message = check.message;
            return result;
        }
    }

    result.pass = false;
    result.message = "cannot repair: " + check.message;
    return result;
}
