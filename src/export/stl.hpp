#pragma once

#include "mesh.hpp"

#include <filesystem>

// Binary STL. Coordinates are millimeters. The header does not start with "solid".
// Read-back keeps one vertex per corner and does not weld coincident points.
bool write_binary_stl(const std::filesystem::path& path, const MeshSolid& mesh);
bool read_binary_stl(const std::filesystem::path& path, MeshSolid& mesh);
