#include "fixtures.hpp"
#include "repair.hpp"
#include "shapes.hpp"
#include "watertight.hpp"

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>

namespace {

int g_failures = 0;

bool starts_with(const std::string& text, const char* prefix) {
    return text.rfind(prefix, 0) == 0;
}

bool vec3_equals(const Vec3& a, const Vec3& b) {
    return a.x == b.x && a.y == b.y && a.z == b.z;
}

bool mesh_equals(const MeshSolid& a, const MeshSolid& b) {
    if (a.vertices.size() != b.vertices.size() || a.triangles.size() != b.triangles.size()) {
        return false;
    }
    for (std::size_t i = 0; i < a.vertices.size(); ++i) {
        if (!vec3_equals(a.vertices[i], b.vertices[i])) {
            return false;
        }
    }
    for (std::size_t i = 0; i < a.triangles.size(); ++i) {
        if (a.triangles[i] != b.triangles[i]) {
            return false;
        }
    }
    return true;
}

void expect(const char* name, bool ok) {
    if (ok) {
        return;
    }
    std::cerr << name << " failed\n";
    ++g_failures;
}

void expect_repair_case(const char* name, const RepairResult& result, bool want_pass,
                        bool want_changed, const char* want_prefix) {
    const WatertightResult wt = check_watertight(result.mesh);
    const char* want_wt_prefix = want_pass ? "PASS: " : "FAIL: ";
    const bool ok = result.pass == want_pass &&
                    result.changed == want_changed &&
                    starts_with(result.message, want_prefix) &&
                    wt.pass == want_pass &&
                    starts_with(wt.message, want_wt_prefix);
    if (ok) {
        return;
    }
    std::cerr << name << " failed:\n"
              << "  result.pass=" << (result.pass ? "true" : "false")
              << " (want " << (want_pass ? "true" : "false") << ")\n"
              << "  result.changed=" << (result.changed ? "true" : "false")
              << " (want " << (want_changed ? "true" : "false") << ")\n"
              << "  result.message=\"" << result.message << "\" (want prefix \"" << want_prefix << "\")\n"
              << "  wt.pass=" << (wt.pass ? "true" : "false")
              << " wt.message=\"" << wt.message << "\"\n";
    ++g_failures;
}

MeshSolid make_duplicate_vertex_soup(const MeshSolid& src) {
    MeshSolid soup;
    soup.vertices.reserve(src.triangles.size() * 3);
    soup.triangles.reserve(src.triangles.size());
    for (const auto& tri : src.triangles) {
        const auto base = static_cast<std::uint32_t>(soup.vertices.size());
        soup.vertices.push_back(src.vertices[tri[0]]);
        soup.vertices.push_back(src.vertices[tri[1]]);
        soup.vertices.push_back(src.vertices[tri[2]]);
        soup.triangles.push_back({base, base + 1, base + 2});
    }
    return soup;
}

}  // namespace

