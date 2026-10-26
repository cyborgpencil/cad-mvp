use wasm_bindgen::prelude::*;

pub const MM_PER_INCH: f64 = 25.4;
pub const EXPORT_UNIT_MM: &str = "millimeter";
pub const VOLUME_EPSILON_MM3: f64 = 1e-9;

pub const MSG_UNITS_PASS: &str = "PASS: export unit is millimeter.";
pub const MSG_UNITS_FAIL: &str = "FAIL: export unit is not millimeter.";
pub const MSG_MESH_NO_TRIANGLES: &str = "FAIL: mesh has no triangles.";
pub const MSG_MESH_INSIDE_OUT: &str = "FAIL: mesh is inside-out (negative volume).";
pub const MSG_MESH_ZERO_VOLUME: &str = "FAIL: mesh has zero volume.";
pub const MSG_MESH_PASS: &str = "PASS: mesh has volume.";

#[derive(Debug, Clone, PartialEq)]
pub struct RustGateReport {
    pub units_pass: bool,
    pub mesh_pass: bool,
    pub export_allowed: bool,
    pub block_reason: String,
    pub units_message: String,
    pub mesh_message: String,
    pub volume_mm3: f64,
}

#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_name = Object)]
    type JsPlainObject;

    #[wasm_bindgen(constructor, js_class = "Object")]
    fn new() -> JsPlainObject;

    #[wasm_bindgen(js_namespace = Reflect, js_name = set)]
    fn reflect_set(target: &JsValue, key: &JsValue, value: &JsValue) -> bool;
}

fn set_prop(obj: &JsValue, key: &str, value: JsValue) {
    let _ = reflect_set(obj, &JsValue::from_str(key), &value);
}

/// Convert stored millimeters to the active display unit.
/// Divides by 25.4 only when `display_is_inch` is true.
#[wasm_bindgen]
pub fn to_display(mm: f64, display_is_inch: bool) -> f64 {
    if display_is_inch {
        mm / MM_PER_INCH
    } else {
        mm
    }
}

/// Convert a displayed length back into stored millimeters.
/// Multiplies by 25.4 only when `display_is_inch` is true.
#[wasm_bindgen]
pub fn to_millimeters(displayed: f64, display_is_inch: bool) -> f64 {
    if display_is_inch {
        displayed * MM_PER_INCH
    } else {
        displayed
    }
}

/// Returns true iff storage, 3MF, and STL unit strings all equal `"millimeter"`.
#[wasm_bindgen]
pub fn export_units_pass(storage: &str, threemf: &str, stl: &str) -> bool {
    storage == EXPORT_UNIT_MM && threemf == EXPORT_UNIT_MM && stl == EXPORT_UNIT_MM
}

/// Signed mesh volume in cubic millimeters using the same triple-product / 6
/// accumulation as `mesh_volume_mm3` in `src/export/gate.cpp`.
/// Triangles with any vertex index >= vertex count are skipped.
#[wasm_bindgen]
pub fn mesh_volume_mm3(vertices_xyz: &[f64], triangles_ijk: &[u32]) -> f64 {
    let vertex_count = vertices_xyz.len() / 3;
    let mut six_volumes: f64 = 0.0;
    for tri in triangles_ijk.chunks_exact(3) {
        let i0 = tri[0] as usize;
        let i1 = tri[1] as usize;
        let i2 = tri[2] as usize;
        if i0 >= vertex_count || i1 >= vertex_count || i2 >= vertex_count {
            continue;
        }
        let ax = vertices_xyz[i0 * 3];
        let ay = vertices_xyz[i0 * 3 + 1];
        let az = vertices_xyz[i0 * 3 + 2];

        let bx = vertices_xyz[i1 * 3];
        let by = vertices_xyz[i1 * 3 + 1];
        let bz = vertices_xyz[i1 * 3 + 2];

        let cx = vertices_xyz[i2 * 3];
        let cy = vertices_xyz[i2 * 3 + 1];
        let cz = vertices_xyz[i2 * 3 + 2];

        let cross_x = by * cz - bz * cy;
        let cross_y = bz * cx - bx * cz;
        let cross_z = bx * cy - by * cx;
        six_volumes += ax * cross_x + ay * cross_y + az * cross_z;
    }
    six_volumes / 6.0
}

