#pragma once

#include <array>
#include <cstdint>
#include <vector>

// Positions have no unit. The MVP unit lock is still undecided.
struct Vec3 {
    double x = 0;
    double y = 0;
    double z = 0;
};

struct MeshSolid {
    std::vector<Vec3> vertices;
    std::vector<std::array<std::uint32_t, 3>> triangles;
};

// True when the cross product of (b - a) and (c - a) is exactly (0, 0, 0).
bool exact_zero_area(const Vec3& a, const Vec3& b, const Vec3& c);
