#include "mesh_view.hpp"

#include <QtGui/qopengl.h>

#include <QMouseEvent>
#include <QWheelEvent>

#include <algorithm>
#include <cmath>

namespace {

const QVector3D kUp(0.0f, 0.0f, 1.0f);
const QVector3D kFixtureCenter(0.5f, 0.5f, 0.5f);
constexpr float kFixtureDistance = 3.2f;
constexpr float kFixtureYaw = -0.78539816f;
constexpr float kFixturePitch = 0.6f;
constexpr float kMinDistance = 0.4f;
constexpr float kMaxDistance = 2000.0f;

bool rayTriangle(const QVector3D& origin, const QVector3D& direction, const QVector3D& v0,
                 const QVector3D& v1, const QVector3D& v2, float& t) {
    constexpr float kEpsilon = 1.0e-6f;
    const QVector3D edge1 = v1 - v0;
    const QVector3D edge2 = v2 - v0;
    const QVector3D p = QVector3D::crossProduct(direction, edge2);
    const float det = QVector3D::dotProduct(edge1, p);
    if (std::fabs(det) < kEpsilon) {
        return false;
    }
    const float inverse = 1.0f / det;
    const QVector3D s = origin - v0;
    const float u = inverse * QVector3D::dotProduct(s, p);
    if (u < 0.0f || u > 1.0f) {
        return false;
    }
    const QVector3D q = QVector3D::crossProduct(s, edge1);
    const float v = inverse * QVector3D::dotProduct(direction, q);
    if (v < 0.0f || u + v > 1.0f) {
        return false;
    }
    t = inverse * QVector3D::dotProduct(edge2, q);
    return t > kEpsilon;
}

}  // namespace

MeshView::MeshView(QWidget* parent) : QOpenGLWidget(parent) {
    setFocusPolicy(Qt::WheelFocus);
}

void MeshView::setMesh(const MeshSolid& mesh) {
    mesh_ = mesh;
    has_selection_ = false;
    update();
}

void MeshView::setGuideLines(const std::vector<std::pair<Vec3, Vec3>>& lines) {
    guides_ = lines;
    if (mesh_.vertices.empty()) {
        frameMesh();
        return;
    }
    update();
}

void MeshView::setSelectionHandler(std::function<void()> handler) {
    selection_handler_ = std::move(handler);
}

bool MeshView::selectedEdge(std::uint32_t& a, std::uint32_t& b) const {
    if (!has_selection_) {
        return false;
    }
    a = selected_a_;
    b = selected_b_;
    return true;
}

void MeshView::resetFixtureCamera() {
    center_ = kFixtureCenter;
    distance_ = kFixtureDistance;
    yaw_ = kFixtureYaw;
    pitch_ = kFixturePitch;
    update();
}

void MeshView::frameMesh() {
    bool any = false;
    double min_x = 0.0;
    double min_y = 0.0;
    double min_z = 0.0;
    double max_x = 0.0;
    double max_y = 0.0;
    double max_z = 0.0;
    const auto include = [&](double x, double y, double z) {
        if (!any) {
            min_x = max_x = x;
            min_y = max_y = y;
            min_z = max_z = z;
            any = true;
            return;
        }
        min_x = std::min(min_x, x);
        min_y = std::min(min_y, y);
        min_z = std::min(min_z, z);
        max_x = std::max(max_x, x);
        max_y = std::max(max_y, y);
        max_z = std::max(max_z, z);
    };
    for (const Vec3& vertex : mesh_.vertices) {
        include(vertex.x, vertex.y, vertex.z);
    }
    for (const auto& segment : guides_) {
        include(segment.first.x, segment.first.y, segment.first.z);
        include(segment.second.x, segment.second.y, segment.second.z);
    }
    if (!any) {
        resetFixtureCamera();
        return;
    }
    center_ = QVector3D(static_cast<float>((min_x + max_x) * 0.5),
                        static_cast<float>((min_y + max_y) * 0.5),
                        static_cast<float>((min_z + max_z) * 0.5));
    const double extent = std::max(max_x - min_x, std::max(max_y - min_y, max_z - min_z));
    distance_ = static_cast<float>(std::max(extent, 1.0) * 2.2);
    if (distance_ < kMinDistance) {
        distance_ = kMinDistance;
    }
    if (distance_ > kMaxDistance) {
        distance_ = kMaxDistance;
    }
    yaw_ = kFixtureYaw;
    pitch_ = kFixturePitch;
    update();
}

void MeshView::initializeGL() {
    glEnable(GL_DEPTH_TEST);
    glClearColor(0.16f, 0.17f, 0.19f, 1.0f);
}

void MeshView::updateProjection() {
    const float aspect = height() <= 0 ? 1.0f : static_cast<float>(width()) / static_cast<float>(height());
    const float near_plane = std::max(0.05f, distance_ * 0.002f);
    const float far_plane = std::max(5000.0f, distance_ * 20.0f);
    projection_.setToIdentity();
    projection_.perspective(40.0f, aspect, near_plane, far_plane);
}

