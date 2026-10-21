#include "export_files.hpp"
#include "part.hpp"

#include <cstdlib>
#include <filesystem>
#include <iostream>

int main(int argc, char** argv) {
    const std::filesystem::path directory =
        argc > 1 ? std::filesystem::path(argv[1]) : repo_export_dir(std::filesystem::current_path());
    const MeshSolid part = build_demo_part();
    const ExportAttempt attempt = export_mesh_if_closed(part, directory);
    std::cout << attempt.check.message << '\n';
    if (!attempt.wrote) {
        return EXIT_FAILURE;
    }
    std::cout << attempt.stl_path.string() << '\n';
    std::cout << attempt.threemf_path.string() << '\n';
    return EXIT_SUCCESS;
}
