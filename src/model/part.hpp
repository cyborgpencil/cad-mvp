#pragma once

#include "mesh.hpp"

// 40 x 30 x 20 mm box, 3 mm fillet on the +Z / -Y edge, then an interior
// 8 x 8 x 6 mm box cut. Stored coordinates are millimeters.
MeshSolid build_demo_part();
