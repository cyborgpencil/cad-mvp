#pragma once

#include "mesh.hpp"

#include <QOpenGLWidget>
#include <QMatrix4x4>
#include <QPoint>
#include <QVector3D>

#include <cstdint>
#include <functional>
#include <utility>
#include <vector>

class QMouseEvent;
class QWheelEvent;

// Z-up orbit view of one triangle mesh. Front faces and back faces use different colors.
class MeshView : public QOpenGLWidget {
public:
    explicit MeshView(QWidget* parent = nullptr);

    void setMesh(const MeshSolid& mesh);
    void setGuideLines(const std::vector<std::pair<Vec3, Vec3>>& lines);
    void resetFixtureCamera();
    void frameMesh();
    void setSelectionHandler(std::function<void()> handler);
    bool selectedEdge(std::uint32_t& a, std::uint32_t& b) const;

protected:
    void initializeGL() override;
    void resizeGL(int width, int height) override;
    void paintGL() override;
    void mousePressEvent(QMouseEvent* event) override;
    void mouseMoveEvent(QMouseEvent* event) override;
    void mouseReleaseEvent(QMouseEvent* event) override;
    void wheelEvent(QWheelEvent* event) override;

private:
    QMatrix4x4 viewMatrix() const;
    void updateProjection();
    void drawTriangles() const;
    void drawEdges() const;
    void panBy(const QPoint& delta);
    void pickAt(const QPoint& pos);

    MeshSolid mesh_;
    std::vector<std::pair<Vec3, Vec3>> guides_;
    QMatrix4x4 projection_;
    QVector3D center_{0.5f, 0.5f, 0.5f};
    // Front-top-right of the unit box: +X, -Y, +Z.
    float yaw_ = -0.78539816f;
    float pitch_ = 0.6f;
    float distance_ = 3.2f;
    QPoint last_pos_;
    QPoint press_pos_;
    Qt::MouseButton press_button_ = Qt::NoButton;
    bool dragged_ = false;
    bool has_selection_ = false;
    std::uint32_t selected_a_ = 0;
    std::uint32_t selected_b_ = 0;
    std::function<void()> selection_handler_;
};