int main() {
    // 1. Clean closed box: pass=true, changed=false, message starts "PASS: ", result.mesh watertight.
    const MeshSolid clean = closed_box();
    const RepairResult clean_res = repair_manifold(clean);
    expect_repair_case("clean_closed_box", clean_res, true, false, "PASS: ");
    expect("clean_closed_box_mesh_unchanged", mesh_equals(clean_res.mesh, clean));

    // 2. Inward-wound (flipped) box: pass=true, changed=true, result.mesh passes check_watertight.
    const MeshSolid inward = flip_winding(closed_box());
    expect("inward_precheck_fails", !check_watertight(inward).pass);
    const RepairResult inward_res = repair_manifold(inward);
    expect_repair_case("inward_wound_box", inward_res, true, true, "PASS: ");
    expect("inward_wound_box_counts",
           inward_res.mesh.vertices.size() == clean.vertices.size() &&
               inward_res.mesh.triangles.size() == clean.triangles.size());

    // 3. Duplicate-vertex soup (same coords): weld path, pass=true, changed=true.
    const MeshSolid soup = make_duplicate_vertex_soup(closed_box());
    expect("duplicate_vertex_soup_precheck_fails",
           soup.vertices.size() == 36 && soup.triangles.size() == 12 && !check_watertight(soup).pass);
    const RepairResult soup_res = repair_manifold(soup);
    expect_repair_case("duplicate_vertex_soup", soup_res, true, true, "PASS: ");
    expect("duplicate_vertex_soup_welded_counts",
           soup_res.mesh.vertices.size() == 8 && soup_res.mesh.triangles.size() == 12);

    // 4. Box plus one zero-area triangle: dropped, pass=true, changed=true.
    // 4a. Collinear zero-area triangle (exact_zero_area path in weld_exact).
    MeshSolid box_zero_collinear = closed_box();
    box_zero_collinear.vertices.push_back({0.5, 0.0, 0.0});
    box_zero_collinear.triangles.push_back({0, 1, 8});
    expect("box_zero_collinear_precheck_fails", !check_watertight(box_zero_collinear).pass);
    const RepairResult zero_collinear_res = repair_manifold(box_zero_collinear);
    expect_repair_case("box_plus_zero_area_collinear", zero_collinear_res, true, true, "PASS: ");
    expect("box_plus_zero_area_collinear_dropped",
           zero_collinear_res.mesh.triangles.size() == 12);

    // 4b. Repeated-vertex zero-area triangle (a == b path in weld_exact).
    MeshSolid box_zero_repeated = closed_box();
    box_zero_repeated.triangles.push_back({0, 0, 1});
    expect("box_zero_repeated_precheck_fails", !check_watertight(box_zero_repeated).pass);
    const RepairResult zero_repeated_res = repair_manifold(box_zero_repeated);
    expect_repair_case("box_plus_zero_area_repeated", zero_repeated_res, true, true, "PASS: ");
    expect("box_plus_zero_area_repeated_dropped",
           zero_repeated_res.mesh.vertices.size() == 8 &&
               zero_repeated_res.mesh.triangles.size() == 12);

    // 5. Open box (one face missing): pass=false, message starts "cannot repair: ".
    const MeshSolid open = open_box();
    const RepairResult open_res = repair_manifold(open);
    expect_repair_case("open_box", open_res, false, false, "cannot repair: ");

    // 6. Cannot-repair mutation probe (General ask):
    // 6a. Plain open_box (no duplicate vertices): weld_exact produces identical counts (8v, 10t),
    // so welded_changed is false and result.mesh == input.
    const bool open_equals_input = mesh_equals(open_res.mesh, open);
    std::cout << "PROBE native open_box (clean vertices): "
              << (!open_equals_input ? "CONFIRMED" : "NOT REPRODUCED")
              << " (pass=" << (open_res.pass ? "true" : "false")
              << ", changed=" << (open_res.changed ? "true" : "false")
              << ", vertices " << open.vertices.size() << "->" << open_res.mesh.vertices.size()
              << ", triangles " << open.triangles.size() << "->" << open_res.mesh.triangles.size()
              << ", mesh_equals_input=" << (open_equals_input ? "true" : "false") << ")\n";
    expect("probe_open_box_clean_unchanged", open_equals_input && !open_res.changed);

    // 6b. Open box that also has duplicate vertices: weld_exact reduces vertex count (9 -> 8)
    // and remaps triangle indices, setting result.mesh = welded and result.changed = true
    // BEFORE check_watertight fails on the missing top face. repair_manifold then returns
    // pass=false with the mutated result.mesh (so bindings.cpp:152 g_mesh = result.mesh
    // overwrites g_mesh on a failed repair).
    MeshSolid open_dup = open_box();
    open_dup.vertices.push_back(open_dup.vertices[0]);
    open_dup.triangles[0][0] = static_cast<std::uint32_t>(open_dup.vertices.size() - 1);
    const RepairResult open_dup_res = repair_manifold(open_dup);
    const bool open_dup_equals_input = mesh_equals(open_dup_res.mesh, open_dup);
    std::cout << "PROBE native open_box+dup_vertices: "
              << (!open_dup_equals_input ? "CONFIRMED" : "NOT REPRODUCED")
              << " (pass=" << (open_dup_res.pass ? "true" : "false")
              << ", changed=" << (open_dup_res.changed ? "true" : "false")
              << ", vertices " << open_dup.vertices.size() << "->" << open_dup_res.mesh.vertices.size()
              << ", triangles " << open_dup.triangles.size() << "->" << open_dup_res.mesh.triangles.size()
              << ", mesh_equals_input=" << (open_dup_equals_input ? "true" : "false") << ")\n";
    expect_repair_case("open_box_with_duplicate_vertices", open_dup_res, false, true, "cannot repair: ");
    expect("probe_open_box_dup_mutates_result_mesh",
           !open_dup_equals_input &&
               open_dup_res.mesh.vertices.size() == 8 &&
               open_dup_res.mesh.triangles.size() == 10 &&
               mesh_equals(open_dup_res.mesh, open));

    if (g_failures != 0) {
        std::cerr << g_failures << " failed\n";
        return EXIT_FAILURE;
    }
    std::cout << "ok\n";
    return EXIT_SUCCESS;
}
