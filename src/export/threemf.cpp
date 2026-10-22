#include "threemf.hpp"

#include "units.hpp"

#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace {

std::uint32_t crc32(const std::string& data) {
    std::uint32_t crc = 0xffffffffu;
    for (unsigned char byte : data) {
        crc ^= byte;
        for (int bit = 0; bit < 8; ++bit) {
            const std::uint32_t mask = 0u - (crc & 1u);
            crc = (crc >> 1) ^ (0xedb88320u & mask);
        }
    }
    return ~crc;
}

void append_u16(std::string& out, std::uint16_t value) {
    out.push_back(static_cast<char>(value & 0xffu));
    out.push_back(static_cast<char>((value >> 8) & 0xffu));
}

void append_u32(std::string& out, std::uint32_t value) {
    out.push_back(static_cast<char>(value & 0xffu));
    out.push_back(static_cast<char>((value >> 8) & 0xffu));
    out.push_back(static_cast<char>((value >> 16) & 0xffu));
    out.push_back(static_cast<char>((value >> 24) & 0xffu));
}

struct ZipItem {
    std::string name;
    std::string data;
    std::uint32_t crc = 0;
    std::uint32_t offset = 0;
};

std::string zip_store(std::vector<ZipItem>& items) {
    constexpr std::uint16_t kDosDate = static_cast<std::uint16_t>((46u << 9) | (10u << 5) | 20u);
    std::string local;
    for (ZipItem& item : items) {
        item.crc = crc32(item.data);
        item.offset = static_cast<std::uint32_t>(local.size());
        append_u32(local, 0x04034b50u);
        append_u16(local, 20);
        append_u16(local, 0);
        append_u16(local, 0);
        append_u16(local, 0);
        append_u16(local, kDosDate);
        append_u32(local, item.crc);
        append_u32(local, static_cast<std::uint32_t>(item.data.size()));
        append_u32(local, static_cast<std::uint32_t>(item.data.size()));
        append_u16(local, static_cast<std::uint16_t>(item.name.size()));
        append_u16(local, 0);
        local += item.name;
        local += item.data;
    }

    const std::uint32_t central_offset = static_cast<std::uint32_t>(local.size());
    std::string central;
    for (const ZipItem& item : items) {
        append_u32(central, 0x02014b50u);
        append_u16(central, 20);
        append_u16(central, 20);
        append_u16(central, 0);
        append_u16(central, 0);
        append_u16(central, 0);
        append_u16(central, kDosDate);
        append_u32(central, item.crc);
        append_u32(central, static_cast<std::uint32_t>(item.data.size()));
        append_u32(central, static_cast<std::uint32_t>(item.data.size()));
        append_u16(central, static_cast<std::uint16_t>(item.name.size()));
        append_u16(central, 0);
        append_u16(central, 0);
        append_u16(central, 0);
        append_u16(central, 0);
        append_u32(central, 0);
        append_u32(central, item.offset);
        central += item.name;
    }

    std::string end;
    append_u32(end, 0x06054b50u);
    append_u16(end, 0);
    append_u16(end, 0);
    append_u16(end, static_cast<std::uint16_t>(items.size()));
    append_u16(end, static_cast<std::uint16_t>(items.size()));
    append_u32(end, static_cast<std::uint32_t>(central.size()));
    append_u32(end, central_offset);
    append_u16(end, 0);
    return local + central + end;
}

std::string model_xml(const MeshSolid& mesh) {
    std::ostringstream xml;
    xml << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        << "<model unit=\"" << ExportUnitRecord::threemf_unit
        << "\" xml:lang=\"en-US\" "
        << "xmlns=\"http://schemas.microsoft.com/3dmanufacturing/core/2015/02\">\n"
        << " <resources>\n"
        << "  <object id=\"1\" type=\"model\">\n"
        << "   <mesh>\n"
        << "    <vertices>\n";
    xml.setf(std::ios::fmtflags(0), std::ios::floatfield);
    xml.precision(9);
    for (const Vec3& vertex : mesh.vertices) {
        xml << "     <vertex x=\"" << vertex.x << "\" y=\"" << vertex.y << "\" z=\"" << vertex.z
            << "\"/>\n";
    }
    xml << "    </vertices>\n"
        << "    <triangles>\n";
    for (const auto& triangle : mesh.triangles) {
        xml << "     <triangle v1=\"" << triangle[0] << "\" v2=\"" << triangle[1] << "\" v3=\""
            << triangle[2] << "\"/>\n";
    }
    xml << "    </triangles>\n"
        << "   </mesh>\n"
        << "  </object>\n"
        << " </resources>\n"
        << " <build>\n"
        << "  <item objectid=\"1\"/>\n"
        << " </build>\n"
        << "</model>\n";
    return xml.str();
}

}  // namespace

