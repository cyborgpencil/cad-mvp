#pragma once

#include "mesh.hpp"

// Axis-aligned box from the origin. Sizes are millimeters.
// Non-positive sizes return a mesh with no triangles.
// Triangle order matches closed_box(), scaled on each axis.
MeshSolid box_mm(double width_mm, double depth_mm, double height_mm);
