#include "box.hpp"
#include "fixtures.hpp"
#include "gate.hpp"

#include <cstdlib>
#include <iostream>
#include <string>

namespace {

int g_failures = 0;

void expect(const char* name, bool ok) {
    if (ok) {
        return;
    }
    std::cerr << name << " failed\n";
    ++g_failures;
}

void expect_exact(const char* name, double got, double wanted) {
    if (got == wanted) {
        return;
    }
    std::cerr << name << "\n  got:    " << got << "\n  wanted: " << wanted << '\n';
    ++g_failures;
}

void expect_text(const char* name, const std::string& got, const std::string& wanted) {
    if (got == wanted) {
        return;
    }
    std::cerr << name << "\n  got:    " << got << "\n  wanted: " << wanted << '\n';
    ++g_failures;
}

}  // namespace

int main() {
    expect("mm units pass", export_units_pass("millimeter", "millimeter", "millimeter"));
    expect("inch storage fails", !export_units_pass("inch", "millimeter", "millimeter"));
    expect("inch 3mf fails", !export_units_pass("millimeter", "inch", "millimeter"));
    expect("inch stl fails", !export_units_pass("millimeter", "millimeter", "inch"));
    expect("null unit fails", !export_units_pass(nullptr, "millimeter", "millimeter"));

    const std::string units_fail = "FAIL: export unit is not millimeter.";
    const std::string watertight_fail = "FAIL: edge (4,5) is shared by 1 triangle (need 2).";
    const std::string units_ok = "PASS: export unit is millimeter.";
    const std::string no_triangles = "FAIL: mesh has no triangles.";
    const std::string zero_volume = "FAIL: mesh has zero volume.";
    const std::string inside_out_reason = "FAIL: mesh is inside-out (negative volume).";
    expect_text("units block ignores watertight fail",
                export_block_reason(false, watertight_fail, false, units_fail), units_fail);
    expect_text("units block when solid passes",
                export_block_reason(true, "PASS", false, units_fail), units_fail);
    expect_text("units beat an empty mesh",
                export_block_reason(false, watertight_fail, false, units_fail, false, no_triangles),
                units_fail);
    expect("units pass clears the block", export_block_reason(true, "PASS", true, units_ok).empty());
    expect("watertight fail does not block",
           export_block_reason(false, watertight_fail, true, units_ok).empty());
    expect_text("zero volume blocks after units pass",
                export_block_reason(false, watertight_fail, true, units_ok, false, zero_volume),
                zero_volume);

    UnitLock lock;
    const GateReport closed = evaluate_export_gate(closed_box(), lock);
    expect("closed watertight", closed.watertight_pass);
    expect("closed units", closed.units_pass);
    expect("closed mesh", closed.mesh_pass);
    expect_text("closed mesh sentence", closed.mesh_message, "PASS: mesh has volume.");
    expect("closed export allowed", closed.export_allowed);
    expect("closed block empty", closed.block_reason.empty());
    expect_text("closed export unit", closed.export_unit, "millimeter");
    expect_text("closed display", closed.display_unit, "mm");
    expect_exact("closed volume", closed.volume_mm3, 1.0);
    expect_exact("closed width", closed.width_mm, 1.0);
    expect_exact("closed depth", closed.depth_mm, 1.0);
    expect_exact("closed height", closed.height_mm, 1.0);
    expect("closed pass sentence", closed.watertight_message.find("PASS:") == 0);
    expect_text("closed units sentence", closed.units_message, "PASS: export unit is millimeter.");

    lock.toggle();
    const GateReport inches = evaluate_export_gate(closed_box(), lock);
    expect("inch display still exports", inches.export_allowed && inches.units_pass);
    expect_text("inch display label", inches.display_unit, "in");
    expect_text("inch export unit stays mm", inches.export_unit, "millimeter");
    expect_exact("inch toggle keeps mm volume", inches.volume_mm3, 1.0);

    const GateReport open = evaluate_export_gate(open_box(), UnitLock{});
    expect("open fails watertight", !open.watertight_pass);
    expect("open units still pass", open.units_pass);
    expect("open mesh", open.mesh_pass);
    expect("open export allowed", open.export_allowed);
    expect("open block empty", open.block_reason.empty());
    expect_text("open watertight sentence", open.watertight_message, watertight_fail);
    expect_exact("open volume times 6", open.volume_mm3 * 6.0, 4.0);

    const GateReport box = evaluate_export_gate(box_mm(20.0, 20.0, 20.0), UnitLock{});
    expect("20 mm box allowed", box.export_allowed && box.mesh_pass && box.watertight_pass && box.units_pass);
    expect_exact("20 mm volume", box.volume_mm3, 8000.0);
    expect_exact("20 mm width", box.width_mm, 20.0);

    const GateReport empty = evaluate_export_gate(MeshSolid{}, UnitLock{});
    expect("empty watertight fails", !empty.watertight_pass);
    expect("empty units pass", empty.units_pass);
    expect("empty mesh blocked", !empty.mesh_pass && !empty.export_allowed);
    expect_exact("empty volume", empty.volume_mm3, 0.0);
    expect_text("empty block", empty.block_reason, no_triangles);
    expect_text("empty mesh sentence", empty.mesh_message, no_triangles);
    expect("empty names the rule", empty.watertight_message.find("no triangles") != std::string::npos);

    MeshSolid flat;
    flat.vertices = {{0, 0, 0}, {20, 0, 0}, {20, 20, 0}, {0, 20, 0}};
    flat.triangles = {{0, 1, 2}, {0, 2, 3}};
    const GateReport degenerate = evaluate_export_gate(flat, UnitLock{});
    expect("flat has triangles", !flat.triangles.empty());
    expect("flat units pass", degenerate.units_pass);
    expect("flat mesh blocked", !degenerate.mesh_pass && !degenerate.export_allowed);
    expect_exact("flat volume", degenerate.volume_mm3, 0.0);
    expect_text("flat block", degenerate.block_reason, zero_volume);
    expect_text("flat mesh sentence", degenerate.mesh_message, zero_volume);

    const GateReport flipped = evaluate_export_gate(flipped_box(), UnitLock{});
    expect("flipped watertight fails", !flipped.watertight_pass);
    // flipped_box() reverses one face. That face lies on z = 0, so the signed
    // volume stays +1 and export stays allowed. A fully reversed shell is below.
    expect_exact("flipped volume", flipped.volume_mm3, 1.0);
    expect("flipped export allowed", flipped.export_allowed);
    expect("flipped block empty", flipped.block_reason.empty());
    expect("flipped names the winding", flipped.watertight_message.find("wound the same way") != std::string::npos);

    MeshSolid inside_out = closed_box();
    for (auto& triangle : inside_out.triangles) {
        const auto saved = triangle[1];
        triangle[1] = triangle[2];
        triangle[2] = saved;
    }
    const GateReport inward = evaluate_export_gate(inside_out, UnitLock{});
    expect("inside-out watertight fails", !inward.watertight_pass);
    expect("inside-out blocked", !inward.mesh_pass && !inward.export_allowed);
    expect_exact("inside-out volume", inward.volume_mm3, -1.0);
    expect_text("inside-out block", inward.block_reason, inside_out_reason);
    expect_text("inside-out sentence", inward.mesh_message, inside_out_reason);

    if (g_failures != 0) {
        std::cerr << g_failures << " failed\n";
        return EXIT_FAILURE;
    }
    std::cout << "ok\n";
    return EXIT_SUCCESS;
}
