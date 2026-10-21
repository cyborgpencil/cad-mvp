#include "main_window.hpp"

#include "box.hpp"
#include "export_files.hpp"
#include "fixtures.hpp"
#include "mesh_view.hpp"
#include "repair.hpp"
#include "shapes.hpp"
#include "stl.hpp"
#include "watertight.hpp"

#include <cmath>
#include <cstdint>
#include <filesystem>
#include <utility>

#include <QButtonGroup>
#include <QCoreApplication>
#include <QDoubleSpinBox>
#include <QFormLayout>
#include <QGuiApplication>
#include <QHBoxLayout>
#include <QLabel>
#include <QListWidget>
#include <QPushButton>
#include <QRadioButton>
#include <QScreen>
#include <QScrollArea>
#include <QStackedWidget>
#include <QTreeWidget>
#include <QVBoxLayout>
#include <QWidget>

namespace {

QPushButton* toolButton(QWidget* parent, QLayout* layout, const QString& text) {
    auto* button = new QPushButton(text, parent);
    button->setAccessibleName(text);
    layout->addWidget(button);
    return button;
}

}  // namespace

MainWindow::MainWindow(QWidget* parent) : QMainWindow(parent) {
    auto* central = new QWidget(this);
    auto* layout = new QVBoxLayout(central);

    auto* tab_row = new QHBoxLayout();
    auto* tabs = new QButtonGroup(this);
    tabs->setExclusive(true);
    auto* stack = new QStackedWidget(central);
    const char* tab_names[] = {"Sketch", "Solid", "Inspect"};
    for (int id = 0; id < 3; ++id) {
        auto* button = new QPushButton(tab_names[id], central);
        button->setCheckable(true);
        button->setAccessibleName(tab_names[id]);
        button->setObjectName(QStringLiteral("tab_") + QString::fromLatin1(tab_names[id]));
        tabs->addButton(button, id);
        tab_row->addWidget(button);
    }
    tab_row->addStretch(1);
    layout->addLayout(tab_row);

    auto* fixture_row = new QHBoxLayout();
    fixtures_ = new QButtonGroup(this);
    fixtures_->setExclusive(true);
    const char* labels[] = {"Closed box", "Open box", "Flipped box"};
    const char* names[] = {"closed_box", "open_box", "flipped_box"};
    for (int id = 0; id < 3; ++id) {
        auto* button = new QPushButton(labels[id], central);
        button->setCheckable(true);
        button->setObjectName(names[id]);
        button->setAccessibleName(names[id]);
        fixtures_->addButton(button, id);
        fixture_row->addWidget(button);
    }
    auto* export_button = new QPushButton(QStringLiteral("20 mm box"), central);
    export_button->setCheckable(true);
    export_button->setObjectName(QStringLiteral("box_20mm"));
    export_button->setAccessibleName(QStringLiteral("box_20mm"));
    fixtures_->addButton(export_button, 3);
    fixture_row->addWidget(export_button);
    fixture_row->addStretch(1);
    layout->addLayout(fixture_row);

    auto* body = new QHBoxLayout();
    browser_ = new QTreeWidget(central);
    browser_->setObjectName(QStringLiteral("browser"));
    browser_->setAccessibleName(QStringLiteral("Browser"));
    browser_->setHeaderLabel(QStringLiteral("Browser"));
    browser_->setMinimumWidth(150);
    auto* part_item = new QTreeWidgetItem(browser_, {QStringLiteral("Part")});
    auto* body_item = new QTreeWidgetItem(part_item, {QStringLiteral("Body")});
    body_item->setData(0, Qt::UserRole, 10);
    auto* fixture_item = new QTreeWidgetItem(browser_, {QStringLiteral("Fixtures")});
    const char* fixture_items[] = {"Closed box", "Open box", "Flipped box", "20 mm box"};
    for (int id = 0; id < 4; ++id) {
        auto* item = new QTreeWidgetItem(fixture_item, {QString::fromLatin1(fixture_items[id])});
        item->setData(0, Qt::UserRole, id);
    }
    browser_->expandAll();
    body->addWidget(browser_);

    view_ = new MeshView(central);
    body->addWidget(view_, 1);

    auto* properties = new QWidget(central);
    properties->setObjectName(QStringLiteral("properties"));
    properties->setAccessibleName(QStringLiteral("Properties"));
    auto* properties_layout = new QVBoxLayout(properties);
    auto* unit_row = new QHBoxLayout();
    auto* millimeters = new QRadioButton(QStringLiteral("Millimeters"), properties);
    auto* inches = new QRadioButton(QStringLiteral("Inches"), properties);
    millimeters->setAccessibleName(QStringLiteral("Millimeters"));
    inches->setAccessibleName(QStringLiteral("Inches"));
    millimeters->setObjectName(QStringLiteral("units_mm"));
    inches->setObjectName(QStringLiteral("units_in"));
    auto* unit_group = new QButtonGroup(this);
    unit_group->setExclusive(true);
    unit_group->addButton(millimeters, 0);
    unit_group->addButton(inches, 1);
    millimeters->setChecked(true);
    unit_row->addWidget(millimeters);
    unit_row->addWidget(inches);
    properties_layout->addLayout(unit_row);

    measure_ = new QLabel(QStringLiteral("Measure: no edge selected"), properties);
    measure_->setObjectName(QStringLiteral("measure-readout"));
    measure_->setWordWrap(true);
    measure_->setAccessibleName(measure_->text());
    properties_layout->addWidget(measure_);

    auto* form = new QFormLayout();
    makeSpin(form, QStringLiteral("Width"), &width_mm_);
    makeSpin(form, QStringLiteral("Depth"), &depth_mm_);
    makeSpin(form, QStringLiteral("Height"), &height_mm_);
    makeSpin(form, QStringLiteral("Radius"), &radius_mm_);
    makeSpin(form, QStringLiteral("X"), &x_mm_);
    makeSpin(form, QStringLiteral("Y"), &y_mm_);
    makeSpin(form, QStringLiteral("Z"), &z_mm_);
    makeSpin(form, QStringLiteral("Extrude"), &extrude_mm_);
    makeSpin(form, QStringLiteral("Fillet"), &fillet_mm_);
    properties_layout->addLayout(form);

    auto* sketch_page = new QWidget(stack);
    auto* sketch_layout = new QVBoxLayout(sketch_page);
    auto* sketch_note = new QLabel(
        QStringLiteral("XY plane. Line uses X,Y to X+Width, Y+Depth. Rectangle uses Width and Depth. Circle uses X, Y, and Radius."),
        sketch_page);
    sketch_note->setWordWrap(true);
    sketch_layout->addWidget(sketch_note);
    const auto add_sketch_button = [&](const QString& text, auto slot) {
        QPushButton* button = toolButton(sketch_page, sketch_layout, text);
        connect(button, &QPushButton::clicked, this, slot);
    };
    add_sketch_button(QStringLiteral("Line"), [this] { addSketchLine(); });
    add_sketch_button(QStringLiteral("Rectangle"), [this] { addSketchRectangle(); });
    add_sketch_button(QStringLiteral("Circle"), [this] { addSketchCircle(); });
    add_sketch_button(QStringLiteral("Horizontal"), [this] { constrainHorizontal(); });
    add_sketch_button(QStringLiteral("Vertical"), [this] { constrainVertical(); });
    add_sketch_button(QStringLiteral("Coincident"), [this] { constrainCoincident(); });
    add_sketch_button(QStringLiteral("Distance"), [this] { constrainDistance(); });
    add_sketch_button(QStringLiteral("Radius"), [this] { constrainRadius(); });
    add_sketch_button(QStringLiteral("Finish Sketch"), [this] { finishSketch(); });
    sketch_layout->addStretch(1);
    stack->addWidget(sketch_page);

    auto* solid_page = new QWidget(stack);
    auto* solid_layout = new QVBoxLayout(solid_page);
    auto* solid_note = new QLabel(
        QStringLiteral("The first solid is the part. The next solid is the tool for Union or Cut. Fillet uses the selected edge."),
        solid_page);
    solid_note->setWordWrap(true);
    solid_layout->addWidget(solid_note);
    const auto add_solid_button = [&](const QString& text, auto slot) {
        QPushButton* button = toolButton(solid_page, solid_layout, text);
        connect(button, &QPushButton::clicked, this, slot);
    };
    add_solid_button(QStringLiteral("Box"), [this] { makeBox(); });
    add_solid_button(QStringLiteral("Cylinder"), [this] { makeCylinder(); });
    add_solid_button(QStringLiteral("Extrude"), [this] { extrudeCurrentSketch(); });
    add_solid_button(QStringLiteral("Union"), [this] { unionSolids(); });
    add_solid_button(QStringLiteral("Cut"), [this] { cutSolid(); });
    add_solid_button(QStringLiteral("Fillet"), [this] { filletSelected(); });
    add_solid_button(QStringLiteral("Export STL + 3MF"), [this] { exportCurrent(); });
    solid_layout->addStretch(1);
    stack->addWidget(solid_page);

    auto* inspect_page = new QWidget(stack);
    auto* inspect_layout = new QVBoxLayout(inspect_page);
    auto* inspect_note = new QLabel(
        QStringLiteral("Left drag orbits. Right drag pans. Wheel zooms. A left click selects the nearest edge."),
        inspect_page);
    inspect_note->setWordWrap(true);
    inspect_layout->addWidget(inspect_note);
    QPushButton* check_button = toolButton(inspect_page, inspect_layout, QStringLiteral("Check watertight"));
    connect(check_button, &QPushButton::clicked, this, [this] { inspectMesh(); });
    inspect_layout->addStretch(1);
    stack->addWidget(inspect_page);

    properties_layout->addWidget(stack);
    auto* scroll = new QScrollArea(central);
    scroll->setWidgetResizable(true);
    scroll->setWidget(properties);
    scroll->setMinimumWidth(230);
    scroll->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    body->addWidget(scroll);
    layout->addLayout(body, 1);

    timeline_ = new QListWidget(central);
    timeline_->setObjectName(QStringLiteral("timeline"));
    timeline_->setAccessibleName(QStringLiteral("Timeline"));
    timeline_->setMaximumHeight(72);
    layout->addWidget(timeline_);

    result_ = new QLabel(central);
    result_->setObjectName(QStringLiteral("watertight-result"));
    result_->setWordWrap(true);
    result_->setMinimumHeight(48);
    result_->setTextInteractionFlags(Qt::TextSelectableByMouse);
    layout->addWidget(result_);

    setCentralWidget(central);
    setWindowTitle(QStringLiteral("Mesh view"));
    const QRect available = QGuiApplication::primaryScreen()->availableGeometry();
    const int width = qMin(960, qMax(640, available.width() - 80));
    const int height = qMin(640, qMax(480, available.height() - 80));
    resize(width, height);
    move(available.center() - QPoint(width / 2, height / 2));

    connect(tabs, &QButtonGroup::idClicked, stack, &QStackedWidget::setCurrentIndex);
    tabs->button(1)->setChecked(true);
    stack->setCurrentIndex(1);
    connect(fixtures_, &QButtonGroup::idClicked, this, [this](int id) { selectFixture(id); });
    connect(unit_group, &QButtonGroup::idClicked, this, [this](int id) {
        const bool want_inch = id == 1;
        const bool is_inch = units_.display() == DisplayUnit::Inch;
        if (want_inch != is_inch) {
            units_.toggle();
        }
        pushSpins();
        refreshMeasure();
        addTimeline(want_inch ? QStringLiteral("Display: inches") : QStringLiteral("Display: millimeters"));
    });
    connect(browser_, &QTreeWidget::itemClicked, this, [this](QTreeWidgetItem* item, int) {
        if (item == nullptr || !item->data(0, Qt::UserRole).isValid()) {
            return;
        }
        const int id = item->data(0, Qt::UserRole).toInt();
        if (id >= 0 && id <= 3) {
            selectFixture(id);
        } else if (id == 10) {
            showCurrentBody();
        }
    });
    view_->setSelectionHandler([this] { refreshMeasure(); });

    pushSpins();
    selectFixture(0);
}

