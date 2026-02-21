"""
Main Window for Component Designer
"""
import json
import traceback
from PySide2.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QSplitter, QAction, QToolBar,
                               QFileDialog, QMessageBox, QComboBox, QCheckBox,
                               QApplication)
from PySide2.QtCore import Qt

from .flowchart import FlowchartNodeItem, FlowchartView, _prefix_for_type
from .preview import GeometryPreview
from .panels import ToolboxPanel
from .models import create_node_from_dict
from .theme_dark import theme


class ComponentDesigner(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Component Designer - FreeCAD Road Workbench")
        self.current_file = None
        self.modified     = False

        theme.apply_palette(QApplication.instance())

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

        # ── Flowchart panel ──────────────────────────────────────────────
        flowchart_container = QWidget()
        flowchart_layout    = QVBoxLayout()
        flowchart_label     = QLabel("Flowchart")
        flowchart_label.setStyleSheet(theme.PANEL_LABEL_STYLE)
        self.flowchart = FlowchartView()
        flowchart_layout.addWidget(flowchart_label)
        flowchart_layout.addWidget(self.flowchart)
        flowchart_layout.setContentsMargins(0, 0, 0, 0)
        flowchart_container.setLayout(flowchart_layout)

        # ── Preview panel ────────────────────────────────────────────────
        preview_container = QWidget()
        preview_layout    = QVBoxLayout()
        preview_header    = QHBoxLayout()

        preview_label = QLabel("Preview")
        preview_label.setStyleSheet(theme.PREVIEW_LABEL_STYLE)

        self.preview_mode_combo = QComboBox()
        self.preview_mode_combo.addItems(["Layout Mode", "Roadway Mode"])
        self.preview_mode_combo.setStyleSheet(theme.PREVIEW_COMBO_STYLE)

        self.show_codes_check = QCheckBox("Codes")
        self.show_codes_check.setChecked(True)
        self.show_codes_check.setStyleSheet(theme.PREVIEW_CHECKBOX_STYLE)

        self.show_comments_check = QCheckBox("Comments")
        self.show_comments_check.setStyleSheet(theme.PREVIEW_CHECKBOX_STYLE)

        preview_header.addWidget(preview_label)
        preview_header.addStretch()
        preview_header.addWidget(QLabel("Mode:"))
        preview_header.addWidget(self.preview_mode_combo)
        preview_header.addWidget(self.show_codes_check)
        preview_header.addWidget(self.show_comments_check)

        preview_header_widget = QWidget()
        preview_header_widget.setLayout(preview_header)
        preview_header_widget.setStyleSheet(theme.PREVIEW_HEADER_STYLE)

        for child in preview_header_widget.findChildren(QLabel):
            if child is not preview_label:
                child.setStyleSheet(
                    "color: #8a98b0; font-size: 8pt; background: transparent;")

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

        self.setStyleSheet(
            theme.MENUBAR_STYLE +
            theme.TOOLBAR_STYLE +
            theme.STATUSBAR_STYLE +
            theme.SPLITTER_STYLE
        )
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

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self.do_undo)

        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self.do_redo)

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

        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.aboutToShow.connect(self._refresh_edit_menu)

        view_menu = menubar.addMenu("View")
        view_menu.addAction(self.restore_layout_action)

        menubar.addMenu("Define")

        help_menu = menubar.addMenu("Help")
        help_menu.addAction(self.about_action)

    def _refresh_edit_menu(self):
        stack = self.flowchart.undo_stack
        if stack.can_undo():
            self.undo_action.setText(f"Undo: {stack.undo_description}")
            self.undo_action.setEnabled(True)
        else:
            self.undo_action.setText("Undo")
            self.undo_action.setEnabled(False)

        if stack.can_redo():
            self.redo_action.setText(f"Redo: {stack.redo_description}")
            self.redo_action.setEnabled(True)
        else:
            self.redo_action.setText("Redo")
            self.redo_action.setEnabled(False)

    def create_toolbars(self):
        toolbar = QToolBar("Main Tools")
        self.addToolBar(toolbar)
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
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

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------

    def do_undo(self):
        desc = self.flowchart.undo_stack.undo()
        if desc:
            self.statusBar().showMessage(f"Undo: {desc}", 3000)
            self.modified = True
            self.update_preview()

    def do_redo(self):
        desc = self.flowchart.undo_stack.redo()
        if desc:
            self.statusBar().showMessage(f"Redo: {desc}", 3000)
            self.modified = True
            self.update_preview()

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def on_flowchart_node_selected(self, node):
        self.statusBar().showMessage(f"Selected: {node.type} - {node.name}")
        self.preview.select_node_visually(node)

    def sync_selection_from_preview(self, node):
        self.statusBar().showMessage(f"Selected: {node.type} - {node.name}")
        self.flowchart.select_node_visually(node)

    def add_element_to_flowchart(self, element_type: str):
        self.flowchart.add_node_by_type(element_type)
        self.modified = True
        self.update_preview()

    # ------------------------------------------------------------------
    # Preview update  —  single entry point, no special-case resolvers
    # ------------------------------------------------------------------

    def update_preview(self):
        """
        Propagate all wire values (topological order) then redraw the preview.

        resolve_all_wires() is the ONLY place where inter-node data transfer
        happens.  It calls node.get_port_value() → node.set_port_value()
        for every connection in topological order, so every node has
        up-to-date inputs before its outputs are read by the preview renderer.
        """
        self.flowchart.scene.resolve_all_wires()
        self.preview.update_preview(
            self.flowchart.scene.nodes,
            connections=self.flowchart.scene.connections,
        )

    def toggle_codes(self, state):
        self.preview.show_codes = (state == Qt.Checked)
        self.update_preview()

    def toggle_comments(self, state):
        self.preview.show_comments = (state == Qt.Checked)
        self.update_preview()

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def new_file(self):
        if self.check_save_changes():
            self.flowchart.scene.clear()
            self.flowchart.scene.nodes.clear()
            self.flowchart.scene.connections.clear()
            self.flowchart.scene.port_wires.clear()
            self.flowchart.node_counter = 0
            self.flowchart._type_counters.clear()
            self.preview.scene.clear()
            self.preview.setup_scene()
            self.flowchart.create_start_node()
            self.flowchart.undo_stack.clear()
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
            self.flowchart._type_counters.clear()

            node_map = {}
            for node_data in data.get('nodes', []):
                node      = create_node_from_dict(node_data)
                x, y      = node_data.get('x', 0), node_data.get('y', 0)
                node.x, node.y = x, y
                self.flowchart.scene.nodes[node.id] = node
                item = FlowchartNodeItem(node, x, y)
                self.flowchart.scene.addItem(item)
                node_map[node.id] = node

                # Restore global ID counter
                if node.id.startswith('N'):
                    try:
                        num = int(node.id[1:])
                        if num > self.flowchart.node_counter:
                            self.flowchart.node_counter = num
                    except ValueError:
                        pass

                # Restore per-type name counter
                node_type = node.type
                prefix    = _prefix_for_type(node_type)
                name      = node.name or ""
                if name.upper().startswith(prefix.upper()):
                    suffix = name[len(prefix):]
                    if suffix.isdigit():
                        n   = int(suffix)
                        cur = self.flowchart._type_counters.get(node_type, 0)
                        if n > cur:
                            self.flowchart._type_counters[node_type] = n

            # ── Legacy migration: from_point / start_point / end_point ──
            # Old JSON files stored node-ID references instead of wires.
            # Convert them to proper connections so the wire system handles them.
            legacy_conns = []
            for node in node_map.values():
                fp = getattr(node, '_legacy_from_point', None)
                if fp and fp in node_map:
                    legacy_conns.append({
                        'from': fp,   'from_port': 'position',
                        'to':   node.id, 'to_port': 'reference',
                    })
                sp = getattr(node, '_legacy_start_point', None)
                if sp and sp in node_map:
                    legacy_conns.append({
                        'from': sp,   'from_port': 'position',
                        'to':   node.id, 'to_port': 'start',
                    })
                ep = getattr(node, '_legacy_end_point', None)
                if ep and ep in node_map:
                    legacy_conns.append({
                        'from': ep,   'from_port': 'position',
                        'to':   node.id, 'to_port': 'end',
                    })

            all_connections = data.get('connections', []) + legacy_conns
            # Deduplicate (to_id + to_port uniquely identifies an input)
            seen = set()
            deduped = []
            for conn in all_connections:
                key = (conn['to'], conn.get('to_port', ''))
                if key not in seen:
                    seen.add(key)
                    deduped.append(conn)

            for conn in deduped:
                from_id   = conn['from']
                to_id     = conn['to']
                from_port = conn.get('from_port', 'position')
                to_port   = conn.get('to_port',   'reference')
                if from_id in node_map and to_id in node_map:
                    self.flowchart.scene.connect_nodes_with_wire(
                        node_map[from_id], node_map[to_id],
                        from_port, to_port,
                    )

            self.flowchart.undo_stack.clear()
            self.current_file = filename
            self.modified     = False
            self.statusBar().showMessage(f"Loaded: {filename}")
            self.update_preview()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")
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