/// Pure-Rust evaluation of the units + mesh volume Export gate (mirrors `src/export/gate.cpp`).
pub fn evaluate_rust_gate_report(
    vertices_xyz: &[f64],
    triangles_ijk: &[u32],
    storage: &str,
    threemf: &str,
    stl: &str,
) -> RustGateReport {
    let units_pass = export_units_pass(storage, threemf, stl);
    let units_message = if units_pass {
        MSG_UNITS_PASS.to_string()
    } else {
        MSG_UNITS_FAIL.to_string()
    };

    let has_triangles = triangles_ijk.len() >= 3;
    let volume_mm3 = mesh_volume_mm3(vertices_xyz, triangles_ijk);
    let mesh_pass = has_triangles && volume_mm3 > VOLUME_EPSILON_MM3;
    let mesh_message = if !has_triangles {
        MSG_MESH_NO_TRIANGLES.to_string()
    } else if volume_mm3 < -VOLUME_EPSILON_MM3 {
        MSG_MESH_INSIDE_OUT.to_string()
    } else if volume_mm3 <= VOLUME_EPSILON_MM3 {
        MSG_MESH_ZERO_VOLUME.to_string()
    } else {
        MSG_MESH_PASS.to_string()
    };

    let export_allowed = units_pass && mesh_pass;
    let block_reason = if !units_pass {
        units_message.clone()
    } else if !mesh_pass {
        mesh_message.clone()
    } else {
        String::new()
    };

    RustGateReport {
        units_pass,
        mesh_pass,
        export_allowed,
        block_reason,
        units_message,
        mesh_message,
        volume_mm3,
    }
}

/// WASM-exported Export gate evaluation matching `evaluate_export_gate` in `src/export/gate.cpp`.
/// Ignores watertight for allow/block (units then mesh volume only).
#[wasm_bindgen]
pub fn evaluate_rust_gate(
    vertices_xyz: &[f64],
    triangles_ijk: &[u32],
    storage: &str,
    threemf: &str,
    stl: &str,
) -> JsValue {
    let report = evaluate_rust_gate_report(vertices_xyz, triangles_ijk, storage, threemf, stl);
    let obj: JsValue = JsPlainObject::new().into();
    set_prop(&obj, "units_pass", JsValue::from_bool(report.units_pass));
    set_prop(&obj, "mesh_pass", JsValue::from_bool(report.mesh_pass));
    set_prop(&obj, "export_allowed", JsValue::from_bool(report.export_allowed));
    set_prop(&obj, "block_reason", JsValue::from_str(&report.block_reason));
    set_prop(&obj, "units_message", JsValue::from_str(&report.units_message));
    set_prop(&obj, "mesh_message", JsValue::from_str(&report.mesh_message));
    set_prop(&obj, "volume_mm3", JsValue::from_f64(report.volume_mm3));
    set_prop(&obj, "unitsPass", JsValue::from_bool(report.units_pass));
    set_prop(&obj, "meshPass", JsValue::from_bool(report.mesh_pass));
    set_prop(&obj, "exportAllowed", JsValue::from_bool(report.export_allowed));
    set_prop(&obj, "blockReason", JsValue::from_str(&report.block_reason));
    set_prop(&obj, "unitsMessage", JsValue::from_str(&report.units_message));
    set_prop(&obj, "meshMessage", JsValue::from_str(&report.mesh_message));
    set_prop(&obj, "volumeMm3", JsValue::from_f64(report.volume_mm3));
    obj
}

#[cfg(test)]
mod tests {
    use super::*;

    fn closed_box_buffers() -> (Vec<f64>, Vec<u32>) {
        let vertices = vec![
            0.0, 0.0, 0.0, // 0
            1.0, 0.0, 0.0, // 1
            1.0, 1.0, 0.0, // 2
            0.0, 1.0, 0.0, // 3
            0.0, 0.0, 1.0, // 4
            1.0, 0.0, 1.0, // 5
            1.0, 1.0, 1.0, // 6
            0.0, 1.0, 1.0, // 7
        ];
        let triangles = vec![
            0, 2, 1, 0, 3, 2, // bottom, outward -Z
            4, 5, 6, 4, 6, 7, // top, outward +Z
            0, 5, 4, 0, 1, 5, // y = 0, outward -Y
            3, 6, 2, 3, 7, 6, // y = 1, outward +Y
            0, 7, 3, 0, 4, 7, // x = 0, outward -X
            1, 2, 6, 1, 6, 5, // x = 1, outward +X
        ];
        (vertices, triangles)
    }

