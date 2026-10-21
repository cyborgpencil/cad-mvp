#pragma once

// Stored lengths are millimeters. DisplayUnit only changes presentation.
// See mvp/units.md.

enum class DisplayUnit { Millimeter, Inch };

inline constexpr double kMmPerInch = 25.4;

const char* display_unit_name(DisplayUnit unit);

class UnitLock {
public:
    DisplayUnit display() const;
    void toggle();
    double to_display(double millimeters) const;
    double to_millimeters(double displayed) const;

private:
    DisplayUnit display_ = DisplayUnit::Millimeter;
};

struct ExportUnitRecord {
    DisplayUnit display = DisplayUnit::Millimeter;
    static constexpr const char* storage = "millimeter";
    static constexpr const char* threemf_unit = "millimeter";
    static constexpr const char* stl_coordinate_unit = "millimeter";
};

ExportUnitRecord export_units(const UnitLock& lock);
