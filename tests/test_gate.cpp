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
    expect_text("units block ignores watertight fail",
                export_block_reason(false, watertight_fail, false, units_fail), units_fail);
    expect_text("units block when solid passes",
                export_block_reason(true, "PASS", false, units_fail), units_fail);
    expect("units pass clears the block", export_block_reason(true, "PASS", true, units_ok).empty());
    expect("watertight fail does not block",
           export_block_reason(false, watertight_fail, true, units_ok).empty());

    UnitLock lock;
    const GateReport closed = evaluate_export_gate(closed_box(), lock);
    expect("closed watertight", closed.watertight_pass);
    expect("closed units", closed.units_pass);
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
    expect("open export allowed", open.export_allowed);
    expect("open block empty", open.block_reason.empty());
    expect_text("open watertight sentence", open.watertight_message, watertight_fail);
    expect_exact("open volume times 6", open.volume_mm3 * 6.0, 4.0);

    const GateReport box = evaluate_export_gate(box_mm(20.0, 20.0, 20.0), UnitLock{});
    expect("20 mm box allowed", box.export_allowed && box.watertight_pass && box.units_pass);
    expect_exact("20 mm volume", box.volume_mm3, 8000.0);
    expect_exact("20 mm width", box.width_mm, 20.0);

    const GateReport empty = evaluate_export_gate(MeshSolid{}, UnitLock{});
    expect("empty watertight fails", !empty.watertight_pass);
    expect("empty units pass", empty.units_pass);
    expect("empty export allowed", empty.export_allowed);
    expect_exact("empty volume", empty.volume_mm3, 0.0);
    expect("empty block empty", empty.block_reason.empty());
    expect("empty names the rule", empty.watertight_message.find("no triangles") != std::string::npos);

    const GateReport flipped = evaluate_export_gate(flipped_box(), UnitLock{});
    expect("flipped watertight fails", !flipped.watertight_pass);
    expect("flipped export allowed", flipped.export_allowed);
    expect("flipped block empty", flipped.block_reason.empty());
    expect("flipped names the winding", flipped.watertight_message.find("wound the same way") != std::string::npos);

    if (g_failures != 0) {
        std::cerr << g_failures << " failed\n";
        return EXIT_FAILURE;
    }
    std::cout << "ok\n";
    return EXIT_SUCCESS;
}
