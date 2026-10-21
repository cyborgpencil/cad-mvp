#include "fixtures.hpp"
#include "watertight.hpp"

#include <iostream>
#include <string>

namespace {

const char kPass[] =
    "PASS: closed triangle mesh, every edge shared by two triangles, "
    "outward winding, no zero-area triangles.";

// Exit 0 means each fixture produced its expected line.
// The open and flipped fixtures are expected to print FAIL.
bool emit(const char* name, const MeshSolid& mesh, bool want_pass, const std::string& expected) {
    const WatertightResult result = check_watertight(mesh);
    std::cout << name << ": " << result.message << '\n';
    if (result.pass == want_pass && result.message == expected) {
        return true;
    }
    std::cerr << name << ": expected " << expected << '\n';
    return false;
}

}  // namespace

int main() {
    int mismatches = 0;
    if (!emit("closed_box", closed_box(), true, kPass)) {
        ++mismatches;
    }
    if (!emit("open_box", open_box(), false,
              "FAIL: edge (4,5) is shared by 1 triangle (need 2).")) {
        ++mismatches;
    }
    if (!emit("flipped_box", flipped_box(), false,
              "FAIL: edge (0,1) is wound the same way by two triangles.")) {
        ++mismatches;
    }
    return mismatches == 0 ? 0 : 1;
}
