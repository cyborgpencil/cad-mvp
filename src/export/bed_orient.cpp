#include "bed_orient.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <vector>

namespace {

constexpr double kNormalDot = 0.999;
constexpr double kPlaneMm = 0.05;

double det3(const int m[9]) {
    return static_cast<double>(m[0] * (m[4] * m[8] - m[5] * m[7]) -
                               m[1] * (m[3] * m[8] - m[5] * m[6]) +
                               m[2] * (m[3] * m[7] - m[4] * m[6]));
}

struct Mat {
    int m[9];
};

std::vector<Mat> axis_rotations() {
    const int perms[6][3] = {
        {0, 1, 2}, {0, 2, 1}, {1, 0, 2}, {1, 2, 0}, {2, 0, 1}, {2, 1, 0},
    };
    const int sign_order[2] = {1, -1};
    std::vector<Mat> out;
    out.reserve(24);
    for (int sa = 0; sa < 2; ++sa) {
        for (int sb = 0; sb < 2; ++sb) {
            for (int sc = 0; sc < 2; ++sc) {
                const int s[3] = {sign_order[sa], sign_order[sb], sign_order[sc]};
                for (const auto& perm : perms) {
                    Mat mat{};
                    for (int row = 0; row < 3; ++row) {
                        mat.m[row * 3 + perm[row]] = s[row];
                    }
                    if (det3(mat.m) == 1.0) {
                        out.push_back(mat);
                    }
                }
            }
        }
    }
    return out;
}

struct Face {
    double nx = 0;
    double ny = 0;
    double nz = 0;
    double offset = 0;
    double area = 0;
    double zmin = 0;
    double zmax = 0;
};

struct TriGeom {
    double nx = 0;
    double ny = 0;
    double nz = 0;
    double offset = 0;
    double area = 0;
    double zmin = 0;
    double zmax = 0;
    bool ok = false;
};

TriGeom tri_geom(const Vec3& a, const Vec3& b, const Vec3& c) {
    TriGeom geom;
    const double ux = b.x - a.x;
    const double uy = b.y - a.y;
    const double uz = b.z - a.z;
    const double vx = c.x - a.x;
    const double vy = c.y - a.y;
    const double vz = c.z - a.z;
    const double cx = uy * vz - uz * vy;
    const double cy = uz * vx - ux * vz;
    const double cz = ux * vy - uy * vx;
    const double len = std::sqrt(cx * cx + cy * cy + cz * cz);
    if (!(len > 1e-12)) {
        return geom;
    }
    geom.ok = true;
    geom.nx = cx / len;
    geom.ny = cy / len;
    geom.nz = cz / len;
    geom.area = len * 0.5;
    geom.offset = geom.nx * a.x + geom.ny * a.y + geom.nz * a.z;
    geom.zmin = std::min(a.z, std::min(b.z, c.z));
    geom.zmax = std::max(a.z, std::max(b.z, c.z));
    return geom;
}

struct Score {
    double height = 0;
    double bed = 0;
    double floating = 0;
    double dx = 0;
    int index = 0;
    double z_shift = 0;
};

Score score_mesh(const std::vector<Vec3>& vertices,
                 const std::vector<std::array<std::uint32_t, 3>>& triangles,
                 int index,
                 double z_shift) {
    Score score;
    score.index = index;
    score.z_shift = z_shift;
    if (vertices.empty()) {
        return score;
    }
    double xmin = vertices[0].x;
    double xmax = xmin;
    double zmin = vertices[0].z;
    double zmax = zmin;
    for (const Vec3& vertex : vertices) {
        xmin = std::min(xmin, vertex.x);
        xmax = std::max(xmax, vertex.x);
        zmin = std::min(zmin, vertex.z);
        zmax = std::max(zmax, vertex.z);
    }
    score.height = zmax - zmin;
    score.dx = xmax - xmin;

    std::vector<Face> faces;
    for (const auto& triangle : triangles) {
        if (triangle[0] >= vertices.size() || triangle[1] >= vertices.size() ||
            triangle[2] >= vertices.size()) {
            continue;
        }
        const TriGeom geom =
            tri_geom(vertices[triangle[0]], vertices[triangle[1]], vertices[triangle[2]]);
        if (!geom.ok) {
            continue;
        }
        Face* found = nullptr;
        for (Face& face : faces) {
            const double dot = face.nx * geom.nx + face.ny * geom.ny + face.nz * geom.nz;
            if (dot >= kNormalDot && std::abs(face.offset - geom.offset) <= kPlaneMm) {
                found = &face;
                break;
            }
        }
        if (found == nullptr) {
            Face face;
            face.nx = geom.nx;
            face.ny = geom.ny;
            face.nz = geom.nz;
            face.offset = geom.offset;
            face.area = geom.area;
            face.zmin = geom.zmin;
            face.zmax = geom.zmax;
            faces.push_back(face);
            found = &faces.back();
        } else {
            found->area += geom.area;
            found->zmin = std::min(found->zmin, geom.zmin);
            found->zmax = std::max(found->zmax, geom.zmax);
        }
    }
    for (const Face& face : faces) {
        const bool down = face.nz <= -kNormalDot;
        const bool on_bed = face.zmax <= kPlaneMm && face.zmin <= 1e-4;
        if (down && on_bed && face.area > score.bed) {
            score.bed = face.area;
        }
        if (down && face.zmin > kPlaneMm) {
            score.floating += face.area;
        }
    }
    return score;
}

bool better_pose(const Score& candidate, const Score& current) {
    if (std::abs(candidate.height - current.height) > kPlaneMm) {
        return candidate.height < current.height;
    }
    if (std::abs(candidate.bed - current.bed) > 1e-3) {
        return candidate.bed > current.bed;
    }
    if (std::abs(candidate.floating - current.floating) > 1e-3) {
        return candidate.floating < current.floating;
    }
    if (std::abs(candidate.dx - current.dx) > kPlaneMm) {
        return candidate.dx > current.dx;
    }
    return candidate.index < current.index;
}

Vec3 mul_row(const int m[9], const Vec3& p) {
    return {
        m[0] * p.x + m[1] * p.y + m[2] * p.z,
        m[3] * p.x + m[4] * p.y + m[5] * p.z,
        m[6] * p.x + m[7] * p.y + m[8] * p.z,
    };
}

}  // namespace