QDoubleSpinBox* MainWindow::makeSpin(QFormLayout* form, const QString& label, double* millimeters) {
    auto* spin = new QDoubleSpinBox(this);
    spin->setRange(-100000.0, 100000.0);
    spin->setDecimals(4);
    spin->setAccessibleName(label);
    spin->setObjectName(QStringLiteral("spin_") + label);
    form->addRow(label, spin);
    connect(spin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), this, [this, millimeters](double displayed) {
        *millimeters = units_.to_millimeters(displayed);
    });
    spins_.push_back(SpinBinding{spin, millimeters});
    return spin;
}

void MainWindow::pushSpins() {
    const bool inches = units_.display() == DisplayUnit::Inch;
    for (const SpinBinding& binding : spins_) {
        binding.spin->blockSignals(true);
        binding.spin->setSuffix(inches ? QStringLiteral(" in") : QStringLiteral(" mm"));
        binding.spin->setSingleStep(inches ? 0.01 : 0.1);
        binding.spin->setValue(units_.to_display(*binding.millimeters));
        binding.spin->blockSignals(false);
    }
}

void MainWindow::setResult(const QString& text) {
    result_->setText(text);
    result_->setAccessibleName(text);
}

void MainWindow::addTimeline(const QString& text) {
    timeline_->addItem(text);
    timeline_->scrollToBottom();
}

