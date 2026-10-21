#pragma once

#include "mesh.hpp"

#include <cstdint>
#include <string>

MeshSolid translate_mesh(const MeshSolid& mesh, double dx, double dy, double dz);
MeshSolid flip_winding(const MeshSolid& mesh);
MeshSolid mesh_append(const MeshSolid& a, const MeshSolid& b);

// Cylinder axis is +Z. Radius and height are millimeters. segments >= 3.
MeshSolid cylinder_mm(double cx, double cy, double radius, double height, int segments);

// Closed meshes. Overlapping axis-aligned boxes become one rectilinear shell.
MeshSolid mesh_union(const MeshSolid& a, const MeshSolid& b);

struct CutResult {
    bool ok = false;
    std::string message;
    MeshSolid mesh;
};

// Removes the cutter. Two boxes use a cell difference. A cutter strictly inside
// another closed mesh becomes an interior void shell.
CutResult mesh_cut(const MeshSolid& subject, const MeshSolid& cutter);

struct FilletResult {
    bool ok = false;
    std::string message;
    MeshSolid mesh;
};

// Constant-radius fillet on one axis-aligned edge of a box mesh.
FilletResult fillet_box_edge(const MeshSolid& box, std::uint32_t vertex_a, std::uint32_t vertex_b,
                             double radius_mm);