MeshSolid lay_single_body_on_bed(const MeshSolid& mesh) {
    if (mesh.vertices.empty() || mesh.triangles.empty()) {
        return mesh;
    }
    const std::vector<Mat> rotations = axis_rotations();
    Score best;
    std::vector<Vec3> best_vertices;
    bool have = false;
    for (int index = 0; index < static_cast<int>(rotations.size()); ++index) {
        const int* m = rotations[static_cast<std::size_t>(index)].m;
        std::vector<Vec3> posed;
        posed.reserve(mesh.vertices.size());
        double zmin = 0;
        bool any = false;
        for (const Vec3& vertex : mesh.vertices) {
            Vec3 next = mul_row(m, vertex);
            if (!any || next.z < zmin) {
                zmin = next.z;
            }
            any = true;
            posed.push_back(next);
        }
        const double shift = any ? zmin : 0;
        if (std::abs(shift) > 1e-12) {
            for (Vec3& vertex : posed) {
                vertex.z -= shift;
            }
        }
        const Score score = score_mesh(posed, mesh.triangles, index, shift);
        if (!have || better_pose(score, best)) {
            best = score;
            best_vertices = std::move(posed);
            have = true;
        }
    }
    if (!have || (best.index == 0 && std::abs(best.z_shift) <= 1e-12)) {
        return mesh;
    }
    MeshSolid out;
    out.vertices = std::move(best_vertices);
    out.triangles = mesh.triangles;
    return out;
}