void MainWindow::refreshMeasure() {
    std::uint32_t a = 0;
    std::uint32_t b = 0;
    if (!view_->selectedEdge(a, b) || a >= shown_.vertices.size() || b >= shown_.vertices.size()) {
        measure_->setText(QStringLiteral("Measure: no edge selected"));
        measure_->setAccessibleName(measure_->text());
        return;
    }
    const Vec3& pa = shown_.vertices[a];
    const Vec3& pb = shown_.vertices[b];
    const double dx = pa.x - pb.x;
    const double dy = pa.y - pb.y;
    const double dz = pa.z - pb.z;
    const double millimeters = std::sqrt(dx * dx + dy * dy + dz * dz);
    const QString unit = units_.display() == DisplayUnit::Inch ? QStringLiteral("in") : QStringLiteral("mm");
    measure_->setText(QStringLiteral("Measure: edge %1-%2 = %3 %4")
                          .arg(a)
                          .arg(b)
                          .arg(units_.to_display(millimeters), 0, 'g', 8)
                          .arg(unit));
    measure_->setAccessibleName(measure_->text());
}

void MainWindow::refreshSketchGuides() {
    std::vector<std::pair<Vec3, Vec3>> lines;
    for (const Sketch::Line& line : sketch_.lines) {
        if (line.a < 0 || line.b < 0 || line.a >= static_cast<int>(sketch_.points.size()) ||
            line.b >= static_cast<int>(sketch_.points.size())) {
            continue;
        }
        const Sketch::Point& a = sketch_.points[static_cast<std::size_t>(line.a)];
        const Sketch::Point& b = sketch_.points[static_cast<std::size_t>(line.b)];
        lines.push_back({Vec3{a.x, a.y, 0.0}, Vec3{b.x, b.y, 0.0}});
    }
    constexpr int kSegments = 24;
    constexpr double kPi = 3.14159265358979323846;
    for (const Sketch::Circle& circle : sketch_.circles) {
        if (circle.center < 0 || circle.center >= static_cast<int>(sketch_.points.size()) ||
            !(circle.radius > 0.0)) {
            continue;
        }
        const Sketch::Point& center = sketch_.points[static_cast<std::size_t>(circle.center)];
        for (int i = 0; i < kSegments; ++i) {
            const double a0 = kPi * 2.0 * static_cast<double>(i) / kSegments;
            const double a1 = kPi * 2.0 * static_cast<double>(i + 1) / kSegments;
            lines.push_back({Vec3{center.x + circle.radius * std::cos(a0), center.y + circle.radius * std::sin(a0), 0.0},
                             Vec3{center.x + circle.radius * std::cos(a1), center.y + circle.radius * std::sin(a1), 0.0}});
        }
    }
    view_->setGuideLines(lines);
}

