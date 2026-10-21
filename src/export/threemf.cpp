#include "threemf.hpp"

#include "units.hpp"

#include <cstdint>
#include <fstream>
#include <sstream>
#include <string>
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

bool write_3mf(const std::filesystem::path& path, const MeshSolid& mesh) {
    for (const auto& triangle : mesh.triangles) {
        if (triangle[0] >= mesh.vertices.size() || triangle[1] >= mesh.vertices.size() ||
            triangle[2] >= mesh.vertices.size()) {
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
        {"3D/3dmodel.model", model_xml(mesh), 0, 0},
    };
    const std::string package = zip_store(items);
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        return false;
    }
    out.write(package.data(), static_cast<std::streamsize>(package.size()));
    return out.good();
}
