#include "units.hpp"

#include <cmath>
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

void expect_record(const char* name, const UnitLock& lock) {
    const ExportUnitRecord record = export_units(lock);
    expect(name, record.display == lock.display());
    expect(name, std::string(record.storage) == "millimeter");
    expect(name, std::string(record.threemf_unit) == "millimeter");
    expect(name, std::string(record.stl_coordinate_unit) == "millimeter");
}

void check_identity(const UnitLock& lock, double millimeters) {
    expect_exact("display identity", lock.to_display(millimeters), millimeters);
    expect_exact("store identity", lock.to_millimeters(millimeters), millimeters);
}

void check_inches(UnitLock& lock) {
    const double stored = 25.4;
    expect_exact("25.4 mm shows as 1 in", lock.to_display(stored), 1.0);
    expect_exact("1 in stores as 25.4 mm", lock.to_millimeters(1.0), stored);
    expect_exact("0 in stays 0", lock.to_display(0.0), 0.0);
    expect_exact("0 displayed in stores 0 mm", lock.to_millimeters(0.0), 0.0);

    const double one_mm_shown = lock.to_display(1.0);
    expect_exact("1 mm shows as 1/25.4 in", one_mm_shown, 1.0 / kMmPerInch);
    const double one_mm_stored = lock.to_millimeters(one_mm_shown);
    const double one_mm_error = std::fabs(one_mm_stored - 1.0);
    if (one_mm_error > 1.2e-16) {
        std::cerr << "1/25.4 in stores within 1 ulp of 1 mm\n  got: " << one_mm_stored
                  << "\n  error: " << one_mm_error << '\n';
        ++g_failures;
    }

    expect_exact("inch round trip", lock.to_millimeters(lock.to_display(stored)), stored);
    expect_exact("mm value unchanged by display", stored, 25.4);
}

}  // namespace

int main() {
    UnitLock lock;
    expect("default is millimeter", lock.display() == DisplayUnit::Millimeter);
    expect("default name", std::string(display_unit_name(lock.display())) == "millimeter");
    check_identity(lock, 0.0);
    check_identity(lock, 1.0);
    check_identity(lock, 25.4);
    expect_record("mm export", lock);

    const double stored_mm = 25.4;
    lock.toggle();
    expect("toggle to inch", lock.display() == DisplayUnit::Inch);
    expect("inch name", std::string(display_unit_name(lock.display())) == "inch");
    expect_exact("stored mm unchanged after toggle", stored_mm, 25.4);
    check_inches(lock);
    expect_record("inch export", lock);

    lock.toggle();
    expect("toggle back to millimeter", lock.display() == DisplayUnit::Millimeter);
    check_identity(lock, stored_mm);
    expect_exact("back to mm shows 25.4", lock.to_display(stored_mm), stored_mm);
    expect_record("mm export again", lock);

    if (g_failures != 0) {
        std::cerr << g_failures << " failed\n";
        return EXIT_FAILURE;
    }
    std::cout << "ok\n";
    return EXIT_SUCCESS;
}
