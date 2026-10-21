# Units lock

**Status**: Built
**Date**: 2026-10-20
**Scope**: Display conversion and export metadata only. Does not change `mvp/requirements.md`.

Stored geometry and lengths are millimeters. See the units row in [requirements.md](requirements.md).

The display unit is `Millimeter` or `Inch`, stored on `UnitLock`. The default is millimeters. `toggle()` flips that setting and does not scale stored numbers. One inch is exactly 25.4 millimeters.

- `to_display` divides by 25.4 only while the display unit is inches.
- `to_millimeters` multiplies by 25.4 only while the display unit is inches.
- `0` and `25.4` millimeters round-trip exactly. `1` millimeter shown in inches and stored again lands within one double ulp of `1`, because `25.4` is not a binary fraction.

`ExportUnitRecord` is the note a later STL or 3MF writer will copy. Storage, the 3MF `unit` attribute, and the STL coordinate unit stay `millimeter`, because the coordinates stay in millimeters. STL has no unit field, so the record is what a later export will keep beside the file. The record's display field follows the toggle.

`src/solid` is unchanged. The mesh window properties panel now calls this lock: Millimeters and Inches rewrite the spin boxes and the measure readout, and the stored millimeter fields stay put.
