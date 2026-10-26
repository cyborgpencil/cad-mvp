use std::collections::HashMap;
use std::fs::File;
use std::io::{Cursor, Read, Write};
use std::path::Path;
use std::process::ExitCode;

use quick_xml::events::{BytesStart, Event};
use quick_xml::Reader;
use zip::ZipArchive;

const DEFAULT_SIZE_TOL: f64 = 0.1;
const DEFAULT_VOLUME_REL_TOL: f64 = 0.01;

#[derive(Debug, Clone)]
struct CliArgs {
    paths: Vec<String>,
    expect_size: [f64; 3],
    expect_volume: f64,
    size_tol: f64,
    volume_rel_tol: f64,
}

#[derive(Debug, Clone)]
struct LoadedMesh {
    vertices_xyz: Vec<f64>,
    triangles_ijk: Vec<u32>,
}

#[derive(Debug, Clone)]
struct LoadError(String);

impl std::fmt::Display for LoadError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

fn emit(out: &mut dyn Write, line: &str) {
    let _ = writeln!(out, "{line}");
    let _ = out.flush();
}

fn fail(out: &mut dyn Write, message: &str) {
    emit(out, &format!("FAIL: {message}"));
}

fn passed(out: &mut dyn Write, message: &str) {
    emit(out, &format!("PASS: {message}"));
}

fn error(err: &mut dyn Write, message: &str) {
    let _ = writeln!(err, "ERROR: {message}");
    let _ = err.flush();
}

/// Format a floating-point number the same way `fmt` does in `tools/check_export.py`:
/// six digits after the decimal, strip trailing zeros and a dangling decimal point;
/// non-finite stays the default rendering; blank / `-` / `-0` print as `0`.
pub fn fmt(value: f64) -> String {
    if !value.is_finite() {
        if value.is_nan() {
            return "nan".to_string();
        } else if value.is_sign_negative() {
            return "-inf".to_string();
        } else {
            return "inf".to_string();
        }
    }
    let formatted = format!("{value:.6}");
    let trimmed = formatted.trim_end_matches('0').trim_end_matches('.');
    if matches!(trimmed, "" | "-" | "-0") {
        "0".to_string()
    } else {
        trimmed.to_string()
    }
}

/// Signed mesh volume in cubic millimeters using the same triple-product / 6
/// accumulation as `mesh_volume_mm3` in `rust/cadcam_gate/src/lib.rs` and `src/export/gate.cpp`.
/// Triangles with any vertex index >= vertex count are skipped.
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

/// Compute axis-aligned bounding box extents (max - min) on each axis in millimeters.
/// Returns `None` if there are no valid triangles or if any coordinate is non-finite.
fn mesh_extents_mm(vertices_xyz: &[f64], triangles_ijk: &[u32]) -> Option<[f64; 3]> {
    let vertex_count = vertices_xyz.len() / 3;
    if triangles_ijk.len() < 3 || vertex_count == 0 {
        return None;
    }
    let mut min_x = f64::INFINITY;
    let mut min_y = f64::INFINITY;
    let mut min_z = f64::INFINITY;
    let mut max_x = f64::NEG_INFINITY;
    let mut max_y = f64::NEG_INFINITY;
    let mut max_z = f64::NEG_INFINITY;
    let mut any_vertex = false;

    for &idx in triangles_ijk {
        let i = idx as usize;
        if i >= vertex_count {
            return None;
        }
        let x = vertices_xyz[i * 3];
        let y = vertices_xyz[i * 3 + 1];
        let z = vertices_xyz[i * 3 + 2];
        if !x.is_finite() || !y.is_finite() || !z.is_finite() {
            return None;
        }
        min_x = min_x.min(x);
        min_y = min_y.min(y);
        min_z = min_z.min(z);
        max_x = max_x.max(x);
        max_y = max_y.max(y);
        max_z = max_z.max(z);
        any_vertex = true;
    }

    if !any_vertex {
        return None;
    }
    let extents = [max_x - min_x, max_y - min_y, max_z - min_z];
    if extents.iter().all(|v| v.is_finite()) {
        Some(extents)
    } else {
        None
    }
}

/// Small in-crate closed-shell watertight check:
/// - Welds vertices at 1e-6 mm quantum (matching `weld_mesh` in `src/export/threemf.cpp`).
/// - Requires non-empty triangles, no degenerate / zero-area triangles,
///   every undirected edge shared by exactly 2 triangles, every directed edge used once,
///   and positive signed volume.
/// Never decides the CLI exit code (INFO only).
pub fn is_mesh_watertight(vertices_xyz: &[f64], triangles_ijk: &[u32]) -> bool {
    let vertex_count = vertices_xyz.len() / 3;
    if triangles_ijk.len() < 3 || triangles_ijk.len() % 3 != 0 || vertex_count == 0 {
        return false;
    }

    const QUANTUM_MM: f64 = 1e-6;
    let mut remap = Vec::with_capacity(vertex_count);
    let mut unique_coords: Vec<[f64; 3]> = Vec::new();
    let mut vertex_map: HashMap<[i64; 3], u32> = HashMap::new();

    for i in 0..vertex_count {
        let x = vertices_xyz[i * 3];
        let y = vertices_xyz[i * 3 + 1];
        let z = vertices_xyz[i * 3 + 2];
        if !x.is_finite() || !y.is_finite() || !z.is_finite() {
            return false;
        }
        let key = [
            (x / QUANTUM_MM).round() as i64,
            (y / QUANTUM_MM).round() as i64,
            (z / QUANTUM_MM).round() as i64,
        ];
        let id = *vertex_map.entry(key).or_insert_with(|| {
            let next_id = unique_coords.len() as u32;
            unique_coords.push([x, y, z]);
            next_id
        });
        remap.push(id);
    }

    let mut undirected: HashMap<(u32, u32), u32> = HashMap::new();
    let mut directed: HashMap<(u32, u32), u32> = HashMap::new();

    for tri in triangles_ijk.chunks_exact(3) {
        let i0 = tri[0] as usize;
        let i1 = tri[1] as usize;
        let i2 = tri[2] as usize;
        if i0 >= vertex_count || i1 >= vertex_count || i2 >= vertex_count {
            return false;
        }
        let a = remap[i0];
        let b = remap[i1];
        let c = remap[i2];
        if a == b || b == c || a == c {
            return false;
        }

        let va = unique_coords[a as usize];
        let vb = unique_coords[b as usize];
        let vc = unique_coords[c as usize];
        let ux = vb[0] - va[0];
        let uy = vb[1] - va[1];
        let uz = vb[2] - va[2];
        let vx = vc[0] - va[0];
        let vy = vc[1] - va[1];
        let vz = vc[2] - va[2];
        let cx = uy * vz - uz * vy;
        let cy = uz * vx - ux * vz;
        let cz = ux * vy - uy * vx;
        if cx == 0.0 && cy == 0.0 && cz == 0.0 {
            return false;
        }

        for &(from, to) in &[(a, b), (b, c), (c, a)] {
            *directed.entry((from, to)).or_insert(0) += 1;
            let edge = if from < to { (from, to) } else { (to, from) };
            *undirected.entry(edge).or_insert(0) += 1;
        }
    }

    if undirected.values().any(|&count| count != 2) {
        return false;
    }
    if directed.values().any(|&count| count != 1) {
        return false;
    }

    mesh_volume_mm3(vertices_xyz, triangles_ijk) > 0.0
}