    #[test]
    fn units_conversion_and_round_trip() {
        // Millimeter identity
        assert_eq!(to_display(0.0, false), 0.0);
        assert_eq!(to_millimeters(0.0, false), 0.0);
        assert_eq!(to_display(1.0, false), 1.0);
        assert_eq!(to_millimeters(1.0, false), 1.0);
        assert_eq!(to_display(25.4, false), 25.4);
        assert_eq!(to_millimeters(25.4, false), 25.4);

        // Inch display conversion & exact round-trip for 0 and 25.4 mm
        assert_eq!(to_display(0.0, true), 0.0);
        assert_eq!(to_millimeters(0.0, true), 0.0);
        assert_eq!(to_display(25.4, true), 1.0);
        assert_eq!(to_millimeters(1.0, true), 25.4);
        assert_eq!(to_millimeters(to_display(25.4, true), true), 25.4);

        // 1 mm -> inch display -> store again within 1 double ulp of 1.0
        let one_mm_shown = to_display(1.0, true);
        assert_eq!(one_mm_shown, 1.0 / 25.4);
        let one_mm_stored = to_millimeters(one_mm_shown, true);
        assert!((one_mm_stored - 1.0).abs() <= f64::EPSILON);
    }

    #[test]
    fn units_gate_checks_all_three_strings() {
        assert!(export_units_pass("millimeter", "millimeter", "millimeter"));
        assert!(!export_units_pass("inch", "millimeter", "millimeter"));
        assert!(!export_units_pass("millimeter", "inch", "millimeter"));
        assert!(!export_units_pass("millimeter", "millimeter", "inch"));
        assert!(!export_units_pass("", "millimeter", "millimeter"));
    }

    #[test]
    fn gate_matches_cpp_for_closed_open_20mm_empty_flat_and_inside_out() {
        let (v_closed, t_closed) = closed_box_buffers();
        let closed = evaluate_rust_gate_report(&v_closed, &t_closed, "millimeter", "millimeter", "millimeter");
        assert!(closed.units_pass);
        assert!(closed.mesh_pass);
        assert!(closed.export_allowed);
        assert_eq!(closed.volume_mm3, 1.0);
        assert_eq!(closed.units_message, "PASS: export unit is millimeter.");
        assert_eq!(closed.mesh_message, "PASS: mesh has volume.");
        assert_eq!(closed.block_reason, "");

        // 20 mm box
        let v_box20: Vec<f64> = v_closed.iter().map(|x| x * 20.0).collect();
        let box20 = evaluate_rust_gate_report(&v_box20, &t_closed, "millimeter", "millimeter", "millimeter");
        assert!(box20.export_allowed);
        assert_eq!(box20.volume_mm3, 8000.0);

        // Empty mesh
        let empty = evaluate_rust_gate_report(&[], &[], "millimeter", "millimeter", "millimeter");
        assert!(empty.units_pass);
        assert!(!empty.mesh_pass);
        assert!(!empty.export_allowed);
        assert_eq!(empty.volume_mm3, 0.0);
        assert_eq!(empty.mesh_message, "FAIL: mesh has no triangles.");
        assert_eq!(empty.block_reason, "FAIL: mesh has no triangles.");

        // Units failure beats empty mesh
        let units_beat_empty = evaluate_rust_gate_report(&[], &[], "inch", "millimeter", "millimeter");
        assert!(!units_beat_empty.units_pass);
        assert!(!units_beat_empty.mesh_pass);
        assert!(!units_beat_empty.export_allowed);
        assert_eq!(units_beat_empty.block_reason, "FAIL: export unit is not millimeter.");

        // Flat / zero volume mesh
        let v_flat = vec![0.0, 0.0, 0.0, 20.0, 0.0, 0.0, 20.0, 20.0, 0.0, 0.0, 20.0, 0.0];
        let t_flat = vec![0, 1, 2, 0, 2, 3];
        let flat = evaluate_rust_gate_report(&v_flat, &t_flat, "millimeter", "millimeter", "millimeter");
        assert!(flat.units_pass);
        assert!(!flat.mesh_pass);
        assert!(!flat.export_allowed);
        assert_eq!(flat.volume_mm3, 0.0);
        assert_eq!(flat.mesh_message, "FAIL: mesh has zero volume.");
        assert_eq!(flat.block_reason, "FAIL: mesh has zero volume.");

        // Inside-out mesh (all triangles reversed -> volume -1.0)
        let mut t_inside_out = t_closed.clone();
        for tri in t_inside_out.chunks_exact_mut(3) {
            tri.swap(1, 2);
        }
        let inside_out = evaluate_rust_gate_report(&v_closed, &t_inside_out, "millimeter", "millimeter", "millimeter");
        assert!(inside_out.units_pass);
        assert!(!inside_out.mesh_pass);
        assert!(!inside_out.export_allowed);
        assert_eq!(inside_out.volume_mm3, -1.0);
        assert_eq!(inside_out.mesh_message, "FAIL: mesh is inside-out (negative volume).");
        assert_eq!(inside_out.block_reason, "FAIL: mesh is inside-out (negative volume).");
    }
}
