#include "stl.hpp"

#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>

namespace {

void write_u16(std::ostream& out, std::uint16_t value) {
    const unsigned char bytes[2] = {
        static_cast<unsigned char>(value & 0xffu),
        static_cast<unsigned char>((value >> 8) & 0xffu),
    };
    out.write(reinterpret_cast<const char*>(bytes), 2);
}

void write_u32(std::ostream& out, std::uint32_t value) {
    const unsigned char bytes[4] = {
        static_cast<unsigned char>(value & 0xffu),
        static_cast<unsigned char>((value >> 8) & 0xffu),
        static_cast<unsigned char>((value >> 16) & 0xffu),
        static_cast<unsigned char>((value >> 24) & 0xffu),
    };
    out.write(reinterpret_cast<const char*>(bytes), 4);
}

void write_f32(std::ostream& out, float value) {
    static_assert(sizeof(float) == 4, "binary STL needs 32-bit float");
    unsigned char bytes[4];
    std::memcpy(bytes, &value, 4);
    out.write(reinterpret_cast<const char*>(bytes), 4);
}

bool read_exact(std::istream& in, void* dest, std::streamsize size) {
    in.read(static_cast<char*>(dest), size);
    return in.good() && in.gcount() == size;
}

std::uint32_t read_u32(const unsigned char* bytes) {
    return static_cast<std::uint32_t>(bytes[0]) |
           (static_cast<std::uint32_t>(bytes[1]) << 8) |
           (static_cast<std::uint32_t>(bytes[2]) << 16) |
           (static_cast<std::uint32_t>(bytes[3]) << 24);
}

float read_f32(const unsigned char* bytes) {
    float value = 0.0f;
    std::memcpy(&value, bytes, 4);
    return value;
}

void face_normal(const Vec3& a, const Vec3& b, const Vec3& c, float out[3]) {
    const double ux = b.x - a.x;
    const double uy = b.y - a.y;
    const double uz = b.z - a.z;
    const double vx = c.x - a.x;
    const double vy = c.y - a.y;
    const double vz = c.z - a.z;
    double nx = uy * vz - uz * vy;
    double ny = uz * vx - ux * vz;
    double nz = ux * vy - uy * vx;
    const double length = std::sqrt(nx * nx + ny * ny + nz * nz);
    if (length == 0.0) {
        out[0] = 0.0f;
        out[1] = 0.0f;
        out[2] = 0.0f;
        return;
    }
    out[0] = static_cast<float>(nx / length);
    out[1] = static_cast<float>(ny / length);
    out[2] = static_cast<float>(nz / length);
}

bool index_ok(const MeshSolid& mesh, std::uint32_t index) {
    return index < mesh.vertices.size();
}

}  // namespace

bool write_binary_stl(const std::filesystem::path& path, const MeshSolid& mesh) {
    for (const auto& triangle : mesh.triangles) {
        if (!index_ok(mesh, triangle[0]) || !index_ok(mesh, triangle[1]) ||
            !index_ok(mesh, triangle[2])) {
            return false;
        }
    }

    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        return false;
    }

    std::array<char, 80> header{};
    const char text[] = "cadcam-mvp binary stl, coordinates in millimeters";
    std::memcpy(header.data(), text, sizeof(text) - 1);
    out.write(header.data(), static_cast<std::streamsize>(header.size()));
    write_u32(out, static_cast<std::uint32_t>(mesh.triangles.size()));

    for (const auto& triangle : mesh.triangles) {
        const Vec3& a = mesh.vertices[triangle[0]];
        const Vec3& b = mesh.vertices[triangle[1]];
        const Vec3& c = mesh.vertices[triangle[2]];
        float normal[3];
        face_normal(a, b, c, normal);
        write_f32(out, normal[0]);
        write_f32(out, normal[1]);
        write_f32(out, normal[2]);
        const Vec3* corners[3] = {&a, &b, &c};
        for (const Vec3* corner : corners) {
            write_f32(out, static_cast<float>(corner->x));
            write_f32(out, static_cast<float>(corner->y));
            write_f32(out, static_cast<float>(corner->z));
        }
        write_u16(out, 0);
    }
    return out.good();
}

bool read_binary_stl(const std::filesystem::path& path, MeshSolid& mesh) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        return false;
    }
    in.seekg(0, std::ios::end);
    const std::streamoff file_size = in.tellg();
    in.seekg(0, std::ios::beg);
    if (file_size < 84) {
        return false;
    }

    unsigned char header[80];
    if (!read_exact(in, header, 80)) {
        return false;
    }
    unsigned char count_bytes[4];
    if (!read_exact(in, count_bytes, 4)) {
        return false;
    }
    const std::uint32_t count = read_u32(count_bytes);
    const unsigned long long expected =
        84ull + static_cast<unsigned long long>(count) * 50ull;
    if (expected != static_cast<unsigned long long>(file_size) || count > 1000000u) {
        return false;
    }

    MeshSolid loaded;
    loaded.vertices.reserve(static_cast<std::size_t>(count) * 3u);
    loaded.triangles.reserve(count);
    for (std::uint32_t triangle = 0; triangle < count; ++triangle) {
        unsigned char record[50];
        if (!read_exact(in, record, 50)) {
            return false;
        }
        const std::uint32_t base = static_cast<std::uint32_t>(loaded.vertices.size());
        for (int corner = 0; corner < 3; ++corner) {
            const unsigned char* xyz = record + 12 + corner * 12;
            loaded.vertices.push_back(
                {read_f32(xyz), read_f32(xyz + 4), read_f32(xyz + 8)});
        }
        loaded.triangles.push_back({base, base + 1u, base + 2u});
    }
    mesh = std::move(loaded);
    return true;
}