void MeshView::resizeGL(int width, int height) {
    Q_UNUSED(width);
    Q_UNUSED(height);
    updateProjection();
}

QMatrix4x4 MeshView::viewMatrix() const {
    const float cos_pitch = std::cos(pitch_);
    const QVector3D eye = center_ + distance_ * QVector3D(cos_pitch * std::cos(yaw_),
                                                          cos_pitch * std::sin(yaw_),
                                                          std::sin(pitch_));
    QMatrix4x4 view;
    view.lookAt(eye, center_, kUp);
    return view;
}

void MeshView::drawTriangles() const {
    glBegin(GL_TRIANGLES);
    for (const auto& triangle : mesh_.triangles) {
        for (std::uint32_t index : triangle) {
            const Vec3& vertex = mesh_.vertices[index];
            glVertex3d(vertex.x, vertex.y, vertex.z);
        }
    }
    glEnd();
}

void MeshView::drawEdges() const {
    glBegin(GL_LINES);
    for (const auto& triangle : mesh_.triangles) {
        for (int corner = 0; corner < 3; ++corner) {
            const Vec3& from = mesh_.vertices[triangle[static_cast<std::size_t>(corner)]];
            const Vec3& to = mesh_.vertices[triangle[static_cast<std::size_t>((corner + 1) % 3)]];
            glVertex3d(from.x, from.y, from.z);
            glVertex3d(to.x, to.y, to.z);
        }
    }
    glEnd();
}

void MeshView::paintGL() {
    updateProjection();
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    glMatrixMode(GL_PROJECTION);
    glLoadMatrixf(projection_.constData());
    glMatrixMode(GL_MODELVIEW);
    glLoadMatrixf(viewMatrix().constData());

    glEnable(GL_POLYGON_OFFSET_FILL);
    glPolygonOffset(1.0f, 1.0f);
    glEnable(GL_CULL_FACE);
    glCullFace(GL_BACK);
    glColor3f(0.72f, 0.74f, 0.76f);
    drawTriangles();
    glCullFace(GL_FRONT);
    glColor3f(0.78f, 0.42f, 0.28f);
    drawTriangles();
    glDisable(GL_CULL_FACE);
    glDisable(GL_POLYGON_OFFSET_FILL);

    glDepthFunc(GL_LEQUAL);
    glColor3f(0.10f, 0.11f, 0.12f);
    drawEdges();
    glDepthFunc(GL_LESS);

    if (!guides_.empty()) {
        glDisable(GL_DEPTH_TEST);
        glColor3f(0.95f, 0.78f, 0.20f);
        glBegin(GL_LINES);
        for (const auto& segment : guides_) {
            glVertex3d(segment.first.x, segment.first.y, segment.first.z);
            glVertex3d(segment.second.x, segment.second.y, segment.second.z);
        }
        glEnd();
        glEnable(GL_DEPTH_TEST);
    }

    if (has_selection_ && selected_a_ < mesh_.vertices.size() && selected_b_ < mesh_.vertices.size()) {
        const Vec3& a = mesh_.vertices[selected_a_];
        const Vec3& b = mesh_.vertices[selected_b_];
        glDepthFunc(GL_LEQUAL);
        glColor3f(0.98f, 0.86f, 0.15f);
        glLineWidth(3.0f);
        glBegin(GL_LINES);
        glVertex3d(a.x, a.y, a.z);
        glVertex3d(b.x, b.y, b.z);
        glEnd();
        glLineWidth(1.0f);
        glDepthFunc(GL_LESS);
    }
}

void MeshView::panBy(const QPoint& delta) {
    const float cos_pitch = std::cos(pitch_);
    const QVector3D back(cos_pitch * std::cos(yaw_), cos_pitch * std::sin(yaw_), std::sin(pitch_));
    const QVector3D forward = -back;
    QVector3D right = QVector3D::crossProduct(forward, kUp);
    if (right.lengthSquared() < 1.0e-8f) {
        right = QVector3D(1.0f, 0.0f, 0.0f);
    } else {
        right.normalize();
    }
    const QVector3D cam_up = QVector3D::crossProduct(right, forward).normalized();
    const float scale = distance_ * 0.0022f;
    center_ -= right * (static_cast<float>(delta.x()) * scale);
    center_ -= cam_up * (static_cast<float>(delta.y()) * scale);
}