void MainWindow::showMesh(const MeshSolid& mesh, bool fixture_camera) {
    shown_ = mesh;
    view_->setGuideLines({});
    view_->setMesh(mesh);
    if (fixture_camera) {
        view_->resetFixtureCamera();
    } else {
        view_->frameMesh();
    }
    const WatertightResult result = check_watertight(mesh);
    setResult(QString::fromStdString(result.message));
    refreshMeasure();
}

void MainWindow::adoptSolid(const MeshSolid& mesh, const QString& label) {
    if (viewing_fixture_ || !has_body_) {
        body_ = mesh;
        has_body_ = true;
        viewing_fixture_ = false;
        has_tool_ = false;
        showing_tool_ = false;
    } else {
        tool_ = mesh;
        has_tool_ = true;
        showing_tool_ = true;
    }
    showMesh(mesh, false);
    addTimeline(label);
}

void MainWindow::selectFixture(int id) {
    fixtures_->blockSignals(true);
    if (QAbstractButton* button = fixtures_->button(id)) {
        button->setChecked(true);
    }
    fixtures_->blockSignals(false);
    if (id == 3) {
        showExportBox();
        return;
    }
    showFixture(id);
}

void MainWindow::showFixture(int id) {
    MeshSolid mesh;
    QString name;
    if (id == 0) {
        mesh = closed_box();
        name = QStringLiteral("Closed box");
    } else if (id == 1) {
        mesh = open_box();
        name = QStringLiteral("Open box");
    } else if (id == 2) {
        mesh = flipped_box();
        name = QStringLiteral("Flipped box");
    } else {
        return;
    }
    body_ = mesh;
    has_body_ = true;
    has_tool_ = false;
    showing_tool_ = false;
    viewing_fixture_ = true;
    showMesh(mesh, true);
    addTimeline(name);
}

