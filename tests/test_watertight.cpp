#include "fixtures.hpp"
#include "watertight.hpp"

#include <cstdlib>
#include <iostream>
#include <string>

namespace {

int g_failures = 0;

void expect_message(const char* name, const WatertightResult& result, bool want_pass,
                    const std::string& expected) {
    if (result.pass == want_pass && result.message == expected) {
        return;
    }
    std::cerr << name << "\n  got:    " << result.message << "\n  wanted: " << expected << '\n';
    ++g_failures;
}

const char kPass[] =
    "PASS: closed triangle mesh, every edge shared by two triangles, "
    "outward winding, no zero-area triangles.";

}  // namespace

int main() {
    expect_message("closed_box", check_watertight(closed_box()), true, kPass);
    expect_message("open_box", check_watertight(open_box()), false,
                   "FAIL: edge (4,5) is shared by 1 triangle (need 2).");
    expect_message("flipped_box", check_watertight(flipped_box()), false,
                   "FAIL: edge (0,1) is wound the same way by two triangles.");

    MeshSolid empty;
    empty.vertices.push_back({0, 0, 0});
    expect_message("empty", check_watertight(empty), false, "FAIL: mesh has no triangles.");

    MeshSolid bad_index;
    bad_index.vertices = {{0, 0, 0}, {1, 0, 0}, {0, 1, 0}};
    bad_index.triangles = {{0, 1, 9}};
    expect_message("bad_index", check_watertight(bad_index), false,
                   "FAIL: triangle 0 uses vertex index 9, which is outside the 3-vertex mesh.");

    MeshSolid repeated;
    repeated.vertices = {{0, 0, 0}, {1, 0, 0}, {0, 1, 0}};
    repeated.triangles = {{0, 0, 1}};
    expect_message("repeated_index", check_watertight(repeated), false,
                   "FAIL: triangle 0 has a repeated vertex index.");

    MeshSolid flat;
    flat.vertices = {{0, 0, 0}, {1, 0, 0}, {2, 0, 0}};
    flat.triangles = {{0, 1, 2}};
    expect_message("zero_area", check_watertight(flat), false, "FAIL: triangle 0 has zero area.");

    MeshSolid nonmanifold;
    nonmanifold.vertices = {{0, 0, 0}, {1, 0, 0}, {0, 1, 0}, {0, 0, 1}, {1, 1, 1}};
    nonmanifold.triangles = {{0, 1, 2}, {0, 1, 3}, {0, 1, 4}};
    expect_message("nonmanifold", check_watertight(nonmanifold), false,
                   "FAIL: edge (0,1) is shared by 3 triangles (need 2).");

    MeshSolid inward = closed_box();
    for (auto& triangle : inward.triangles) {
        const auto saved = triangle[1];
        triangle[1] = triangle[2];
        triangle[2] = saved;
    }
    expect_message("inward_box", check_watertight(inward), false,
                   "FAIL: winding is inward (signed volume is negative).");

    if (g_failures != 0) {
        std::cerr << g_failures << " failed\n";
        return EXIT_FAILURE;
    }
    std::cout << "ok\n";
    return EXIT_SUCCESS;
}
