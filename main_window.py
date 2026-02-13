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
from models import PointNode, LinkNode, ShapeNode, DecisionNode
from flowchart import FlowchartNodeItem


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
            'component_settings': {
                'name': self.parameters.component_name.text(),
                'description': self.parameters.component_desc.toPlainText()
            },
            'nodes': [],
            'connections': []
        }
        
        # Save nodes in order
        for node_id, node in self.flowchart.scene.nodes.items():
            node_data = {
                'id': node.id,
                'type': node.type,
                'name': node.name,
                'x': node.x,
                'y': node.y
            }
            
            # Add type-specific properties
            if isinstance(node, PointNode):
                node_data['geometry_type'] = node.geometry_type.value
                node_data['offset'] = node.offset
                node_data['elevation'] = node.elevation
                node_data['delta_x'] = node.delta_x
                node_data['delta_y'] = node.delta_y
                node_data['slope'] = node.slope
                node_data['from_point'] = node.from_point
                node_data['point_codes'] = node.point_codes
                node_data['add_link_to_from'] = node.add_link_to_from
                
            elif isinstance(node, LinkNode):
                node_data['link_type'] = node.link_type.value
                node_data['start_point'] = node.start_point
                node_data['end_point'] = node.end_point
                node_data['link_codes'] = node.link_codes
                node_data['material'] = node.material
                node_data['thickness'] = node.thickness
                
            elif isinstance(node, ShapeNode):
                node_data['shape_codes'] = node.shape_codes
                node_data['links'] = node.links
                node_data['material'] = node.material
                
            elif isinstance(node, DecisionNode):
                node_data['condition'] = node.condition
                
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
                
            # Load component settings
            if 'component_settings' in data:
                self.parameters.component_name.setText(data['component_settings'].get('name', ''))
                self.parameters.component_desc.setPlainText(data['component_settings'].get('description', ''))
                
            # Clear existing flowchart
            self.flowchart.scene.clear()
            self.flowchart.scene.nodes.clear()
            self.flowchart.scene.connections.clear()
            self.flowchart.scene.arrows.clear()
            self.flowchart.scene.last_added_node = None
            self.flowchart.node_counter = 0
            
            # Load nodes
            if 'nodes' in data:
                node_map = {}  # Map old IDs to new node objects
                
                for node_data in data['nodes']:
                    node = None
                    node_type = node_data.get('type')
                    
                    if node_type == 'Point':
                        from models import PointGeometryType
                        node = PointNode(node_data['id'], node_data['name'])
                        # Load geometry type
                        geo_type_str = node_data.get('geometry_type', 'Offset and Elevation')
                        for gt in PointGeometryType:
                            if gt.value == geo_type_str:
                                node.geometry_type = gt
                                break
                        node.offset = node_data.get('offset', 0.0)
                        node.elevation = node_data.get('elevation', 0.0)
                        node.delta_x = node_data.get('delta_x', 0.0)
                        node.delta_y = node_data.get('delta_y', 0.0)
                        node.slope = node_data.get('slope', 0.0)
                        node.from_point = node_data.get('from_point')
                        node.point_codes = node_data.get('point_codes', [])
                        node.add_link_to_from = node_data.get('add_link_to_from', True)
                        
                    elif node_type == 'Link':
                        from models import LinkType
                        node = LinkNode(node_data['id'], node_data['name'])
                        # Load link type
                        link_type_str = node_data.get('link_type', 'Line')
                        for lt in LinkType:
                            if lt.value == link_type_str:
                                node.link_type = lt
                                break
                        node.start_point = node_data.get('start_point')
                        node.end_point = node_data.get('end_point')
                        node.link_codes = node_data.get('link_codes', [])
                        node.material = node_data.get('material', 'Asphalt')
                        node.thickness = node_data.get('thickness', 0.0)
                        
                    elif node_type == 'Shape':
                        node = ShapeNode(node_data['id'], node_data['name'])
                        node.shape_codes = node_data.get('shape_codes', [])
                        node.links = node_data.get('links', [])
                        node.material = node_data.get('material', 'Asphalt')
                        
                    elif node_type == 'Decision':
                        node = DecisionNode(node_data['id'], node_data['name'])
                        node.condition = node_data.get('condition', '')
                        
                    elif node_type == 'Start':
                        from models import FlowchartNode
                        node = FlowchartNode(node_data['id'], node_type, node_data['name'])
                        
                    else:
                        # Generic node for other types
                        from models import FlowchartNode
                        node = FlowchartNode(node_data['id'], node_type, node_data['name'])
                    
                    if node:
                        x = node_data.get('x', 0)
                        y = node_data.get('y', 0)
                        
                        # Add node without auto-connecting
                        self.flowchart.scene.nodes[node.id] = node
                        node.x = x
                        node.y = y
                        node_item = FlowchartNodeItem(node, x, y)
                        self.flowchart.scene.addItem(node_item)
                        
                        node_map[node.id] = node
                        
                        # Update counter
                        if node.id.startswith('N'):
                            try:
                                num = int(node.id[1:])
                                if num > self.flowchart.node_counter:
                                    self.flowchart.node_counter = num
                            except:
                                pass
            
            # Load connections
            if 'connections' in data:
                for conn in data['connections']:
                    from_id = conn['from']
                    to_id = conn['to']
                    
                    if from_id in node_map and to_id in node_map:
                        from_node = node_map[from_id]
                        to_node = node_map[to_id]
                        self.flowchart.scene.connect_nodes(from_node, to_node)
            
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