fn indexed_mesh_to_loaded(path: &Path, mesh: stl_io::IndexedMesh) -> Result<LoadedMesh, LoadError> {
    let mut vertices_xyz = Vec::with_capacity(mesh.vertices.len() * 3);
    for v in &mesh.vertices {
        let x = v[0] as f64;
        let y = v[1] as f64;
        let z = v[2] as f64;
        if !x.is_finite() || !y.is_finite() || !z.is_finite() {
            return Err(LoadError(format!(
                "{}: STL contains non-finite vertex coordinates.",
                path.display()
            )));
        }
        vertices_xyz.push(x);
        vertices_xyz.push(y);
        vertices_xyz.push(z);
    }

    let mut triangles_ijk = Vec::with_capacity(mesh.faces.len() * 3);
    for face in &mesh.faces {
        if face.vertices[0] >= mesh.vertices.len()
            || face.vertices[1] >= mesh.vertices.len()
            || face.vertices[2] >= mesh.vertices.len()
        {
            return Err(LoadError(format!(
                "{}: STL triangle vertex index out of bounds.",
                path.display()
            )));
        }
        triangles_ijk.push(face.vertices[0] as u32);
        triangles_ijk.push(face.vertices[1] as u32);
        triangles_ijk.push(face.vertices[2] as u32);
    }

    Ok(LoadedMesh {
        vertices_xyz,
        triangles_ijk,
    })
}

fn is_exact_binary_stl_size(bytes: &[u8]) -> bool {
    if bytes.len() < 84 {
        return false;
    }
    let count = u32::from_le_bytes([bytes[80], bytes[81], bytes[82], bytes[83]]) as usize;
    bytes
        .len()
        .checked_sub(84)
        .is_some_and(|rem| rem == count.saturating_mul(50) && count <= 10_000_000)
}

fn load_stl(path: &Path) -> Result<LoadedMesh, LoadError> {
    let bytes = std::fs::read(path)
        .map_err(|exc| LoadError(format!("{}: could not read STL ({exc}).", path.display())))?;

    // Check if the file starts with ASCII "solid" header (including "solid\n" or "solid\r\n" without space).
    let starts_with_solid = bytes.starts_with(b"solid ")
        || bytes.starts_with(b"solid\n")
        || bytes.starts_with(b"solid\r\n")
        || bytes.starts_with(b"solid\t");

    if starts_with_solid {
        // Normalize "solid\n" / "solid\r\n" / "solid\t" to "solid " so stl_io's probe recognizes it.
        let normalized: Vec<u8> = if bytes.starts_with(b"solid ") {
            bytes.clone()
        } else {
            let mut buf = Vec::with_capacity(bytes.len() + 1);
            buf.extend_from_slice(b"solid ");
            buf.extend_from_slice(&bytes[5..]);
            buf
        };
        let mut cursor = Cursor::new(normalized);
        match stl_io::read_stl(&mut cursor) {
            Ok(mesh) => return indexed_mesh_to_loaded(path, mesh),
            Err(ascii_err) => {
                // Fallback only if this is a binary STL whose 80-byte header happens to begin with "solid".
                if is_exact_binary_stl_size(&bytes) {
                    let mut bin_bytes = bytes;
                    bin_bytes[0..5].copy_from_slice(b"binst");
                    let mut bin_cursor = Cursor::new(bin_bytes);
                    let mesh = stl_io::read_stl(&mut bin_cursor).map_err(|exc| {
                        LoadError(format!("{}: could not load STL ({exc}).", path.display()))
                    })?;
                    return indexed_mesh_to_loaded(path, mesh);
                }
                return Err(LoadError(format!(
                    "{}: could not load STL ({ascii_err}).",
                    path.display()
                )));
            }
        }
    }

    // Binary STL must match the exact 84 + 50 * count byte layout.
    if !is_exact_binary_stl_size(&bytes) {
        return Err(LoadError(format!(
            "{}: not a valid ASCII or binary STL file.",
            path.display()
        )));
    }

    let mut cursor = Cursor::new(bytes);
    let mesh = stl_io::read_stl(&mut cursor)
        .map_err(|exc| LoadError(format!("{}: could not load STL ({exc}).", path.display())))?;
    indexed_mesh_to_loaded(path, mesh)
}

fn xml_local_name(raw: &[u8]) -> Result<&str, String> {
    let text = std::str::from_utf8(raw).map_err(|e| e.to_string())?;
    let after_brace = match text.rsplit_once('}') {
        Some((_, local)) => local,
        None => text,
    };
    let after_colon = match after_brace.rsplit_once(':') {
        Some((_, local)) => local,
        None => after_brace,
    };
    Ok(after_colon)
}

fn is_xmlns_attr(raw: &[u8]) -> bool {
    raw == b"xmlns" || raw.starts_with(b"xmlns:")
}

fn parse_3mf_element_attrs(
    e: &BytesStart<'_>,
) -> Result<Vec<(String, String)>, String> {
    let mut attrs = Vec::new();
    for attr_res in e.attributes().with_checks(true) {
        let attr = attr_res.map_err(|err| err.to_string())?;
        if is_xmlns_attr(attr.key.as_ref()) {
            continue;
        }
        let key = xml_local_name(attr.key.as_ref())?.to_string();
        let value = attr
            .unescape_value()
            .map_err(|err| err.to_string())?
            .into_owned();
        attrs.push((key, value));
    }
    Ok(attrs)
}

