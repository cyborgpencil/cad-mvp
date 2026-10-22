#include "export_files.hpp"

#include "gate.hpp"
#include "stl.hpp"
#include "threemf.hpp"

#include <iostream>

namespace {

bool is_repo_root(const std::filesystem::path& path) {
    std::error_code error;
    return std::filesystem::is_regular_file(path / "CMakeLists.txt", error) &&
           std::filesystem::is_directory(path / "mvp", error);
}

}  // namespace

std::filesystem::path repo_export_dir(const std::filesystem::path& start) {
    std::error_code error;
    std::filesystem::path current = std::filesystem::absolute(start, error);
    if (error) {
        current = start;
    }
    for (int step = 0; step < 8; ++step) {
        if (is_repo_root(current)) {
            return current / "builds" / "export";
        }
        const std::filesystem::path parent = current.parent_path();
        if (parent.empty() || parent == current) {
            break;
        }
        current = parent;
    }
    std::filesystem::path fallback = std::filesystem::absolute(start, error);
    if (error) {
        fallback = start;
    }
    return fallback / "builds" / "export";
}

ExportAttempt export_mesh_if_closed(const MeshSolid& mesh, const std::filesystem::path& directory) {
    ExportAttempt attempt;
    attempt.check = check_watertight(mesh);
    attempt.stl_path = directory / "box.stl";
    attempt.threemf_path = directory / "box.3mf";

    const GateReport report = evaluate_export_gate(mesh, UnitLock{});
    if (!report.mesh_pass) {
        std::cerr << report.mesh_message << '\n';
        return attempt;
    }

    std::error_code error;
    std::filesystem::create_directories(directory, error);
    if (error) {
        return attempt;
    }
    if (!write_binary_stl(attempt.stl_path, mesh)) {
        return attempt;
    }
    if (!write_3mf(attempt.threemf_path, mesh)) {
        std::filesystem::remove(attempt.stl_path, error);
        return attempt;
    }
    attempt.wrote = true;
    return attempt;
}
