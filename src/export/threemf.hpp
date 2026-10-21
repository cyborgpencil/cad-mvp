#pragma once

#include "mesh.hpp"

#include <filesystem>

// One mesh, unit="millimeter", stored ZIP with no compression library.
bool write_3mf(const std::filesystem::path& path, const MeshSolid& mesh);