void MainWindow::showCurrentBody() {
    if (!has_body_) {
        setResult(QStringLiteral("No part yet."));
        return;
    }
    showing_tool_ = false;
    showMesh(body_, viewing_fixture_);
    addTimeline(QStringLiteral("Body"));
}

void MainWindow::showExportBox() {
    const MeshSolid box = box_mm(20.0, 20.0, 20.0);
    const std::filesystem::path directory =
        repo_export_dir(std::filesystem::path(QCoreApplication::applicationDirPath().toStdWString()));
    const ExportAttempt attempt = export_mesh_if_closed(box, directory);
    MeshSolid shown = box;
    if (attempt.wrote) {
        MeshSolid loaded;
        if (read_binary_stl(attempt.stl_path, loaded)) {
            shown = std::move(loaded);
        }
    }
    body_ = box;
    has_body_ = true;
    has_tool_ = false;
    showing_tool_ = false;
    viewing_fixture_ = true;
    shown_ = shown;
    view_->setGuideLines({});
    view_->setMesh(shown);
    view_->frameMesh();
    QString text = QString::fromStdString(attempt.check.message);
    if (attempt.wrote) {
        text += QStringLiteral("\nWrote ");
        text += QString::fromStdWString(attempt.stl_path.wstring());
        text += QStringLiteral(" and ");
        text += QString::fromStdWString(attempt.threemf_path.wstring());
    }
    setResult(text);
    refreshMeasure();
    addTimeline(QStringLiteral("20 mm box"));
}

void MainWindow::addSketchLine() {
    if (!(std::fabs(width_mm_) > 1.0e-9 || std::fabs(depth_mm_) > 1.0e-9)) {
        setResult(QStringLiteral("Line needs a non-zero Width or Depth."));
        return;
    }
    last_line_ = sketch_.add_line(x_mm_, y_mm_, x_mm_ + width_mm_, y_mm_ + depth_mm_);
    refreshSketchGuides();
    addTimeline(QStringLiteral("Line"));
    setResult(QStringLiteral("Line added on the XY plane. Finish Sketch, then Extrude."));
}

void MainWindow::addSketchRectangle() {
    if (!(width_mm_ > 0.0) || !(depth_mm_ > 0.0)) {
        setResult(QStringLiteral("Rectangle Width and Depth must be positive."));
        return;
    }
    last_line_ = sketch_.add_rectangle(x_mm_, y_mm_, width_mm_, depth_mm_);
    refreshSketchGuides();
    addTimeline(QStringLiteral("Rectangle"));
    setResult(QStringLiteral("Rectangle added with horizontal, vertical, and distance constraints. Finish Sketch, then Extrude."));
}

void MainWindow::addSketchCircle() {
    if (!(radius_mm_ > 0.0)) {
        setResult(QStringLiteral("Circle Radius must be positive."));
        return;
    }
    last_circle_ = sketch_.add_circle(x_mm_, y_mm_, radius_mm_);
    refreshSketchGuides();
    addTimeline(QStringLiteral("Circle"));
    setResult(QStringLiteral("Circle added. Radius sets the dimension. Finish Sketch, then Extrude."));
}

