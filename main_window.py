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
from panels import ToolboxPanel
from models import PointNode, LinkNode, ShapeNode, DecisionNode
from flowchart import FlowchartNodeItem
from models import create_node_from_dict


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
        
        # Main horizontal splitter - only left and center now
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(center_splitter)
        main_splitter.setSizes([250, 800])
        
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
        self.flowchart.scene.preview_update_requested.connect(self.update_preview)
        
    def on_flowchart_node_selected(self, node):
        """Handle flowchart node selection"""
        self.statusBar().showMessage(f"Selected: {node.type} - {node.name}")
        # Sync selection to preview
        self.preview.select_node_visually(node)
        
    def sync_selection_from_preview(self, node):
        """Handle selection from preview - sync to flowchart"""
        self.statusBar().showMessage(f"Selected: {node.type} - {node.name}")
        # Sync selection to flowchart
        self.flowchart.select_node_visually(node)

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
            # Clear flowchart scene
            self.flowchart.scene.clear()
            self.flowchart.scene.nodes.clear()
            self.flowchart.scene.connections.clear()
            self.flowchart.scene.port_wires.clear()
            self.flowchart.scene.last_added_node = None
            
            # Reset counter
            self.flowchart.node_counter = 0
            
            # Clear preview
            self.preview.scene.clear()
            self.preview.setup_scene()
            
            # Create START node again
            self.flowchart.create_start_node()
            
            # Reset file info
            self.current_file = None
            self.modified = False
            self.statusBar().showMessage("New component created")
            
    def open_file(self):
        """Open existing JSON file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open JSON File", "", "JSON Files (*.json)"
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
            'nodes': [],
            'connections': []
        }
        
        # Save nodes in order
        for node_id, node in self.flowchart.scene.nodes.items():
            node_data = node.to_dict()
            data['nodes'].append(node_data)
        
        # Save connections
        data['connections'] = self.flowchart.scene.connections
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        self.modified = False
        self.statusBar().showMessage(f"Saved: {filename}")
        
    def load_file(self, filename):
        """Load component from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Clear existing flowchart
            self.flowchart.scene.clear()
            self.flowchart.scene.nodes.clear()
            self.flowchart.scene.connections.clear()
            self.flowchart.scene.port_wires.clear()
            self.flowchart.scene.last_added_node = None
            self.flowchart.node_counter = 0
            
            # Load nodes
            if 'nodes' in data:
                node_map = {}  # Map old IDs to new node objects
                last_non_start_node = None  # Track last non-start node
                
                for node_data in data['nodes']:
                    node = create_node_from_dict(node_data)
                    x = node_data.get('x', 0)
                    y = node_data.get('y', 0)
                    
                    # Add node without auto-connecting
                    self.flowchart.scene.nodes[node.id] = node
                    node.x = x
                    node.y = y
                    node_item = FlowchartNodeItem(node, x, y)
                    self.flowchart.scene.addItem(node_item)
                    
                    node_map[node.id] = node
                    
                    # Track last non-start node for continuation
                    from models import StartNode
                    if not isinstance(node, StartNode):
                        last_non_start_node = node
                    
                    # Update counter
                    if node.id.startswith('N'):
                        try:
                            num = int(node.id[1:])
                            if num > self.flowchart.node_counter:
                                self.flowchart.node_counter = num
                        except:
                            pass
                
                # Set last_added_node to continue chain
                self.flowchart.scene.last_added_node = last_non_start_node
            
            # Load connections
            if 'connections' in data:
                for conn in data['connections']:
                    from_id = conn['from']
                    to_id = conn['to']
                    from_port = conn.get('from_port', 'from')
                    to_port = conn.get('to_port', 'to')
                    
                    if from_id in node_map and to_id in node_map:
                        from_node = node_map[from_id]
                        to_node = node_map[to_id]
                        self.flowchart.scene.connect_nodes_with_wire(
                            from_node, to_node, from_port, to_port
                        )

            self.current_file = filename
            self.modified = False
            self.statusBar().showMessage(f"Loaded: {filename}")
            
            # Update preview
            self.update_preview()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
            import traceback
            traceback.print_exc()
            
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