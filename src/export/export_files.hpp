#pragma once

#include "watertight.hpp"

#include <filesystem>

struct ExportAttempt {
    bool wrote = false;
    WatertightResult check;
    std::filesystem::path stl_path;
    std::filesystem::path threemf_path;
};

// Writes box.stl and box.3mf only when check_watertight passes.
// A failed check does not create the directory and does not touch existing files.
ExportAttempt export_mesh_if_closed(const MeshSolid& mesh, const std::filesystem::path& directory);

// Walks parents for the repo root, then returns <root>/builds/export.
std::filesystem::path repo_export_dir(const std::filesystem::path& start);
