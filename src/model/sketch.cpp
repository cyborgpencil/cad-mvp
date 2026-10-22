#include "sketch.hpp"

#include "shapes.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <map>
#include <utility>

namespace {

double hypot2(double x, double y) {
    return std::sqrt(x * x + y * y);
}

MeshSolid extrude_loop(const std::vector<Sketch::Point>& loop, double distance) {
    const int count = static_cast<int>(loop.size());
    MeshSolid mesh;
    mesh.vertices.reserve(static_cast<std::size_t>(count) * 2u);
    for (const Sketch::Point& point : loop) {
        mesh.vertices.push_back({point.x, point.y, 0.0});
    }
    for (const Sketch::Point& point : loop) {
        mesh.vertices.push_back({point.x, point.y, distance});
    }
    const auto top = static_cast<std::uint32_t>(count);
    for (int i = 1; i + 1 < count; ++i) {
        mesh.triangles.push_back({0u, static_cast<std::uint32_t>(i + 1), static_cast<std::uint32_t>(i)});
        mesh.triangles.push_back({top, top + static_cast<std::uint32_t>(i), top + static_cast<std::uint32_t>(i + 1)});
    }
    for (int i = 0; i < count; ++i) {
        const auto next = static_cast<std::uint32_t>((i + 1) % count);
        const auto current = static_cast<std::uint32_t>(i);
        mesh.triangles.push_back({current, next, top + next});
        mesh.triangles.push_back({current, top + next, top + current});
    }
    return mesh;
}

bool closed_loop(const Sketch& sketch, std::vector<Sketch::Point>& loop) {
    std::map<int, std::vector<int>> neighbors;
    for (const Sketch::Line& line : sketch.lines) {
        neighbors[line.a].push_back(line.b);
        neighbors[line.b].push_back(line.a);
    }
    int start = -1;
    for (const auto& entry : neighbors) {
        if (entry.second.size() == 2) {
            start = entry.first;
            break;
        }
    }
    if (start < 0) {
        return false;
    }
    std::vector<int> order;
    int previous = -1;
    int current = start;
    do {
        order.push_back(current);
        const std::vector<int>& nexts = neighbors[current];
        if (nexts.size() != 2) {
            return false;
        }
        const int next = nexts[0] == previous ? nexts[1] : nexts[0];
        previous = current;
        current = next;
        if (order.size() > sketch.points.size()) {
            return false;
        }
    } while (current != start);
    if (order.size() < 3) {
        return false;
    }
    loop.clear();
    double area = 0.0;
    for (std::size_t i = 0; i < order.size(); ++i) {
        const Sketch::Point& a = sketch.points[static_cast<std::size_t>(order[i])];
        const Sketch::Point& b =
            sketch.points[static_cast<std::size_t>(order[(i + 1) % order.size()])];
        area += a.x * b.y - b.x * a.y;
        loop.push_back(a);
    }
    if (area < 0.0) {
        std::reverse(loop.begin(), loop.end());
    }
    return true;
}

}  // namespace

int Sketch::add_line(double x0, double y0, double x1, double y1) {
    const int a = static_cast<int>(points.size());
    points.push_back({x0, y0});
    const int b = static_cast<int>(points.size());
    points.push_back({x1, y1});
    const int line = static_cast<int>(lines.size());
    lines.push_back({a, b});
    return line;
}

int Sketch::add_rectangle(double x, double y, double width, double height) {
    const int first = static_cast<int>(lines.size());
    const int p0 = static_cast<int>(points.size());
    points.push_back({x, y});
    points.push_back({x + width, y});
    points.push_back({x + width, y + height});
    points.push_back({x, y + height});
    lines.push_back({p0, p0 + 1});
    lines.push_back({p0 + 1, p0 + 2});
    lines.push_back({p0 + 2, p0 + 3});
    lines.push_back({p0 + 3, p0});
    add_horizontal(first);
    add_vertical(first + 1);
    add_horizontal(first + 2);
    add_vertical(first + 3);
    add_distance(p0, p0 + 1, width);
    add_distance(p0 + 1, p0 + 2, height);
    return first;
}

