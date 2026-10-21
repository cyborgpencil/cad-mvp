#include "part.hpp"

#include "box.hpp"
#include "shapes.hpp"
#include "sketch.hpp"

MeshSolid build_demo_part() {
    Sketch sketch;
    sketch.add_rectangle(0.0, 0.0, 40.0, 30.0);
    sketch.solve();
    const ExtrudeResult extruded = extrude_sketch(sketch, 20.0);
    const FilletResult filleted = fillet_box_edge(extruded.mesh, 4, 5, 3.0);
    const MeshSolid cutter = translate_mesh(box_mm(8.0, 8.0, 6.0), 16.0, 12.0, 7.0);
    const CutResult cut = mesh_cut(filleted.mesh, cutter);
    return cut.ok ? cut.mesh : filleted.mesh;
}
