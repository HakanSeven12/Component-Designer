"""
Main Window for Component Designer
"""
import json
from PySide2.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QSplitter, QAction, QToolBar,
                               QFileDialog, QMessageBox, QComboBox, QCheckBox)
from PySide2.QtCore import Qt

from flowchart import FlowchartView, _TYPED_INPUT_TYPES
from preview import GeometryPreview
from panels import ToolboxPanel
from flowchart import FlowchartNodeItem
from models import create_node_from_dict


class ComponentDesigner(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Component Designer - FreeCAD Road Workbench")
        self.current_file = None
        self.modified     = False

        self.setup_ui()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.connect_signals()
        self.showMaximized()

    def setup_ui(self):
        central     = QWidget()
        main_layout = QHBoxLayout()

        left_splitter = QSplitter(Qt.Vertical)
        self.toolbox  = ToolboxPanel()
        left_splitter.addWidget(self.toolbox)
        left_splitter.setSizes([300, 200])

        center_splitter = QSplitter(Qt.Vertical)

        flowchart_container = QWidget()
        flowchart_layout    = QVBoxLayout()
        flowchart_label     = QLabel("Flowchart")
        flowchart_label.setStyleSheet(
            "font-weight: bold; background: #e0e0e0; padding: 5px;")
        self.flowchart = FlowchartView()
        flowchart_layout.addWidget(flowchart_label)
        flowchart_layout.addWidget(self.flowchart)
        flowchart_layout.setContentsMargins(0, 0, 0, 0)
        flowchart_container.setLayout(flowchart_layout)

        preview_container = QWidget()
        preview_layout    = QVBoxLayout()
        preview_header    = QHBoxLayout()

        preview_label = QLabel("Preview")
        preview_label.setStyleSheet(
            "font-weight: bold; background: #e0e0e0; padding: 5px;")

        self.preview_mode_combo = QComboBox()
        self.preview_mode_combo.addItems(["Layout Mode", "Roadway Mode"])
        self.show_codes_check    = QCheckBox("Codes")
        self.show_codes_check.setChecked(True)
        self.show_comments_check = QCheckBox("Comments")

        preview_header.addWidget(preview_label)
        preview_header.addStretch()
        preview_header.addWidget(QLabel("Mode:"))
        preview_header.addWidget(self.preview_mode_combo)
        preview_header.addWidget(self.show_codes_check)
        preview_header.addWidget(self.show_comments_check)

        preview_header_widget = QWidget()
        preview_header_widget.setLayout(preview_header)
        preview_header_widget.setStyleSheet("background: #e0e0e0;")

        self.preview = GeometryPreview()
        preview_layout.addWidget(preview_header_widget)
        preview_layout.addWidget(self.preview)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_container.setLayout(preview_layout)

        center_splitter.addWidget(flowchart_container)
        center_splitter.addWidget(preview_container)
        center_splitter.setSizes([400, 400])

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(center_splitter)
        main_splitter.setSizes([250, 800])

        main_layout.addWidget(main_splitter)
        central.setLayout(main_layout)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Ready")

    def create_actions(self):
        self.new_action = QAction("New", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.triggered.connect(self.new_file)

        self.open_action = QAction("Open...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_file)

        self.save_action = QAction("Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_file)

        self.save_as_action = QAction("Save As...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.triggered.connect(self.save_file_as)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)

        self.restore_layout_action = QAction("Restore Default Layout", self)
        self.restore_layout_action.triggered.connect(self.restore_default_layout)

        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.show_about)

    def create_menus(self):
        menubar   = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        view_menu = menubar.addMenu("View")
        view_menu.addAction(self.restore_layout_action)

        menubar.addMenu("Define")

        help_menu = menubar.addMenu("Help")
        help_menu.addAction(self.about_action)

    def create_toolbars(self):
        toolbar = QToolBar("Main Tools")
        self.addToolBar(toolbar)
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()

        update_btn = QAction("Update Preview", self)
        update_btn.triggered.connect(self.update_preview)
        toolbar.addAction(update_btn)

    def connect_signals(self):
        self.toolbox.element_selected.connect(self.add_element_to_flowchart)
        self.show_codes_check.stateChanged.connect(self.toggle_codes)
        self.show_comments_check.stateChanged.connect(self.toggle_comments)
        self.flowchart.scene.node_selected.connect(self.on_flowchart_node_selected)
        self.flowchart.scene.preview_update_requested.connect(self.update_preview)

    def on_flowchart_node_selected(self, node):
        self.statusBar().showMessage(f"Selected: {node.type} - {node.name}")
        self.preview.select_node_visually(node)

    def sync_selection_from_preview(self, node):
        self.statusBar().showMessage(f"Selected: {node.type} - {node.name}")
        self.flowchart.select_node_visually(node)

    def add_element_to_flowchart(self, element_type: str):
        creators = {
            "Point":    self.flowchart.add_point_node,
            "Link":     self.flowchart.add_link_node,
            "Shape":    self.flowchart.add_shape_node,
            "Decision": self.flowchart.add_decision_node,
            "Output":   self.flowchart.add_output_parameter_node,
            "Target":   self.flowchart.add_target_parameter_node,
        }
        fn = creators.get(element_type)
        if fn:
            fn()
        elif element_type in _TYPED_INPUT_TYPES:
            self.flowchart.add_typed_input_node(element_type)
        else:
            x, y = self.flowchart._auto_pos()
            self.flowchart.create_generic_node_at(element_type, x, y)

        self.modified = True
        self.update_preview()

    def update_preview(self):
        self.preview.update_preview(self.flowchart.scene.nodes)

    def toggle_codes(self, state):
        self.preview.show_codes = (state == Qt.Checked)
        self.update_preview()

    def toggle_comments(self, state):
        self.preview.show_comments = (state == Qt.Checked)
        self.update_preview()

    def new_file(self):
        if self.check_save_changes():
            self.flowchart.scene.clear()
            self.flowchart.scene.nodes.clear()
            self.flowchart.scene.connections.clear()
            self.flowchart.scene.port_wires.clear()
            self.flowchart.node_counter = 0
            self.preview.scene.clear()
            self.preview.setup_scene()
            self.flowchart.create_start_node()
            self.current_file = None
            self.modified     = False
            self.statusBar().showMessage("New component created")

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open JSON File", "", "JSON Files (*.json)")
        if filename:
            self.load_file(filename)

    def save_file(self):
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_file_as()

    def save_file_as(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save As", "", "JSON Files (*.json)")
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
            self.save_to_file(filename)
            self.current_file = filename

    def save_to_file(self, filename):
        data = {'nodes': [], 'connections': []}
        for node in self.flowchart.scene.nodes.values():
            data['nodes'].append(node.to_dict())
        data['connections'] = self.flowchart.scene.connections

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.modified = False
        self.statusBar().showMessage(f"Saved: {filename}")

    def load_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.flowchart.scene.clear()
            self.flowchart.scene.nodes.clear()
            self.flowchart.scene.connections.clear()
            self.flowchart.scene.port_wires.clear()
            self.flowchart.node_counter = 0

            node_map = {}
            for node_data in data.get('nodes', []):
                node      = create_node_from_dict(node_data)
                x, y      = node_data.get('x', 0), node_data.get('y', 0)
                node.x, node.y = x, y
                self.flowchart.scene.nodes[node.id] = node
                item = FlowchartNodeItem(node, x, y)
                self.flowchart.scene.addItem(item)
                node_map[node.id] = node

                if node.id.startswith('N'):
                    try:
                        num = int(node.id[1:])
                        if num > self.flowchart.node_counter:
                            self.flowchart.node_counter = num
                    except ValueError:
                        pass

            for conn in data.get('connections', []):
                from_id   = conn['from']
                to_id     = conn['to']
                from_port = conn.get('from_port', 'vector')
                to_port   = conn.get('to_port',   'reference')
                if from_id in node_map and to_id in node_map:
                    self.flowchart.scene.connect_nodes_with_wire(
                        node_map[from_id], node_map[to_id],
                        from_port, to_port,
                    )

            self.current_file = filename
            self.modified     = False
            self.statusBar().showMessage(f"Loaded: {filename}")
            self.update_preview()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")
            import traceback
            traceback.print_exc()

    def check_save_changes(self):
        if self.modified:
            reply = QMessageBox.question(
                self, "Save Changes?",
                "The file has unsaved changes. Do you want to save them?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Save:
                self.save_file()
                return True
            elif reply == QMessageBox.Cancel:
                return False
        return True

    def restore_default_layout(self):
        pass

    def show_about(self):
        QMessageBox.about(
            self, "About",
            "Component Designer for FreeCAD Road Workbench\n\n"
            "An advanced tool for designing road cross-section components.\n\n"
            "Version 1.0",
        )

    def closeEvent(self, event):
        if self.check_save_changes():
            event.accept()
        else:
            event.ignore()