void MainWindow::constrainHorizontal() {
    if (last_line_ < 0) {
        setResult(QStringLiteral("Add a line before Horizontal."));
        return;
    }
    sketch_.add_horizontal(last_line_);
    addTimeline(QStringLiteral("Horizontal"));
    setResult(QStringLiteral("Horizontal constraint stored. Finish Sketch solves it."));
}

void MainWindow::constrainVertical() {
    if (last_line_ < 0) {
        setResult(QStringLiteral("Add a line before Vertical."));
        return;
    }
    sketch_.add_vertical(last_line_);
    addTimeline(QStringLiteral("Vertical"));
    setResult(QStringLiteral("Vertical constraint stored. Finish Sketch solves it."));
}

void MainWindow::constrainCoincident() {
    if (sketch_.lines.size() < 2) {
        setResult(QStringLiteral("Add two lines before Coincident."));
        return;
    }
    const Sketch::Line& newest = sketch_.lines.back();
    const Sketch::Line& previous = sketch_.lines[sketch_.lines.size() - 2];
    sketch_.add_coincident(newest.a, previous.a);
    addTimeline(QStringLiteral("Coincident"));
    setResult(QStringLiteral("Coincident constraint stored between the newest line start and the previous line start."));
}

void MainWindow::constrainDistance() {
    if (last_line_ < 0 || last_line_ >= static_cast<int>(sketch_.lines.size())) {
        setResult(QStringLiteral("Add a line before Distance."));
        return;
    }
    if (!(width_mm_ > 0.0)) {
        setResult(QStringLiteral("Distance uses a positive Width, in millimeters internally."));
        return;
    }
    const Sketch::Line& line = sketch_.lines[static_cast<std::size_t>(last_line_)];
    sketch_.add_distance(line.a, line.b, width_mm_);
    addTimeline(QStringLiteral("Distance"));
    setResult(QStringLiteral("Distance constraint stored from Width. The value stays in millimeters."));
}

void MainWindow::constrainRadius() {
    if (last_circle_ < 0 || last_circle_ >= static_cast<int>(sketch_.circles.size())) {
        setResult(QStringLiteral("Add a circle before Radius."));
        return;
    }
    if (!(radius_mm_ > 0.0)) {
        setResult(QStringLiteral("Radius must be positive."));
        return;
    }
    sketch_.add_radius(last_circle_, radius_mm_);
    addTimeline(QStringLiteral("Radius"));
    setResult(QStringLiteral("Radius dimension stored. The value stays in millimeters."));
}

void MainWindow::finishSketch() {
    if (sketch_.lines.empty() && sketch_.circles.empty()) {
        setResult(QStringLiteral("Sketch is empty."));
        return;
    }
    sketch_.solve();
    refreshSketchGuides();
    addTimeline(QStringLiteral("Finish sketch"));
    setResult(QStringLiteral("Sketch finished. Extrude travels +Z by the Extrude distance."));
}

void MainWindow::makeBox() {
    if (!(width_mm_ > 0.0) || !(depth_mm_ > 0.0) || !(height_mm_ > 0.0)) {
        setResult(QStringLiteral("Box Width, Depth, and Height must be positive."));
        return;
    }
    const MeshSolid mesh = translate_mesh(box_mm(width_mm_, depth_mm_, height_mm_), x_mm_, y_mm_, z_mm_);
    adoptSolid(mesh, QStringLiteral("Box %1 x %2 x %3 mm").arg(width_mm_).arg(depth_mm_).arg(height_mm_));
}

void MainWindow::makeCylinder() {
    if (!(radius_mm_ > 0.0) || !(height_mm_ > 0.0)) {
        setResult(QStringLiteral("Cylinder Radius and Height must be positive."));
        return;
    }
    MeshSolid mesh = cylinder_mm(x_mm_, y_mm_, radius_mm_, height_mm_, 24);
    if (z_mm_ != 0.0) {
        mesh = translate_mesh(mesh, 0.0, 0.0, z_mm_);
    }
    adoptSolid(mesh, QStringLiteral("Cylinder r %1 h %2 mm").arg(radius_mm_).arg(height_mm_));
}

