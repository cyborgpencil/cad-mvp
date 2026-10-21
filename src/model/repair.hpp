#pragma once

#include "mesh.hpp"

#include <string>

struct RepairResult {
    bool pass = false;
    bool changed = false;
    std::string message;
    MeshSolid mesh;
};

// Runs the existing checker. On failure, welds identical vertices, drops
// degenerate triangles, and flips an inward shell. A second failure is
// reported as "cannot repair: " plus the checker sentence.
RepairResult repair_manifold(const MeshSolid& mesh);
