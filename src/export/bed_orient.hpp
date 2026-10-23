#pragma once

#include "mesh.hpp"

// Single-body print pose. Searches the 24 proper axis-aligned rotations,
// seats zmin at 0, and keeps the lowest part. Equal heights keep the larger
// planar face on the bed, then the longer X extent. The identity pose is
// kept when it already wins, so an on-bed cube is unchanged.
// Tolerances match web/assemblies.mjs (0.999 normal dot, 0.05 mm plane).
MeshSolid lay_single_body_on_bed(const MeshSolid& mesh);