fn read_3mf(path: &Path) -> Result<(Option<String>, LoadedMesh), LoadError> {
    let file = File::open(path)
        .map_err(|exc| LoadError(format!("{}: {exc}.", path.display())))?;
    let mut archive = ZipArchive::new(file)
        .map_err(|exc| LoadError(format!("{}: not a readable 3MF zip ({exc}).", path.display())))?;

    let mut model_name: Option<String> = None;
    for i in 0..archive.len() {
        let entry = archive.by_index_raw(i).map_err(|exc| {
            LoadError(format!("{}: not a readable 3MF zip ({exc}).", path.display()))
        })?;
        let name = entry.name().to_string();
        let normalized = name.replace('\\', "/");
        let normalized = normalized.trim_start_matches('/');
        if normalized.eq_ignore_ascii_case("3d/3dmodel.model") {
            model_name = Some(name);
            break;
        }
    }

    let Some(model_name) = model_name else {
        return Err(LoadError(format!(
            "{}: 3MF is missing 3D/3dmodel.model.",
            path.display()
        )));
    };

    let mut payload = Vec::new();
    {
        let mut model_file = archive.by_name(&model_name).map_err(|exc| {
            LoadError(format!(
                "{}: could not read 3D/3dmodel.model ({exc}).",
                path.display()
            ))
        })?;
        model_file.read_to_end(&mut payload).map_err(|exc| {
            LoadError(format!(
                "{}: could not read 3D/3dmodel.model ({exc}).",
                path.display()
            ))
        })?;
    }

    parse_3mf_model_xml(path, &payload)
}

#[derive(Default)]
struct ModelXmlState {
    saw_model: bool,
    model_unit: Option<String>,
    saw_mesh: bool,
    in_mesh: bool,
    current_vertices: Vec<f64>,
    current_triangles: Vec<u32>,
    all_vertices_xyz: Vec<f64>,
    all_triangles_ijk: Vec<u32>,
}

impl ModelXmlState {
    fn handle_element_open(
        &mut self,
        path: &Path,
        local: &str,
        attrs: &[(String, String)],
        is_empty: bool,
    ) -> Result<(), LoadError> {
        if local == "model" && !self.saw_model {
            self.saw_model = true;
            for (k, v) in attrs {
                if k == "unit" {
                    self.model_unit = Some(v.clone());
                    break;
                }
            }
        } else if local == "mesh" {
            if self.in_mesh {
                return Err(LoadError(format!(
                    "{}: nested mesh element in 3D/3dmodel.model.",
                    path.display()
                )));
            }
            self.saw_mesh = true;
            if !is_empty {
                self.in_mesh = true;
                self.current_vertices.clear();
                self.current_triangles.clear();
            }
        } else if local == "vertex" && self.in_mesh {
            let mut x_val: Option<f64> = None;
            let mut y_val: Option<f64> = None;
            let mut z_val: Option<f64> = None;
            for (k, v) in attrs {
                match k.as_str() {
                    "x" => x_val = v.parse::<f64>().ok().filter(|n| n.is_finite()),
                    "y" => y_val = v.parse::<f64>().ok().filter(|n| n.is_finite()),
                    "z" => z_val = v.parse::<f64>().ok().filter(|n| n.is_finite()),
                    _ => {}
                }
            }
            let (Some(x), Some(y), Some(z)) = (x_val, y_val, z_val) else {
                return Err(LoadError(format!(
                    "{}: invalid vertex attributes in 3D/3dmodel.model.",
                    path.display()
                )));
            };
            self.current_vertices.push(x);
            self.current_vertices.push(y);
            self.current_vertices.push(z);
        } else if local == "triangle" && self.in_mesh {
            let mut v1_val: Option<u32> = None;
            let mut v2_val: Option<u32> = None;
            let mut v3_val: Option<u32> = None;
            for (k, v) in attrs {
                match k.as_str() {
                    "v1" => v1_val = v.parse::<u32>().ok(),
                    "v2" => v2_val = v.parse::<u32>().ok(),
                    "v3" => v3_val = v.parse::<u32>().ok(),
                    _ => {}
                }
            }
            let (Some(v1), Some(v2), Some(v3)) = (v1_val, v2_val, v3_val) else {
                return Err(LoadError(format!(
                    "{}: invalid triangle attributes in 3D/3dmodel.model.",
                    path.display()
                )));
            };
            self.current_triangles.push(v1);
            self.current_triangles.push(v2);
            self.current_triangles.push(v3);
        }
        Ok(())
    }

    fn finish_mesh(&mut self, path: &Path) -> Result<(), LoadError> {
        let vertex_count = self.current_vertices.len() / 3;
        for &idx in &self.current_triangles {
            if (idx as usize) >= vertex_count {
                return Err(LoadError(format!(
                    "{}: triangle vertex index {idx} out of bounds (vertex count {vertex_count}).",
                    path.display()
                )));
            }
        }
        let base = (self.all_vertices_xyz.len() / 3) as u32;
        self.all_vertices_xyz
            .extend_from_slice(&self.current_vertices);
        for &idx in &self.current_triangles {
            self.all_triangles_ijk.push(base + idx);
        }
        self.current_vertices.clear();
        self.current_triangles.clear();
        self.in_mesh = false;
        Ok(())
    }
}

fn parse_3mf_model_xml(
    path: &Path,
    payload: &[u8],
) -> Result<(Option<String>, LoadedMesh), LoadError> {
    let xml_str = std::str::from_utf8(payload).map_err(|exc| {
        LoadError(format!(
            "{}: 3D/3dmodel.model is not XML ({exc}).",
            path.display()
        ))
    })?;

    let mut reader = Reader::from_str(xml_str);
    reader.config_mut().check_end_names = true;
    reader.config_mut().check_comments = true;

    let mut saw_root = false;
    let mut root_closed = false;
    let mut tag_stack: Vec<String> = Vec::new();
    let mut state = ModelXmlState::default();

    let xml_err = |msg: String| {
        LoadError(format!(
            "{}: 3D/3dmodel.model is not XML ({msg}).",
            path.display()
        ))
    };

    loop {
        match reader.read_event() {
            Ok(Event::Start(ref e)) => {
                if root_closed {
                    return Err(xml_err("multiple root elements".to_string()));
                }
                saw_root = true;
                let qname = e.name();
                let local = xml_local_name(qname.as_ref()).map_err(xml_err)?.to_string();
                let attrs = parse_3mf_element_attrs(e).map_err(xml_err)?;
                state.handle_element_open(path, &local, &attrs, false)?;
                tag_stack.push(local);
            }
            Ok(Event::Empty(ref e)) => {
                if root_closed {
                    return Err(xml_err("multiple root elements".to_string()));
                }
                saw_root = true;
                let qname = e.name();
                let local = xml_local_name(qname.as_ref()).map_err(xml_err)?.to_string();
                let attrs = parse_3mf_element_attrs(e).map_err(xml_err)?;
                state.handle_element_open(path, &local, &attrs, true)?;
                if tag_stack.is_empty() {
                    root_closed = true;
                }
            }
            Ok(Event::End(ref e)) => {
                let qname = e.name();
                let local = xml_local_name(qname.as_ref()).map_err(xml_err)?.to_string();
                let Some(expected) = tag_stack.pop() else {
                    return Err(xml_err(format!("unexpected closing tag </{local}>")));
                };
                if expected != local {
                    return Err(xml_err(format!(
                        "mismatched closing tag: expected </{expected}>, got </{local}>"
                    )));
                }
                if local == "mesh" && state.in_mesh {
                    state.finish_mesh(path)?;
                }
                if tag_stack.is_empty() {
                    root_closed = true;
                }
            }
            Ok(Event::Text(ref e)) => {
                let unescaped = e.unescape().map_err(|err| xml_err(err.to_string()))?;
                if tag_stack.is_empty() && !unescaped.trim().is_empty() {
                    return Err(xml_err("text outside root element".to_string()));
                }
            }
            Ok(Event::Decl(_)) | Ok(Event::Comment(_)) | Ok(Event::PI(_)) | Ok(Event::CData(_)) => {
            }
            Ok(Event::DocType(_)) => {}
            Ok(Event::Eof) => break,
            Err(err) => return Err(xml_err(err.to_string())),
        }
    }

    if !saw_root || !tag_stack.is_empty() {
        return Err(xml_err("unexpected EOF".to_string()));
    }
    if !state.saw_model {
        return Err(LoadError(format!(
            "{}: 3D/3dmodel.model has no model element.",
            path.display()
        )));
    }
    if !state.saw_mesh {
        return Err(LoadError(format!(
            "{}: 3D/3dmodel.model has no mesh element.",
            path.display()
        )));
    }

    Ok((
        state.model_unit,
        LoadedMesh {
            vertices_xyz: state.all_vertices_xyz,
            triangles_ijk: state.all_triangles_ijk,
        },
    ))
}

