"""
Main Window for Component Designer
Contains the main application window and file operations
"""
import json
from PySide2.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QSplitter, QAction, QToolBar, QFileDialog, QMessageBox,
                               QComboBox, QCheckBox)
from PySide2.QtCore import Qt

from flowchart import FlowchartView
from preview import GeometryPreview
from panels import PropertiesPanel, ParametersPanel, ToolboxPanel


class ComponentDesigner(QMainWindow):
    """Main Component Designer application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Component Designer - FreeCAD Road Workbench")
        
        self.current_file = None
        self.modified = False
        
        self.setup_ui()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.connect_signals()

        # Maximize window on startup
        self.showMaximized()
        
    def setup_ui(self):
        """Setup main user interface"""
        # Central widget with splitters
        central = QWidget()
        main_layout = QHBoxLayout()
        
        # Left side: Toolbox
        left_splitter = QSplitter(Qt.Vertical)
        
        self.toolbox = ToolboxPanel()
        left_splitter.addWidget(self.toolbox)
        left_splitter.setSizes([300, 200])
        
        # Center: Flowchart and Preview
        center_splitter = QSplitter(Qt.Vertical)
        
        flowchart_container = QWidget()
        flowchart_layout = QVBoxLayout()
        flowchart_label = QLabel("Flowchart")
        flowchart_label.setStyleSheet("font-weight: bold; background: #e0e0e0; padding: 5px;")
        self.flowchart = FlowchartView()
        flowchart_layout.addWidget(flowchart_label)
        flowchart_layout.addWidget(self.flowchart)
        flowchart_layout.setContentsMargins(0, 0, 0, 0)
        flowchart_container.setLayout(flowchart_layout)
        
        preview_container = QWidget()
        preview_layout = QVBoxLayout()
        preview_header = QHBoxLayout()
        preview_label = QLabel("Preview")
        preview_label.setStyleSheet("font-weight: bold; background: #e0e0e0; padding: 5px;")
        
        # Preview controls
        self.preview_mode_combo = QComboBox()
        self.preview_mode_combo.addItems(["Layout Mode", "Roadway Mode"])
        self.show_codes_check = QCheckBox("Codes")
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
        
        # Right side: Properties and Parameters
        right_splitter = QSplitter(Qt.Vertical)
        
        properties_container = QWidget()
        properties_layout = QVBoxLayout()
        properties_label = QLabel("Properties")
        properties_label.setStyleSheet("font-weight: bold; background: #e0e0e0; padding: 5px;")
        self.properties = PropertiesPanel()
        properties_layout.addWidget(properties_label)
        properties_layout.addWidget(self.properties)
        properties_layout.setContentsMargins(0, 0, 0, 0)
        properties_container.setLayout(properties_layout)
        
        parameters_container = QWidget()
        parameters_layout = QVBoxLayout()
        parameters_label = QLabel("Settings and Parameters")
        parameters_label.setStyleSheet("font-weight: bold; background: #e0e0e0; padding: 5px;")
        self.parameters = ParametersPanel()
        parameters_layout.addWidget(parameters_label)
        parameters_layout.addWidget(self.parameters)
        parameters_layout.setContentsMargins(0, 0, 0, 0)
        parameters_container.setLayout(parameters_layout)
        
        right_splitter.addWidget(properties_container)
        right_splitter.addWidget(parameters_container)
        right_splitter.setSizes([400, 300])
        
        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(center_splitter)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([250, 800, 400])
        
        main_layout.addWidget(main_splitter)
        central.setLayout(main_layout)
        self.setCentralWidget(central)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def create_actions(self):
        """Create menu and toolbar actions"""
        # File actions
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
        
        self.export_action = QAction("Export as PKT...", self)
        self.export_action.triggered.connect(self.export_pkt)
        
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)
        
        # View actions
        self.restore_layout_action = QAction("Restore Default Layout", self)
        self.restore_layout_action.triggered.connect(self.restore_default_layout)
        
        # Help actions
        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.show_about)
        
    def create_menus(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction(self.restore_layout_action)
        
        # Define menu
        define_menu = menubar.addMenu("Define")
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction(self.about_action)
        
    def create_toolbars(self):
        """Create toolbars"""
        toolbar = QToolBar("Main Tools")
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        
        # Preview update button
        update_preview_btn = QAction("Update Preview", self)
        update_preview_btn.triggered.connect(self.update_preview)
        toolbar.addAction(update_preview_btn)
        
    def connect_signals(self):
        """Connect signals and slots"""
        self.toolbox.element_selected.connect(self.add_element_to_flowchart)
        self.show_codes_check.stateChanged.connect(self.toggle_codes)
        self.show_comments_check.stateChanged.connect(self.toggle_comments)
        self.flowchart.scene.node_selected.connect(self.on_flowchart_node_selected)
        
    def on_flowchart_node_selected(self, node):
        """Handle flowchart node selection"""
        self.properties.load_node(node)
        self.statusBar().showMessage(f"Selected: {node.type} - {node.name}")
        
    def add_element_to_flowchart(self, element_type):
        """Add element to flowchart"""
        if element_type == "Point":
            self.flowchart.add_point_node()
        elif element_type == "Link":
            self.flowchart.add_link_node()
        elif element_type == "Shape":
            self.flowchart.add_shape_node()
        elif element_type == "Decision":
            self.flowchart.add_decision_node()
            
        self.modified = True
        self.update_preview()
        
    def update_preview(self):
        """Update geometry preview"""
        self.preview.update_preview(self.flowchart.scene.nodes)
        
    def toggle_codes(self, state):
        """Toggle code display in preview"""
        self.preview.show_codes = (state == Qt.Checked)
        self.update_preview()
        
    def toggle_comments(self, state):
        """Toggle comment display in preview"""
        self.preview.show_comments = (state == Qt.Checked)
        self.update_preview()
        
    def new_file(self):
        """Create new component"""
        if self.check_save_changes():
            self.flowchart.scene.clear()
            self.flowchart.scene.nodes.clear()
            self.flowchart.node_counter = 0
            self.preview.scene.clear()
            self.preview.setup_scene()
            self.current_file = None
            self.modified = False
            self.statusBar().showMessage("New component created")
            
    def open_file(self):
        """Open existing PKT file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open PKT File", "", "PKT Files (*.pkt);;JSON Files (*.json)"
        )
        if filename:
            self.load_file(filename)
            
    def save_file(self):
        """Save current file"""
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_file_as()
            
    def save_file_as(self):
        """Save file with new name"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save As", "", "JSON Files (*.json)"
        )
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
            self.save_to_file(filename)
            self.current_file = filename
            
    def save_to_file(self, filename):
        """Save component to file"""
        data = {
            'component_settings': {
                'name': self.parameters.component_name.text(),
                'description': self.parameters.component_desc.toPlainText()
            },
            'nodes': {node_id: node.to_dict() for node_id, node in self.flowchart.scene.nodes.items()},
            'connections': self.flowchart.scene.connections
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        self.modified = False
        self.statusBar().showMessage(f"Saved: {filename}")
        
    def load_file(self, filename):
        """Load component from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Load component settings
            if 'component_settings' in data:
                self.parameters.component_name.setText(data['component_settings'].get('name', ''))
                self.parameters.component_desc.setPlainText(data['component_settings'].get('description', ''))
            elif 'packet_settings' in data:  # Backward compatibility
                self.parameters.component_name.setText(data['packet_settings'].get('name', ''))
                self.parameters.component_desc.setPlainText(data['packet_settings'].get('description', ''))
                
            # Load nodes
            self.flowchart.scene.clear()
            self.flowchart.scene.nodes.clear()
            
            # TODO: Reconstruct nodes from data
            
            self.current_file = filename
            self.modified = False
            self.statusBar().showMessage(f"Loaded: {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
            
    def export_pkt(self):
        """Export to PKT format"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export as PKT", "", "PKT Files (*.pkt)"
        )
        if filename:
            if not filename.endswith('.pkt'):
                filename += '.pkt'
            # TODO: Implement actual PKT export
            QMessageBox.information(self, "Information", 
                                   "PKT export functionality is under development.\n"
                                   "Please use JSON format for now.")
            
    def check_save_changes(self):
        """Check if changes need to be saved"""
        if self.modified:
            reply = QMessageBox.question(
                self, "Save Changes?",
                "The file has unsaved changes. Do you want to save them?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                self.save_file()
                return True
            elif reply == QMessageBox.Cancel:
                return False
        return True
        
    def restore_default_layout(self):
        """Restore default window layout"""
        # TODO: Implement layout restoration
        pass
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About",
            "Component Designer for FreeCAD Road Workbench\n\n"
            "An advanced tool for designing road cross-section components.\n\n"
            "Version 1.0"
        )
        
    def closeEvent(self, event):
        """Handle window close event"""
        if self.check_save_changes():
            event.accept()
        else:
            event.ignore()
