#pragma once

#include "mesh.hpp"

#include <filesystem>

// Weld vertices that round to the same 1e-6 mm, remap triangles, drop
// degenerates, and swap a triangle that would reuse a directed edge.
MeshSolid weld_mesh(const MeshSolid& mesh);

// One mesh, unit="millimeter", stored ZIP with no compression library.
bool write_3mf(const std::filesystem::path& path, const MeshSolid& mesh);
