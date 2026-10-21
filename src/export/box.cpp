#include "box.hpp"

MeshSolid box_mm(double width_mm, double depth_mm, double height_mm) {
    if (!(width_mm > 0.0) || !(depth_mm > 0.0) || !(height_mm > 0.0)) {
        return {};
    }
    MeshSolid mesh;
    mesh.vertices = {
        {0, 0, 0},
        {width_mm, 0, 0},
        {width_mm, depth_mm, 0},
        {0, depth_mm, 0},
        {0, 0, height_mm},
        {width_mm, 0, height_mm},
        {width_mm, depth_mm, height_mm},
        {0, depth_mm, height_mm},
    };
    mesh.triangles = {
        {0, 2, 1}, {0, 3, 2},
        {4, 5, 6}, {4, 6, 7},
        {0, 5, 4}, {0, 1, 5},
        {3, 6, 2}, {3, 7, 6},
        {0, 7, 3}, {0, 4, 7},
        {1, 2, 6}, {1, 6, 5},
    };
    return mesh;
}