MeshSolid weld_mesh(const MeshSolid& mesh) {
    constexpr double kQuantumMm = 1e-6;
    MeshSolid out;
    std::map<std::array<long long, 3>, std::uint32_t> index;
    std::vector<std::uint32_t> remap(mesh.vertices.size(), 0);
    for (std::size_t i = 0; i < mesh.vertices.size(); ++i) {
        const Vec3& vertex = mesh.vertices[i];
        const std::array<long long, 3> key = {
            std::llround(vertex.x / kQuantumMm),
            std::llround(vertex.y / kQuantumMm),
            std::llround(vertex.z / kQuantumMm),
        };
        const auto found = index.find(key);
        if (found == index.end()) {
            const auto id = static_cast<std::uint32_t>(out.vertices.size());
            index.emplace(key, id);
            remap[i] = id;
            out.vertices.push_back(vertex);
        } else {
            remap[i] = found->second;
        }
    }

    using Directed = std::pair<std::uint32_t, std::uint32_t>;
    std::map<Directed, int> directed;
    for (const auto& triangle : mesh.triangles) {
        if (triangle[0] >= remap.size() || triangle[1] >= remap.size() ||
            triangle[2] >= remap.size()) {
            continue;
        }
        std::uint32_t a = remap[triangle[0]];
        std::uint32_t b = remap[triangle[1]];
        std::uint32_t c = remap[triangle[2]];
        if (a == b || b == c || a == c) {
            continue;
        }
        if (exact_zero_area(out.vertices[a], out.vertices[b], out.vertices[c])) {
            continue;
        }
        // Same swap as TopAbs_REVERSED faces: (v1, v3, v2) when this winding
        // would traverse an edge that is already used in this direction.
        if (directed[{a, b}] > 0 || directed[{b, c}] > 0 || directed[{c, a}] > 0) {
            const std::uint32_t saved = b;
            b = c;
            c = saved;
            if (a == b || b == c || a == c) {
                continue;
            }
            if (exact_zero_area(out.vertices[a], out.vertices[b], out.vertices[c])) {
                continue;
            }
        }
        out.triangles.push_back({a, b, c});
        directed[{a, b}] += 1;
        directed[{b, c}] += 1;
        directed[{c, a}] += 1;
    }
    double sum = 0.0;
    for (const auto& triangle : out.triangles) {
        const Vec3& p = out.vertices[triangle[0]];
        const Vec3& q = out.vertices[triangle[1]];
        const Vec3& r = out.vertices[triangle[2]];
        const double cx = q.y * r.z - q.z * r.y;
        const double cy = q.z * r.x - q.x * r.z;
        const double cz = q.x * r.y - q.y * r.x;
        sum += p.x * cx + p.y * cy + p.z * cz;
    }
    if (sum < 0.0) {
        for (auto& triangle : out.triangles) {
            const auto saved = triangle[1];
            triangle[1] = triangle[2];
            triangle[2] = saved;
        }
    }
    return out;
}

bool write_3mf(const std::filesystem::path& path, const MeshSolid& mesh) {
    const MeshSolid welded = weld_mesh(mesh);
    for (const auto& triangle : welded.triangles) {
        if (triangle[0] >= welded.vertices.size() || triangle[1] >= welded.vertices.size() ||
            triangle[2] >= welded.vertices.size()) {
            return false;
        }
    }

    const std::string types =
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">\n"
        " <Default Extension=\"rels\" "
        "ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>\n"
        " <Default Extension=\"model\" "
        "ContentType=\"application/vnd.ms-package.3dmanufacturing-3dmodel+xml\"/>\n"
        "</Types>\n";
    const std::string rels =
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<Relationships "
        "xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">\n"
        " <Relationship Target=\"/3D/3dmodel.model\" Id=\"rel0\" "
        "Type=\"http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel\"/>\n"
        "</Relationships>\n";

    std::vector<ZipItem> items = {
        {"[Content_Types].xml", types, 0, 0},
        {"_rels/.rels", rels, 0, 0},
        {"3D/3dmodel.model", model_xml(welded), 0, 0},
    };
    const std::string package = zip_store(items);
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        return false;
    }
    out.write(package.data(), static_cast<std::streamsize>(package.size()));
    return out.good();
}