void MeshView::pickAt(const QPoint& pos) {
    has_selection_ = false;
    if (width() > 0 && height() > 0 && !mesh_.triangles.empty()) {
        const QMatrix4x4 mvp = projection_ * viewMatrix();
        bool invertible = false;
        const QMatrix4x4 inverse = mvp.inverted(&invertible);
        if (invertible) {
            const float nx = (2.0f * static_cast<float>(pos.x()) / static_cast<float>(width())) - 1.0f;
            const float ny = 1.0f - (2.0f * static_cast<float>(pos.y()) / static_cast<float>(height()));
            QVector4D near_point = inverse * QVector4D(nx, ny, -1.0f, 1.0f);
            QVector4D far_point = inverse * QVector4D(nx, ny, 1.0f, 1.0f);
            if (near_point.w() != 0.0f && far_point.w() != 0.0f) {
                near_point /= near_point.w();
                far_point /= far_point.w();
                const QVector3D origin(near_point.x(), near_point.y(), near_point.z());
                const QVector3D direction = QVector3D(far_point.x(), far_point.y(), far_point.z()) - origin;
                float best_t = 0.0f;
                int best_triangle = -1;
                for (int index = 0; index < static_cast<int>(mesh_.triangles.size()); ++index) {
                    const auto& triangle = mesh_.triangles[static_cast<std::size_t>(index)];
                    if (triangle[0] >= mesh_.vertices.size() || triangle[1] >= mesh_.vertices.size() ||
                        triangle[2] >= mesh_.vertices.size()) {
                        continue;
                    }
                    const Vec3& va = mesh_.vertices[triangle[0]];
                    const Vec3& vb = mesh_.vertices[triangle[1]];
                    const Vec3& vc = mesh_.vertices[triangle[2]];
                    float t = 0.0f;
                    if (!rayTriangle(origin, direction,
                                     QVector3D(static_cast<float>(va.x), static_cast<float>(va.y),
                                               static_cast<float>(va.z)),
                                     QVector3D(static_cast<float>(vb.x), static_cast<float>(vb.y),
                                               static_cast<float>(vb.z)),
                                     QVector3D(static_cast<float>(vc.x), static_cast<float>(vc.y),
                                               static_cast<float>(vc.z)),
                                     t)) {
                        continue;
                    }
                    if (best_triangle < 0 || t < best_t) {
                        best_t = t;
                        best_triangle = index;
                    }
                }
                if (best_triangle >= 0) {
                    const auto& triangle = mesh_.triangles[static_cast<std::size_t>(best_triangle)];
                    const QVector3D hit = origin + direction * best_t;
                    float best_distance = 0.0f;
                    int best_corner = 0;
                    for (int corner = 0; corner < 3; ++corner) {
                        const Vec3& from = mesh_.vertices[triangle[static_cast<std::size_t>(corner)]];
                        const Vec3& to = mesh_.vertices[triangle[static_cast<std::size_t>((corner + 1) % 3)]];
                        const QVector3D a(static_cast<float>(from.x), static_cast<float>(from.y),
                                          static_cast<float>(from.z));
                        const QVector3D b(static_cast<float>(to.x), static_cast<float>(to.y),
                                          static_cast<float>(to.z));
                        const QVector3D span = b - a;
                        const float span_length = span.lengthSquared();
                        float param = span_length > 0.0f ? QVector3D::dotProduct(hit - a, span) / span_length : 0.0f;
                        if (param < 0.0f) {
                            param = 0.0f;
                        }
                        if (param > 1.0f) {
                            param = 1.0f;
                        }
                        const float distance = (a + span * param - hit).lengthSquared();
                        if (corner == 0 || distance < best_distance) {
                            best_distance = distance;
                            best_corner = corner;
                        }
                    }
                    selected_a_ = triangle[static_cast<std::size_t>(best_corner)];
                    selected_b_ = triangle[static_cast<std::size_t>((best_corner + 1) % 3)];
                    has_selection_ = selected_a_ != selected_b_;
                }
            }
        }
    }
    update();
    if (selection_handler_) {
        selection_handler_();
    }
}

void MeshView::mousePressEvent(QMouseEvent* event) {
    if (event->button() == Qt::LeftButton || event->button() == Qt::RightButton) {
        last_pos_ = event->position().toPoint();
        press_pos_ = last_pos_;
        press_button_ = event->button();
        dragged_ = false;
    }
}

void MeshView::mouseMoveEvent(QMouseEvent* event) {
    const bool left = (event->buttons() & Qt::LeftButton) != 0;
    const bool right = (event->buttons() & Qt::RightButton) != 0;
    if (!left && !right) {
        return;
    }
    const QPoint pos = event->position().toPoint();
    if ((pos - press_pos_).manhattanLength() > 4) {
        dragged_ = true;
    }
    const QPoint delta = pos - last_pos_;
    last_pos_ = pos;
    if (left && !right) {
        yaw_ += static_cast<float>(delta.x()) * 0.01f;
        pitch_ -= static_cast<float>(delta.y()) * 0.01f;
        const float limit = 1.45f;
        if (pitch_ > limit) {
            pitch_ = limit;
        }
        if (pitch_ < -limit) {
            pitch_ = -limit;
        }
    } else if (right) {
        panBy(delta);
    }
    update();
}

void MeshView::mouseReleaseEvent(QMouseEvent* event) {
    if (event->button() == Qt::LeftButton && press_button_ == Qt::LeftButton && !dragged_) {
        pickAt(event->position().toPoint());
    }
}

void MeshView::wheelEvent(QWheelEvent* event) {
    if (event->angleDelta().y() > 0) {
        distance_ *= 0.9f;
    } else if (event->angleDelta().y() < 0) {
        distance_ *= 1.1f;
    }
    if (distance_ < kMinDistance) {
        distance_ = kMinDistance;
    }
    if (distance_ > kMaxDistance) {
        distance_ = kMaxDistance;
    }
    update();
}