void MainWindow::extrudeCurrentSketch() {
    if (sketch_.lines.empty() && sketch_.circles.empty()) {
        setResult(QStringLiteral("Sketch is empty."));
        return;
    }
    sketch_.solve();
    const ExtrudeResult result = extrude_sketch(sketch_, extrude_mm_);
    if (!result.ok) {
        setResult(QString::fromStdString(result.message));
        addTimeline(QString::fromStdString(result.message));
        return;
    }
    adoptSolid(result.mesh, QStringLiteral("Extrude %1 mm").arg(extrude_mm_));
}

void MainWindow::unionSolids() {
    if (viewing_fixture_ || !has_body_ || !has_tool_) {
        setResult(QStringLiteral("Create a part, then a second solid, then Union."));
        addTimeline(QStringLiteral("Union needs two solids"));
        return;
    }
    body_ = mesh_union(body_, tool_);
    has_tool_ = false;
    showing_tool_ = false;
    showMesh(body_, false);
    addTimeline(QStringLiteral("Union"));
}

void MainWindow::cutSolid() {
    if (viewing_fixture_ || !has_body_ || !has_tool_) {
        setResult(QStringLiteral("Create a part, then a box tool inside it, then Cut."));
        addTimeline(QStringLiteral("Cut needs two solids"));
        return;
    }
    const CutResult result = mesh_cut(body_, tool_);
    if (!result.ok) {
        setResult(QString::fromStdString(result.message));
        addTimeline(QString::fromStdString(result.message));
        return;
    }
    body_ = result.mesh;
    has_tool_ = false;
    showing_tool_ = false;
    showMesh(body_, false);
    addTimeline(QStringLiteral("Cut"));
}

void MainWindow::filletSelected() {
    std::uint32_t a = 0;
    std::uint32_t b = 0;
    if (!view_->selectedEdge(a, b)) {
        setResult(QStringLiteral("Select an edge, then Fillet."));
        addTimeline(QStringLiteral("Fillet needs an edge"));
        return;
    }
    if (!(fillet_mm_ > 0.0)) {
        setResult(QStringLiteral("Fillet radius must be positive."));
        return;
    }
    const FilletResult result = fillet_box_edge(shown_, a, b, fillet_mm_);
    if (!result.ok) {
        setResult(QString::fromStdString(result.message));
        addTimeline(QString::fromStdString(result.message));
        return;
    }
    if (showing_tool_ && has_tool_) {
        tool_ = result.mesh;
        showMesh(tool_, false);
    } else {
        body_ = result.mesh;
        has_body_ = true;
        viewing_fixture_ = false;
        showMesh(body_, false);
    }
    addTimeline(QStringLiteral("Fillet %1 mm").arg(fillet_mm_));
}

void MainWindow::exportCurrent() {
    if (!has_body_ || body_.triangles.empty()) {
        setResult(QStringLiteral("Nothing to export."));
        return;
    }
    const RepairResult repair = repair_manifold(body_);
    if (!repair.pass) {
        setResult(QString::fromStdString(repair.message));
        addTimeline(QString::fromStdString(repair.message));
        return;
    }
    if (repair.changed) {
        body_ = repair.mesh;
        if (!showing_tool_) {
            showMesh(body_, false);
        }
    }
    const std::filesystem::path directory =
        repo_export_dir(std::filesystem::path(QCoreApplication::applicationDirPath().toStdWString()));
    const ExportAttempt attempt = export_mesh_if_closed(body_, directory);
    QString text = QString::fromStdString(attempt.check.message);
    if (attempt.wrote) {
        text += QStringLiteral("\nWrote ");
        text += QString::fromStdWString(attempt.stl_path.wstring());
        text += QStringLiteral(" and ");
        text += QString::fromStdWString(attempt.threemf_path.wstring());
        addTimeline(QStringLiteral("Export PASS"));
    } else {
        addTimeline(QStringLiteral("Export blocked"));
    }
    setResult(text);
}

void MainWindow::inspectMesh() {
    const WatertightResult result = check_watertight(shown_);
    setResult(QString::fromStdString(result.message));
    addTimeline(QStringLiteral("Inspect"));
}
