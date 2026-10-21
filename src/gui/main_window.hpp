#pragma once

#include "mesh.hpp"
#include "sketch.hpp"
#include "units.hpp"

#include <QMainWindow>

#include <vector>

class QButtonGroup;
class QDoubleSpinBox;
class QLabel;
class QListWidget;
class QTreeWidget;
class MeshView;

class MainWindow : public QMainWindow {
public:
    explicit MainWindow(QWidget* parent = nullptr);

private:
    struct SpinBinding {
        QDoubleSpinBox* spin = nullptr;
        double* millimeters = nullptr;
    };

    void selectFixture(int id);
    void showFixture(int id);
    void showExportBox();
    void showCurrentBody();
    void showMesh(const MeshSolid& mesh, bool fixture_camera);
    void adoptSolid(const MeshSolid& mesh, const QString& label);
    void pushSpins();
    void refreshMeasure();
    void refreshSketchGuides();
    void setResult(const QString& text);
    void addTimeline(const QString& text);
    QDoubleSpinBox* makeSpin(class QFormLayout* form, const QString& label, double* millimeters);

    void addSketchLine();
    void addSketchRectangle();
    void addSketchCircle();
    void constrainHorizontal();
    void constrainVertical();
    void constrainCoincident();
    void constrainDistance();
    void constrainRadius();
    void finishSketch();
    void makeBox();
    void makeCylinder();
    void extrudeCurrentSketch();
    void unionSolids();
    void cutSolid();
    void filletSelected();
    void exportCurrent();
    void inspectMesh();

    MeshView* view_ = nullptr;
    QLabel* result_ = nullptr;
    QLabel* measure_ = nullptr;
    QListWidget* timeline_ = nullptr;
    QTreeWidget* browser_ = nullptr;
    QButtonGroup* fixtures_ = nullptr;
    UnitLock units_;
    Sketch sketch_;
    MeshSolid body_;
    MeshSolid tool_;
    MeshSolid shown_;
    bool has_body_ = false;
    bool has_tool_ = false;
    bool showing_tool_ = false;
    bool viewing_fixture_ = true;
    int last_line_ = -1;
    int last_circle_ = -1;
    double width_mm_ = 40.0;
    double depth_mm_ = 30.0;
    double height_mm_ = 20.0;
    double radius_mm_ = 5.0;
    double x_mm_ = 0.0;
    double y_mm_ = 0.0;
    double z_mm_ = 0.0;
    double extrude_mm_ = 20.0;
    double fillet_mm_ = 3.0;
    std::vector<SpinBinding> spins_;
};
