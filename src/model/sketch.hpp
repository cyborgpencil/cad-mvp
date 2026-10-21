#pragma once

#include "mesh.hpp"

#include <string>
#include <vector>

// Sketch coordinates are millimeters on the XY plane. Extrude travels +Z.
struct Sketch {
    struct Point {
        double x = 0;
        double y = 0;
    };
    struct Line {
        int a = 0;
        int b = 0;
    };
    struct Circle {
        int center = 0;
        double radius = 0;
    };
    enum class Kind { Horizontal, Vertical, Coincident, Distance, Radius };
    struct Constraint {
        Kind kind = Kind::Horizontal;
        int a = 0;
        int b = 0;
        double value = 0;
    };

    std::vector<Point> points;
    std::vector<Line> lines;
    std::vector<Circle> circles;
    std::vector<Constraint> constraints;

    int add_line(double x0, double y0, double x1, double y1);
    int add_rectangle(double x, double y, double width, double height);
    int add_circle(double cx, double cy, double radius);
    void add_horizontal(int line);
    void add_vertical(int line);
    void add_coincident(int point_a, int point_b);
    void add_distance(int point_a, int point_b, double millimeters);
    void add_radius(int circle, double millimeters);
    void solve();
};

struct ExtrudeResult {
    bool ok = false;
    std::string message;
    MeshSolid mesh;
};

// One direction, +Z. Closed line loops and circles are extruded and unioned.
// Open lines stay in the sketch and are not extruded.
ExtrudeResult extrude_sketch(const Sketch& sketch, double distance_mm);
