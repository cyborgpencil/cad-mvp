#pragma once

#include "mesh.hpp"

#include <cstdint>
#include <utility>

// Unit box, corners 0..7:
// 0 (0,0,0)  1 (1,0,0)  2 (1,1,0)  3 (0,1,0)
// 4 (0,0,1)  5 (1,0,1)  6 (1,1,1)  7 (0,1,1)
// Twelve triangles, right-hand outward. No unit is assigned.

inline MeshSolid closed_box() {
    MeshSolid mesh;
    mesh.vertices = {
        {0, 0, 0}, {1, 0, 0}, {1, 1, 0}, {0, 1, 0},
        {0, 0, 1}, {1, 0, 1}, {1, 1, 1}, {0, 1, 1},
    };
    mesh.triangles = {
        {0, 2, 1}, {0, 3, 2},  // bottom, outward -Z
        {4, 5, 6}, {4, 6, 7},  // top, outward +Z
        {0, 5, 4}, {0, 1, 5},  // y = 0, outward -Y
        {3, 6, 2}, {3, 7, 6},  // y = 1, outward +Y
        {0, 7, 3}, {0, 4, 7},  // x = 0, outward -X
        {1, 2, 6}, {1, 6, 5},  // x = 1, outward +X
    };
    return mesh;
}

// Same box with every triangle on z = 1 removed. Boundary edges include (4,5).
inline MeshSolid open_box() {
    MeshSolid mesh = closed_box();
    std::vector<std::array<std::uint32_t, 3>> kept;
    for (const auto& triangle : mesh.triangles) {
        const bool on_top = mesh.vertices[triangle[0]].z == 1.0 &&
                            mesh.vertices[triangle[1]].z == 1.0 &&
                            mesh.vertices[triangle[2]].z == 1.0;
        if (!on_top) {
            kept.push_back(triangle);
        }
    }
    mesh.triangles = std::move(kept);
    return mesh;
}

// Closed box with triangle 0 reversed. Edge (0,1) is then wound twice.
inline MeshSolid flipped_box() {
    MeshSolid mesh = closed_box();
    auto& triangle = mesh.triangles[0];
    const auto saved = triangle[1];
    triangle[1] = triangle[2];
    triangle[2] = saved;
    return mesh;
}