fn check_file(
    label: &str,
    path: &Path,
    expect_size: [f64; 3],
    expect_volume: f64,
    size_tol: f64,
    volume_rel_tol: f64,
    out: &mut dyn Write,
) -> Result<bool, LoadError> {
    let suffix = path
        .extension()
        .and_then(|s| s.to_str())
        .map(|s| format!(".{}", s.to_ascii_lowercase()))
        .unwrap_or_default();

    if suffix != ".stl" && suffix != ".3mf" {
        return Err(LoadError(format!(
            "{}: expected an .stl or .3mf file.",
            path.display()
        )));
    }
    if !path.is_file() {
        return Err(LoadError(format!("{}: file not found.", path.display())));
    }

    let (unit, mesh) = if suffix == ".3mf" {
        let (u, m) = read_3mf(path)?;
        (u, m)
    } else {
        (None, load_stl(path)?)
    };

    emit(out, label);
    let mut ok = true;

    let mut failed = |out: &mut dyn Write, message: &str| {
        ok = false;
        fail(out, message);
    };

    if suffix == ".3mf" {
        match unit.as_deref() {
            None => failed(out, "export unit attribute is missing."),
            Some("millimeter") => passed(out, "export unit is millimeter."),
            Some(_) => failed(out, "export unit is not millimeter."),
        }
    }

    let triangle_count = mesh.triangles_ijk.len() / 3;
    if triangle_count == 0 {
        failed(out, "mesh has no triangles.");
    } else {
        match mesh_extents_mm(&mesh.vertices_xyz, &mesh.triangles_ijk) {
            None => failed(out, "bbox extents are missing."),
            Some(actual) => {
                let bad_extents = actual.iter().any(|v| !v.is_finite())
                    || actual
                        .iter()
                        .zip(expect_size.iter())
                        .any(|(got, want)| (got - want).abs() > size_tol);
                let got_text = format!("{} {} {}", fmt(actual[0]), fmt(actual[1]), fmt(actual[2]));
                if bad_extents {
                    let want_text = format!(
                        "{} {} {}",
                        fmt(expect_size[0]),
                        fmt(expect_size[1]),
                        fmt(expect_size[2])
                    );
                    failed(
                        out,
                        &format!("bbox extents are {got_text} mm, expected {want_text} mm."),
                    );
                } else {
                    passed(out, &format!("bbox extents are {got_text} mm."));
                }
            }
        }

        let volume = mesh_volume_mm3(&mesh.vertices_xyz, &mesh.triangles_ijk);
        if !volume.is_finite() || volume <= 0.0 {
            failed(
                out,
                &format!("volume is not positive ({} mm3).", fmt(volume)),
            );
        } else {
            let baseline = expect_volume.abs();
            let relative = if baseline == 0.0 {
                if volume == expect_volume {
                    0.0
                } else {
                    f64::INFINITY
                }
            } else {
                (volume - expect_volume).abs() / baseline
            };
            if relative > volume_rel_tol {
                failed(
                    out,
                    &format!(
                        "volume is {} mm3, expected {} mm3.",
                        fmt(volume),
                        fmt(expect_volume)
                    ),
                );
            } else {
                passed(out, &format!("volume is {} mm3.", fmt(volume)));
            }
        }
    }

    let watertight = is_mesh_watertight(&mesh.vertices_xyz, &mesh.triangles_ijk);
    emit(
        out,
        &format!(
            "INFO: is_watertight is {}.",
            if watertight { "true" } else { "false" }
        ),
    );

    Ok(ok)
}

fn is_known_flag(token: &str) -> bool {
    matches!(
        token,
        "--expect-size"
            | "--expect-volume"
            | "--size-tol"
            | "--volume-rel-tol"
            | "--help"
            | "-h"
    ) || token.starts_with("--expect-size=")
        || token.starts_with("--expect-volume=")
        || token.starts_with("--size-tol=")
        || token.starts_with("--volume-rel-tol=")
}

fn finite_number(name: &str, value: f64, err: &mut dyn Write) -> bool {
    if value.is_finite() {
        true
    } else {
        error(err, &format!("{name} must be a finite number."));
        false
    }
}

fn parse_float_arg(name: &str, raw: &str, err: &mut dyn Write) -> Option<f64> {
    let Ok(val) = raw.parse::<f64>() else {
        error(err, &format!("{name} must be a finite number (got '{raw}')."));
        return None;
    };
    if !finite_number(name, val, err) {
        return None;
    }
    Some(val)
}