int Sketch::add_circle(double cx, double cy, double radius) {
    const int center = static_cast<int>(points.size());
    points.push_back({cx, cy});
    const int circle = static_cast<int>(circles.size());
    circles.push_back({center, radius});
    return circle;
}

void Sketch::add_horizontal(int line) {
    constraints.push_back({Kind::Horizontal, line, 0, 0});
}

void Sketch::add_vertical(int line) {
    constraints.push_back({Kind::Vertical, line, 0, 0});
}

void Sketch::add_coincident(int point_a, int point_b) {
    constraints.push_back({Kind::Coincident, point_a, point_b, 0});
}

void Sketch::add_distance(int point_a, int point_b, double millimeters) {
    constraints.push_back({Kind::Distance, point_a, point_b, millimeters});
}

void Sketch::add_radius(int circle, double millimeters) {
    constraints.push_back({Kind::Radius, circle, 0, millimeters});
}

void Sketch::solve() {
    for (int iteration = 0; iteration < 40; ++iteration) {
        for (const Constraint& constraint : constraints) {
            if (constraint.kind == Kind::Radius) {
                if (constraint.a >= 0 && constraint.a < static_cast<int>(circles.size())) {
                    circles[static_cast<std::size_t>(constraint.a)].radius = constraint.value;
                }
                continue;
            }
            if (constraint.kind == Kind::Horizontal || constraint.kind == Kind::Vertical) {
                if (constraint.a < 0 || constraint.a >= static_cast<int>(lines.size())) {
                    continue;
                }
                const Line& line = lines[static_cast<std::size_t>(constraint.a)];
                Point& a = points[static_cast<std::size_t>(line.a)];
                Point& b = points[static_cast<std::size_t>(line.b)];
                if (constraint.kind == Kind::Horizontal) {
                    const double y = (a.y + b.y) * 0.5;
                    a.y = y;
                    b.y = y;
                } else {
                    const double x = (a.x + b.x) * 0.5;
                    a.x = x;
                    b.x = x;
                }
                continue;
            }
            if (constraint.a < 0 || constraint.b < 0 ||
                constraint.a >= static_cast<int>(points.size()) ||
                constraint.b >= static_cast<int>(points.size())) {
                continue;
            }
            Point& a = points[static_cast<std::size_t>(constraint.a)];
            Point& b = points[static_cast<std::size_t>(constraint.b)];
            if (constraint.kind == Kind::Coincident) {
                const double x = (a.x + b.x) * 0.5;
                const double y = (a.y + b.y) * 0.5;
                a.x = b.x = x;
                a.y = b.y = y;
                continue;
            }
            double dx = b.x - a.x;
            double dy = b.y - a.y;
            const double length = hypot2(dx, dy);
            if (length < 1e-12) {
                b.x = a.x + constraint.value;
                b.y = a.y;
            } else {
                b.x = a.x + dx * (constraint.value / length);
                b.y = a.y + dy * (constraint.value / length);
            }
        }
    }
}

ExtrudeResult extrude_sketch(const Sketch& sketch, double distance_mm) {
    ExtrudeResult result;
    if (!(distance_mm > 0.0)) {
        result.message = "cannot extrude: distance must be positive.";
        return result;
    }
    std::vector<Sketch::Point> loop;
    const bool has_loop = closed_loop(sketch, loop);
    if (!has_loop && sketch.circles.empty()) {
        result.message = "cannot extrude: the sketch has no closed profile.";
        return result;
    }
    bool any = false;
    if (has_loop) {
        result.mesh = extrude_loop(loop, distance_mm);
        any = true;
    }
    for (const Sketch::Circle& circle : sketch.circles) {
        if (!(circle.radius > 0.0) || circle.center < 0 ||
            circle.center >= static_cast<int>(sketch.points.size())) {
            continue;
        }
        const Sketch::Point& center = sketch.points[static_cast<std::size_t>(circle.center)];
        const MeshSolid disk = cylinder_mm(center.x, center.y, circle.radius, distance_mm, 24);
        result.mesh = any ? mesh_union(result.mesh, disk) : disk;
        any = true;
    }
    if (!any || result.mesh.triangles.empty()) {
        result.message = "cannot extrude: the profile produced no triangles.";
        result.mesh = {};
        return result;
    }
    result.ok = true;
    result.message = "extrude";
    return result;
}
