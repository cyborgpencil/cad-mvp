#include "units.hpp"

const char* display_unit_name(DisplayUnit unit) {
    if (unit == DisplayUnit::Inch) {
        return "inch";
    }
    return "millimeter";
}

DisplayUnit UnitLock::display() const {
    return display_;
}

void UnitLock::toggle() {
    if (display_ == DisplayUnit::Millimeter) {
        display_ = DisplayUnit::Inch;
    } else {
        display_ = DisplayUnit::Millimeter;
    }
}

double UnitLock::to_display(double millimeters) const {
    if (display_ == DisplayUnit::Inch) {
        return millimeters / kMmPerInch;
    }
    return millimeters;
}

double UnitLock::to_millimeters(double displayed) const {
    if (display_ == DisplayUnit::Inch) {
        return displayed * kMmPerInch;
    }
    return displayed;
}

ExportUnitRecord export_units(const UnitLock& lock) {
    ExportUnitRecord record;
    record.display = lock.display();
    return record;
}