fn parse_args(argv: &[String], err: &mut dyn Write) -> Option<CliArgs> {
    let mut paths: Vec<String> = Vec::new();
    let mut expect_size_raw: Option<[String; 3]> = None;
    let mut expect_volume_raw: Option<String> = None;
    let mut size_tol_raw: Option<String> = None;
    let mut volume_rel_tol_raw: Option<String> = None;

    let mut i = 0;
    while i < argv.len() {
        let arg = &argv[i];
        if arg == "--expect-size" {
            if i + 3 >= argv.len()
                || is_known_flag(&argv[i + 1])
                || is_known_flag(&argv[i + 2])
                || is_known_flag(&argv[i + 3])
            {
                error(err, "--expect-size requires 3 values (X Y Z).");
                return None;
            }
            expect_size_raw = Some([
                argv[i + 1].clone(),
                argv[i + 2].clone(),
                argv[i + 3].clone(),
            ]);
            i += 4;
        } else if arg == "--expect-volume" {
            if i + 1 >= argv.len() || is_known_flag(&argv[i + 1]) {
                error(err, "--expect-volume requires 1 value.");
                return None;
            }
            expect_volume_raw = Some(argv[i + 1].clone());
            i += 2;
        } else if let Some(val) = arg.strip_prefix("--expect-volume=") {
            if val.is_empty() {
                error(err, "--expect-volume requires 1 value.");
                return None;
            }
            expect_volume_raw = Some(val.to_string());
            i += 1;
        } else if arg == "--size-tol" {
            if i + 1 >= argv.len() || is_known_flag(&argv[i + 1]) {
                error(err, "--size-tol requires 1 value.");
                return None;
            }
            size_tol_raw = Some(argv[i + 1].clone());
            i += 2;
        } else if let Some(val) = arg.strip_prefix("--size-tol=") {
            if val.is_empty() {
                error(err, "--size-tol requires 1 value.");
                return None;
            }
            size_tol_raw = Some(val.to_string());
            i += 1;
        } else if arg == "--volume-rel-tol" {
            if i + 1 >= argv.len() || is_known_flag(&argv[i + 1]) {
                error(err, "--volume-rel-tol requires 1 value.");
                return None;
            }
            volume_rel_tol_raw = Some(argv[i + 1].clone());
            i += 2;
        } else if let Some(val) = arg.strip_prefix("--volume-rel-tol=") {
            if val.is_empty() {
                error(err, "--volume-rel-tol requires 1 value.");
                return None;
            }
            volume_rel_tol_raw = Some(val.to_string());
            i += 1;
        } else if arg.starts_with('-') {
            error(err, &format!("unrecognized option '{arg}'."));
            return None;
        } else {
            paths.push(arg.clone());
            i += 1;
        }
    }

    if paths.is_empty() {
        error(err, "at least one .stl or .3mf file path is required.");
        return None;
    }
    let Some(size_tokens) = expect_size_raw else {
        error(err, "--expect-size is required.");
        return None;
    };
    let Some(volume_token) = expect_volume_raw else {
        error(err, "--expect-volume is required.");
        return None;
    };

    let sx = parse_float_arg("--expect-size X", &size_tokens[0], err)?;
    let sy = parse_float_arg("--expect-size Y", &size_tokens[1], err)?;
    let sz = parse_float_arg("--expect-size Z", &size_tokens[2], err)?;
    let expect_volume = parse_float_arg("--expect-volume", &volume_token, err)?;

    let size_tol = match size_tol_raw {
        Some(ref raw) => {
            let val = parse_float_arg("--size-tol", raw, err)?;
            if val < 0.0 {
                error(err, "--size-tol must be zero or positive.");
                return None;
            }
            val
        }
        None => DEFAULT_SIZE_TOL,
    };

    let volume_rel_tol = match volume_rel_tol_raw {
        Some(ref raw) => {
            let val = parse_float_arg("--volume-rel-tol", raw, err)?;
            if val < 0.0 {
                error(err, "--volume-rel-tol must be zero or positive.");
                return None;
            }
            val
        }
        None => DEFAULT_VOLUME_REL_TOL,
    };

    Some(CliArgs {
        paths,
        expect_size: [sx, sy, sz],
        expect_volume,
        size_tol,
        volume_rel_tol,
    })
}

pub fn run(argv: &[String], out: &mut dyn Write, err: &mut dyn Write) -> u8 {
    let Some(args) = parse_args(argv, err) else {
        return 2;
    };

    let mut any_fail = false;
    let mut load_error = false;

    for label in &args.paths {
        match check_file(
            label,
            Path::new(label),
            args.expect_size,
            args.expect_volume,
            args.size_tol,
            args.volume_rel_tol,
            out,
        ) {
            Ok(true) => {}
            Ok(false) => {
                any_fail = true;
            }
            Err(exc) => {
                error(err, &exc.to_string());
                load_error = true;
            }
        }
    }

    if load_error {
        2
    } else if any_fail {
        1
    } else {
        0
    }
}

fn main() -> ExitCode {
    let argv: Vec<String> = std::env::args().skip(1).collect();
    let mut stdout = std::io::stdout();
    let mut stderr = std::io::stderr();
    let code = run(&argv, &mut stdout, &mut stderr);
    ExitCode::from(code)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use std::sync::atomic::{AtomicUsize, Ordering};
    use zip::write::SimpleFileOptions;
    use zip::CompressionMethod;

    static NEXT_TEST_ID: AtomicUsize = AtomicUsize::new(0);

    struct TempTestDir {
        path: PathBuf,
    }

    impl TempTestDir {
        fn new(label: &str) -> Self {
            let id = NEXT_TEST_ID.fetch_add(1, Ordering::Relaxed);
            let path = std::env::temp_dir()
                .join(format!("cadcam-rust-check-export-{}-{label}-{id}", std::process::id()));
            let _ = std::fs::remove_dir_all(&path);
            std::fs::create_dir_all(&path).expect("create temp test dir");
            Self { path }
        }
    }

    impl Drop for TempTestDir {
        fn drop(&mut self) {
            let _ = std::fs::remove_dir_all(&self.path);
        }
    }

    fn box_20_vertices_and_triangles() -> (Vec<[f32; 3]>, Vec<[usize; 3]>) {
        let vertices = vec![
            [0.0, 0.0, 0.0],
            [20.0, 0.0, 0.0],
            [20.0, 20.0, 0.0],
            [0.0, 20.0, 0.0],
            [0.0, 0.0, 20.0],
            [20.0, 0.0, 20.0],
            [20.0, 20.0, 20.0],
            [0.0, 20.0, 20.0],
        ];
        let triangles = vec![
            [0, 2, 1],
            [0, 3, 2], // bottom, outward -Z
            [4, 5, 6],
            [4, 6, 7], // top, outward +Z
            [0, 5, 4],
            [0, 1, 5], // y = 0, outward -Y
            [3, 6, 2],
            [3, 7, 6], // y = 20, outward +Y
            [0, 7, 3],
            [0, 4, 7], // x = 0, outward -X
            [1, 2, 6],
            [1, 6, 5], // x = 20, outward +X
        ];
        (vertices, triangles)
    }

    fn write_binary_stl_file(path: &Path, vertices: &[[f32; 3]], triangles: &[[usize; 3]]) {
        let stl_tris: Vec<stl_io::Triangle> = triangles
            .iter()
            .map(|tri| stl_io::Triangle {
                normal: stl_io::Normal::new([0.0, 0.0, 1.0]),
                vertices: [
                    stl_io::Vertex::new(vertices[tri[0]]),
                    stl_io::Vertex::new(vertices[tri[1]]),
                    stl_io::Vertex::new(vertices[tri[2]]),
                ],
            })
            .collect();
        let mut file = File::create(path).expect("create stl");
        stl_io::write_stl(&mut file, stl_tris.iter()).expect("write stl");
    }

    fn write_3mf_archive(path: &Path, entries: &[(&str, &[u8])]) {
        let file = File::create(path).expect("create 3mf");
        let mut zip = zip::ZipWriter::new(file);
        let options = SimpleFileOptions::default().compression_method(CompressionMethod::Stored);
        for &(name, data) in entries {
            zip.start_file(name, options).expect("start zip entry");
            zip.write_all(data).expect("write zip entry");
        }
        zip.finish().expect("finish zip");
    }

    fn model_xml_for_mesh(
        unit_attr: Option<&str>,
        vertices: &[[f32; 3]],
        triangles: &[[usize; 3]],
    ) -> String {
        let unit_part = match unit_attr {
            Some(u) => format!(" unit=\"{u}\""),
            None => String::new(),
        };
        let mut xml = format!(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\
             <model{unit_part} xml:lang=\"en-US\" xmlns=\"http://schemas.microsoft.com/3dmanufacturing/core/2015/02\">\n\
              <resources>\n\
               <object id=\"1\" type=\"model\">\n\
                <mesh>\n\
                 <vertices>\n"
        );
        for v in vertices {
            xml.push_str(&format!(
                "      <vertex x=\"{}\" y=\"{}\" z=\"{}\"/>\n",
                v[0], v[1], v[2]
            ));
        }
        xml.push_str("     </vertices>\n     <triangles>\n");
        for t in triangles {
            xml.push_str(&format!(
                "      <triangle v1=\"{}\" v2=\"{}\" v3=\"{}\"/>\n",
                t[0], t[1], t[2]
            ));
        }
        xml.push_str(
            "     </triangles>\n\
                </mesh>\n\
               </object>\n\
              </resources>\n\
              <build>\n\
               <item objectid=\"1\"/>\n\
              </build>\n\
             </model>\n",
        );
        xml
    }

    fn run_cli(args: &[&str]) -> (u8, String, String) {
        let argv: Vec<String> = args.iter().map(|s| (*s).to_string()).collect();
        let mut out = Vec::new();
        let mut err = Vec::new();
        let code = run(&argv, &mut out, &mut err);
        (
            code,
            String::from_utf8(out).expect("stdout utf8"),
            String::from_utf8(err).expect("stderr utf8"),
        )
    }

    #[test]
    fn good_stl_and_3mf_20mm_box_exit_0_with_expected_lines() {
        let dir = TempTestDir::new("good-box");
        let stl_path = dir.path.join("box.stl");
        let threemf_path = dir.path.join("box.3mf");
        let (v, t) = box_20_vertices_and_triangles();
        write_binary_stl_file(&stl_path, &v, &t);
        let xml = model_xml_for_mesh(Some("millimeter"), &v, &t);
        write_3mf_archive(&threemf_path, &[("3D/3dmodel.model", xml.as_bytes())]);

        let stl_arg = stl_path.to_string_lossy().into_owned();
        let threemf_arg = threemf_path.to_string_lossy().into_owned();
        let (code, stdout, stderr) = run_cli(&[
            &stl_arg,
            &threemf_arg,
            "--expect-size",
            "20",
            "20",
            "20",
            "--expect-volume",
            "8000",
        ]);

        assert_eq!(code, 0, "stderr: {stderr}");
        assert!(stderr.is_empty());
        let expected_stdout = format!(
            "{stl_arg}\n\
             PASS: bbox extents are 20 20 20 mm.\n\
             PASS: volume is 8000 mm3.\n\
             INFO: is_watertight is true.\n\
             {threemf_arg}\n\
             PASS: export unit is millimeter.\n\
             PASS: bbox extents are 20 20 20 mm.\n\
             PASS: volume is 8000 mm3.\n\
             INFO: is_watertight is true.\n"
        );
        assert_eq!(stdout, expected_stdout);
    }

    #[test]
    fn ascii_stl_and_case_insensitive_3mf_path_pass() {
        let dir = TempTestDir::new("ascii-stl");
        let stl_path = dir.path.join("ascii_box.stl");
        let threemf_path = dir.path.join("case.3mf");
        let (v, t) = box_20_vertices_and_triangles();

        let mut ascii = String::from("solid box\n");
        for tri in &t {
            let a = v[tri[0]];
            let b = v[tri[1]];
            let c = v[tri[2]];
            ascii.push_str(&format!(
                "  facet normal 0 0 1\n    outer loop\n      vertex {} {} {}\n      vertex {} {} {}\n      vertex {} {} {}\n    endloop\n  endfacet\n",
                a[0], a[1], a[2], b[0], b[1], b[2], c[0], c[1], c[2]
            ));
        }
        ascii.push_str("endsolid box\n");
        std::fs::write(&stl_path, ascii.as_bytes()).expect("write ascii stl");

        let xml = model_xml_for_mesh(Some("millimeter"), &v, &t);
        write_3mf_archive(&threemf_path, &[("3d/3DModel.MODEL", xml.as_bytes())]);

        let stl_arg = stl_path.to_string_lossy().into_owned();
        let threemf_arg = threemf_path.to_string_lossy().into_owned();
        let (code, stdout, stderr) = run_cli(&[
            &stl_arg,
            &threemf_arg,
            "--expect-size",
            "20",
            "20",
            "20",
            "--expect-volume",
            "8000",
        ]);
        assert_eq!(code, 0, "stderr: {stderr}");
        assert!(!stdout.lines().take(4).any(|l| l.contains("export unit")));
        assert!(stdout.contains("PASS: export unit is millimeter."));
    }

    #[test]
    fn size_outside_tol_exits_1_with_fail_bbox_line() {
        let dir = TempTestDir::new("bad-size");
        let stl_path = dir.path.join("box.stl");
        let (v, t) = box_20_vertices_and_triangles();
        write_binary_stl_file(&stl_path, &v, &t);

        let stl_arg = stl_path.to_string_lossy().into_owned();
        let (code, stdout, stderr) = run_cli(&[
            &stl_arg,
            "--expect-size",
            "20",
            "20",
            "25",
            "--expect-volume",
            "8000",
        ]);
        assert_eq!(code, 1);
        assert!(stderr.is_empty());
        assert!(stdout.contains("FAIL: bbox extents are 20 20 20 mm, expected 20 20 25 mm."));
        assert!(stdout.contains("PASS: volume is 8000 mm3."));
        assert!(stdout.contains("INFO: is_watertight is true."));
    }

    #[test]
    fn threemf_missing_or_wrong_unit_exits_1() {
        let dir = TempTestDir::new("unit-fail");
        let missing_unit_path = dir.path.join("no_unit.3mf");
        let inch_unit_path = dir.path.join("inch_unit.3mf");
        let (v, t) = box_20_vertices_and_triangles();

        let xml_missing = model_xml_for_mesh(None, &v, &t);
        write_3mf_archive(
            &missing_unit_path,
            &[("3D/3dmodel.model", xml_missing.as_bytes())],
        );

        let xml_inch = model_xml_for_mesh(Some("inch"), &v, &t);
        write_3mf_archive(
            &inch_unit_path,
            &[("3D/3dmodel.model", xml_inch.as_bytes())],
        );

        let missing_arg = missing_unit_path.to_string_lossy().into_owned();
        let (code1, stdout1, stderr1) = run_cli(&[
            &missing_arg,
            "--expect-size",
            "20",
            "20",
            "20",
            "--expect-volume",
            "8000",
        ]);
        assert_eq!(code1, 1);
        assert!(stderr1.is_empty());
        assert!(stdout1.contains("FAIL: export unit attribute is missing."));
        assert!(stdout1.contains("PASS: bbox extents are 20 20 20 mm."));
        assert!(stdout1.contains("PASS: volume is 8000 mm3."));

        let inch_arg = inch_unit_path.to_string_lossy().into_owned();
        let (code2, stdout2, stderr2) = run_cli(&[
            &inch_arg,
            "--expect-size",
            "20",
            "20",
            "20",
            "--expect-volume",
            "8000",
        ]);
        assert_eq!(code2, 1);
        assert!(stderr2.is_empty());
        assert!(stdout2.contains("FAIL: export unit is not millimeter."));
    }

    #[test]
    fn zero_triangles_exits_1_and_skips_extents_and_volume() {
        let dir = TempTestDir::new("zero-tris");
        let stl_path = dir.path.join("empty.stl");
        let threemf_path = dir.path.join("empty.3mf");

        write_binary_stl_file(&stl_path, &[], &[]);
        let xml = model_xml_for_mesh(Some("millimeter"), &[], &[]);
        write_3mf_archive(&threemf_path, &[("3D/3dmodel.model", xml.as_bytes())]);

        let stl_arg = stl_path.to_string_lossy().into_owned();
        let threemf_arg = threemf_path.to_string_lossy().into_owned();
        let (code, stdout, stderr) = run_cli(&[
            &stl_arg,
            &threemf_arg,
            "--expect-size",
            "20",
            "20",
            "20",
            "--expect-volume",
            "8000",
        ]);
        assert_eq!(code, 1);
        assert!(stderr.is_empty());
        let expected = format!(
            "{stl_arg}\n\
             FAIL: mesh has no triangles.\n\
             INFO: is_watertight is false.\n\
             {threemf_arg}\n\
             PASS: export unit is millimeter.\n\
             FAIL: mesh has no triangles.\n\
             INFO: is_watertight is false.\n"
        );
        assert_eq!(stdout, expected);
    }

    #[test]
    fn missing_path_bad_zip_and_bad_xml_exit_2_with_stderr_error() {
        let dir = TempTestDir::new("load-errors");
        let missing = dir.path.join("does_not_exist.stl");
        let bad_zip = dir.path.join("bad.3mf");
        let bad_xml = dir.path.join("bad_xml.3mf");
        let no_model = dir.path.join("no_model.3mf");

        std::fs::write(&bad_zip, b"not a zip file").expect("write bad zip");
        write_3mf_archive(
            &bad_xml,
            &[("3D/3dmodel.model", b"<model unit=\"millimeter\"><unclosed")],
        );
        write_3mf_archive(&no_model, &[("3D/3dmodel.model", b"<notmodel/>")]);

        for path in [&missing, &bad_zip, &bad_xml, &no_model] {
            let arg = path.to_string_lossy().into_owned();
            let (code, stdout, stderr) = run_cli(&[
                &arg,
                "--expect-size",
                "20",
                "20",
                "20",
                "--expect-volume",
                "8000",
            ]);
            assert_eq!(code, 2, "expected exit 2 for {arg}, stderr: {stderr}");
            assert!(stdout.is_empty(), "expected empty stdout for {arg}");
            assert!(
                stderr.starts_with("ERROR: "),
                "expected ERROR: on stderr for {arg}, got: {stderr}"
            );
        }
    }

    #[test]
    fn load_error_wins_over_fail_on_another_path() {
        let dir = TempTestDir::new("load-wins");
        let empty_stl = dir.path.join("empty.stl");
        let missing_stl = dir.path.join("missing.stl");
        write_binary_stl_file(&empty_stl, &[], &[]);

        let empty_arg = empty_stl.to_string_lossy().into_owned();
        let missing_arg = missing_stl.to_string_lossy().into_owned();
        let (code, stdout, stderr) = run_cli(&[
            &empty_arg,
            &missing_arg,
            "--expect-size",
            "20",
            "20",
            "20",
            "--expect-volume",
            "8000",
        ]);
        assert_eq!(code, 2);
        assert!(stdout.contains("FAIL: mesh has no triangles."));
        assert!(stderr.starts_with("ERROR: "));
    }

    #[test]
    fn size_and_volume_pass_while_watertight_false_exits_0() {
        let dir = TempTestDir::new("open-watertight-info");
        let stl_path = dir.path.join("flipped_bottom.stl");
        let (v, mut t) = box_20_vertices_and_triangles();
        // Drop one bottom triangle lying on z = 0: tetrahedral contribution with origin is 0,
        // so volume stays 8000 and bbox extents stay 20 20 20, while the shell is open (not watertight).
        t.remove(0);
        write_binary_stl_file(&stl_path, &v, &t);

        let stl_arg = stl_path.to_string_lossy().into_owned();
        let (code, stdout, stderr) = run_cli(&[
            &stl_arg,
            "--expect-size",
            "20",
            "20",
            "20",
            "--expect-volume",
            "8000",
        ]);
        assert_eq!(code, 0, "stderr: {stderr}");
        assert!(stderr.is_empty());
        let expected = format!(
            "{stl_arg}\n\
             PASS: bbox extents are 20 20 20 mm.\n\
             PASS: volume is 8000 mm3.\n\
             INFO: is_watertight is false.\n"
        );
        assert_eq!(stdout, expected);
    }

    #[test]
    fn non_finite_or_negative_tol_or_missing_required_flag_exits_2() {
        let cases: &[&[&str]] = &[
            // Missing --expect-size
            &["box.stl", "--expect-volume", "8000"],
            // Missing --expect-volume
            &["box.stl", "--expect-size", "20", "20", "20"],
            // Bad arity for --expect-size
            &["box.stl", "--expect-size", "20", "20", "--expect-volume", "8000"],
            // Non-finite --expect-size
            &["box.stl", "--expect-size", "20", "nan", "20", "--expect-volume", "8000"],
            // Non-finite --expect-volume
            &["box.stl", "--expect-size", "20", "20", "20", "--expect-volume", "inf"],
            // Negative --size-tol
            &[
                "box.stl",
                "--expect-size",
                "20",
                "20",
                "20",
                "--expect-volume",
                "8000",
                "--size-tol",
                "-0.1",
            ],
            // Non-finite --size-tol
            &[
                "box.stl",
                "--expect-size",
                "20",
                "20",
                "20",
                "--expect-volume",
                "8000",
                "--size-tol",
                "nan",
            ],
            // Negative --volume-rel-tol
            &[
                "box.stl",
                "--expect-size",
                "20",
                "20",
                "20",
                "--expect-volume",
                "8000",
                "--volume-rel-tol",
                "-0.01",
            ],
            // Non-finite --volume-rel-tol
            &[
                "box.stl",
                "--expect-size",
                "20",
                "20",
                "20",
                "--expect-volume",
                "8000",
                "--volume-rel-tol",
                "inf",
            ],
        ];

        for args in cases {
            let (code, stdout, stderr) = run_cli(args);
            assert_eq!(code, 2, "expected exit 2 for {args:?}, got {code}");
            assert!(stdout.is_empty());
            assert!(
                stderr.starts_with("ERROR: "),
                "expected ERROR: on stderr for {args:?}, got: {stderr}"
            );
        }
    }

    #[test]
    fn volume_outside_tol_and_non_positive_volume_exit_1() {
        let dir = TempTestDir::new("volume-fail");
        let stl_path = dir.path.join("box.stl");
        let inside_out_path = dir.path.join("inside_out.stl");
        let (v, t) = box_20_vertices_and_triangles();
        write_binary_stl_file(&stl_path, &v, &t);

        let mut t_rev = t.clone();
        for tri in &mut t_rev {
            tri.swap(1, 2);
        }
        write_binary_stl_file(&inside_out_path, &v, &t_rev);

        let stl_arg = stl_path.to_string_lossy().into_owned();
        let (code1, stdout1, _) = run_cli(&[
            &stl_arg,
            "--expect-size",
            "20",
            "20",
            "20",
            "--expect-volume",
            "9000",
        ]);
        assert_eq!(code1, 1);
        assert!(stdout1.contains("FAIL: volume is 8000 mm3, expected 9000 mm3."));

        let rev_arg = inside_out_path.to_string_lossy().into_owned();
        let (code2, stdout2, _) = run_cli(&[
            &rev_arg,
            "--expect-size",
            "20",
            "20",
            "20",
            "--expect-volume",
            "8000",
        ]);
        assert_eq!(code2, 1);
        assert!(stdout2.contains("FAIL: volume is not positive (-8000 mm3)."));
    }

    #[test]
    fn boundary_equal_to_tolerances_passes() {
        let dir = TempTestDir::new("boundary-tol");
        let stl_path = dir.path.join("box.stl");
        let (v, t) = box_20_vertices_and_triangles();
        write_binary_stl_file(&stl_path, &v, &t);

        let stl_arg = stl_path.to_string_lossy().into_owned();
        // Size diff = 0.5 == --size-tol 0.5; volume rel diff = |8000 - 10000| / 10000 = 0.2 == --volume-rel-tol 0.2
        let (code, stdout, stderr) = run_cli(&[
            &stl_arg,
            "--expect-size",
            "20.5",
            "19.5",
            "20",
            "--expect-volume",
            "10000",
            "--size-tol",
            "0.5",
            "--volume-rel-tol",
            "0.2",
        ]);
        assert_eq!(code, 0, "stderr: {stderr}");
        assert!(stdout.contains("PASS: bbox extents are 20 20 20 mm."));
        assert!(stdout.contains("PASS: volume is 8000 mm3."));
    }

    #[test]
    fn fmt_matches_python_contract() {
        assert_eq!(fmt(0.0), "0");
        assert_eq!(fmt(-0.0), "0");
        assert_eq!(fmt(-0.000_000_1), "0");
        assert_eq!(fmt(20.0), "20");
        assert_eq!(fmt(8000.0), "8000");
        assert_eq!(fmt(12.345000), "12.345");
        assert_eq!(fmt(1.2345678), "1.234568");
        assert_eq!(fmt(f64::NAN), "nan");
        assert_eq!(fmt(f64::INFINITY), "inf");
        assert_eq!(fmt(f64::NEG_INFINITY), "-inf");
    }

    #[test]
    fn exit_codes_and_zero_expected_volume_rule_match_contract() {
        let dir = TempTestDir::new("exit-codes");
        let stl_path = dir.path.join("box.stl");
        let (v, t) = box_20_vertices_and_triangles();
        write_binary_stl_file(&stl_path, &v, &t);
        let stl_arg = stl_path.to_string_lossy().into_owned();

        let (code_ok, _, _) = run_cli(&[
            &stl_arg,
            "--expect-size",
            "20",
            "20",
            "20",
            "--expect-volume",
            "8000",
        ]);
        assert_eq!(code_ok, 0);
        assert_eq!(ExitCode::from(code_ok), ExitCode::from(0));

        // Expected volume 0 with positive actual volume fails with non-finite relative error -> exit 1
        let (code_zero_exp, stdout_zero_exp, _) = run_cli(&[
            &stl_arg,
            "--expect-size",
            "20",
            "20",
            "20",
            "--expect-volume",
            "0",
        ]);
        assert_eq!(code_zero_exp, 1);
        assert_eq!(ExitCode::from(code_zero_exp), ExitCode::from(1));
        assert!(stdout_zero_exp.contains("FAIL: volume is 8000 mm3, expected 0 mm3."));

        let (code_err, _, _) = run_cli(&["--expect-size", "20", "20", "20"]);
        assert_eq!(code_err, 2);
        assert_eq!(ExitCode::from(code_err), ExitCode::from(2));
    }
}
