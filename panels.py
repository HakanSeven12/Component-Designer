"""
UI Panels for Component Designer
Contains Properties, Parameters, and Toolbox panels
"""
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                               QLineEdit, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit,
                               QPushButton, QTableWidget, QTableWidgetItem, QListWidget,
                               QTabWidget, QTreeWidget, QTreeWidgetItem, QAbstractItemView,
                               QApplication)
from PySide2.QtCore import Qt, Signal, QMimeData
from PySide2.QtGui import QDrag, QPainter, QPixmap, QPen, QColor

from models import (PointGeometryType, LinkType, ParameterType, TargetType,
                   PointNode, LinkNode, ShapeNode, DecisionNode,FlowchartNode)


class DraggableTreeWidget(QTreeWidget):
    """Custom tree widget with drag support"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.drag_start_position = None
        
    def mousePressEvent(self, event):
        """Handle mouse press to start drag"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move to perform drag"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if self.drag_start_position is None:
            return
            
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
            
        item = self.itemAt(self.drag_start_position)
        if item and item.parent():  # Only drag child items
            element_type = item.text(0)
            
            # Create mime data
            mime_data = QMimeData()
            mime_data.setText(element_type)
            
            # Create drag with pixmap
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # Create a simple pixmap for drag feedback
            pixmap = QPixmap(100, 40)
            pixmap.fill(QColor(200, 220, 255, 200))
            painter = QPainter(pixmap)
            painter.setPen(QPen(Qt.black))
            painter.drawRect(0, 0, 99, 39)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, element_type)
            painter.end()
            
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())
            
            # Execute drag
            drag.exec_(Qt.CopyAction)


class PropertiesPanel(QWidget):
    """Properties panel for editing selected node"""
    
    def __init__(self):
        super().__init__()
        self.current_node = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Node name
        name_group = QGroupBox("General")
        name_layout = QFormLayout()
        self.node_name = QLineEdit()
        name_layout.addRow("Name:", self.node_name)
        name_group.setLayout(name_layout)
        layout.addWidget(name_group)
        
        # Point properties
        self.point_group = QGroupBox("Point Geometry")
        point_layout = QFormLayout()
        
        self.geometry_type = QComboBox()
        for gt in PointGeometryType:
            self.geometry_type.addItem(gt.value, gt)
        
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-1000, 1000)
        self.offset_spin.setDecimals(3)
        
        self.elevation_spin = QDoubleSpinBox()
        self.elevation_spin.setRange(-1000, 1000)
        self.elevation_spin.setDecimals(3)
        
        self.delta_x_spin = QDoubleSpinBox()
        self.delta_x_spin.setRange(-1000, 1000)
        self.delta_x_spin.setDecimals(3)
        
        self.delta_y_spin = QDoubleSpinBox()
        self.delta_y_spin.setRange(-1000, 1000)
        self.delta_y_spin.setDecimals(3)
        
        self.slope_spin = QDoubleSpinBox()
        self.slope_spin.setRange(-10, 10)
        self.slope_spin.setDecimals(3)
        
        self.from_point_combo = QComboBox()
        self.add_link_check = QCheckBox("Add Link to From Point")
        
        self.point_codes_edit = QLineEdit()
        self.point_codes_edit.setPlaceholderText('"Code1","Code2"')
        
        point_layout.addRow("Geometry Type:", self.geometry_type)
        point_layout.addRow("Offset:", self.offset_spin)
        point_layout.addRow("Elevation:", self.elevation_spin)
        point_layout.addRow("Delta X:", self.delta_x_spin)
        point_layout.addRow("Delta Y:", self.delta_y_spin)
        point_layout.addRow("Slope:", self.slope_spin)
        point_layout.addRow("From Point:", self.from_point_combo)
        point_layout.addRow("", self.add_link_check)
        point_layout.addRow("Point Codes:", self.point_codes_edit)
        
        self.point_group.setLayout(point_layout)
        layout.addWidget(self.point_group)
        
        # Link properties
        self.link_group = QGroupBox("Link Properties")
        link_layout = QFormLayout()
        
        self.link_type_combo = QComboBox()
        for lt in LinkType:
            self.link_type_combo.addItem(lt.value, lt)
            
        self.start_point_combo = QComboBox()
        self.end_point_combo = QComboBox()
        
        self.link_codes_edit = QLineEdit()
        self.link_codes_edit.setPlaceholderText('"Top","Pave"')
        
        self.material_combo = QComboBox()
        self.material_combo.addItems(["Asphalt", "Concrete", "Granular", "Soil"])
        
        self.thickness_spin = QDoubleSpinBox()
        self.thickness_spin.setRange(0, 10)
        self.thickness_spin.setDecimals(3)
        self.thickness_spin.setSuffix(" m")
        
        link_layout.addRow("Link Type:", self.link_type_combo)
        link_layout.addRow("Start Point:", self.start_point_combo)
        link_layout.addRow("End Point:", self.end_point_combo)
        link_layout.addRow("Link Codes:", self.link_codes_edit)
        link_layout.addRow("Material:", self.material_combo)
        link_layout.addRow("Thickness:", self.thickness_spin)
        
        self.link_group.setLayout(link_layout)
        layout.addWidget(self.link_group)
        
        # Shape properties
        self.shape_group = QGroupBox("Shape Properties")
        shape_layout = QFormLayout()
        
        self.shape_codes_edit = QLineEdit()
        self.shape_codes_edit.setPlaceholderText('"Pave"')
        
        self.shape_links_list = QListWidget()
        self.add_link_to_shape_btn = QPushButton("Add Link")
        
        shape_layout.addRow("Shape Codes:", self.shape_codes_edit)
        shape_layout.addRow("Links:", self.shape_links_list)
        shape_layout.addRow("", self.add_link_to_shape_btn)
        
        self.shape_group.setLayout(shape_layout)
        layout.addWidget(self.shape_group)
        
        # Decision properties
        self.decision_group = QGroupBox("Decision Properties")
        decision_layout = QFormLayout()
        
        self.condition_edit = QTextEdit()
        self.condition_edit.setMaximumHeight(60)
        self.condition_edit.setPlaceholderText('e.g.: EG_Elevation > P1_Elevation')
        
        decision_layout.addRow("Condition:", self.condition_edit)
        
        self.decision_group.setLayout(decision_layout)
        layout.addWidget(self.decision_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Hide all groups initially
        self.point_group.hide()
        self.link_group.hide()
        self.shape_group.hide()
        self.decision_group.hide()
        
        # Connect signals for property changes
        self.connect_property_signals()

    def connect_property_signals(self):
        """Connect property change signals"""
        # Point properties
        self.node_name.textChanged.connect(self.on_name_changed)
        self.geometry_type.currentIndexChanged.connect(self.on_geometry_type_changed)
        self.offset_spin.valueChanged.connect(self.on_offset_changed)
        self.elevation_spin.valueChanged.connect(self.on_elevation_changed)
        self.delta_x_spin.valueChanged.connect(self.on_delta_x_changed)
        self.delta_y_spin.valueChanged.connect(self.on_delta_y_changed)
        self.slope_spin.valueChanged.connect(self.on_slope_changed)
        self.from_point_combo.currentIndexChanged.connect(self.on_from_point_changed)
        self.add_link_check.stateChanged.connect(self.on_add_link_changed)
        self.point_codes_edit.textChanged.connect(self.on_point_codes_changed)
        
        # Link properties
        self.link_type_combo.currentIndexChanged.connect(self.on_link_type_changed)
        self.start_point_combo.currentIndexChanged.connect(self.on_start_point_changed)
        self.end_point_combo.currentIndexChanged.connect(self.on_end_point_changed)
        self.link_codes_edit.textChanged.connect(self.on_link_codes_changed)
        self.material_combo.currentTextChanged.connect(self.on_material_changed)
        self.thickness_spin.valueChanged.connect(self.on_thickness_changed)
        
        # Shape properties
        self.shape_codes_edit.textChanged.connect(self.on_shape_codes_changed)
        
        # Decision properties
        self.condition_edit.textChanged.connect(self.on_condition_changed)

    def block_all_signals(self, block):
        """Block or unblock all widget signals"""
        # Point widgets
        self.node_name.blockSignals(block)
        self.geometry_type.blockSignals(block)
        self.offset_spin.blockSignals(block)
        self.elevation_spin.blockSignals(block)
        self.delta_x_spin.blockSignals(block)
        self.delta_y_spin.blockSignals(block)
        self.slope_spin.blockSignals(block)
        self.from_point_combo.blockSignals(block)
        self.add_link_check.blockSignals(block)
        self.point_codes_edit.blockSignals(block)
        
        # Link widgets
        self.link_type_combo.blockSignals(block)
        self.start_point_combo.blockSignals(block)
        self.end_point_combo.blockSignals(block)
        self.link_codes_edit.blockSignals(block)
        self.material_combo.blockSignals(block)
        self.thickness_spin.blockSignals(block)
        
        # Shape widgets
        self.shape_codes_edit.blockSignals(block)
        
        # Decision widgets
        self.condition_edit.blockSignals(block)

    def on_name_changed(self, text):
        """Handle name change"""
        if self.current_node:
            self.current_node.name = text
            self.update_flowchart_display()
            self.update_preview()
            
    def on_geometry_type_changed(self, index):
        """Handle geometry type change"""
        if self.current_node and isinstance(self.current_node, PointNode):
            self.current_node.geometry_type = self.geometry_type.currentData()
            self.update_preview()
            
    def on_offset_changed(self, value):
        """Handle offset change"""
        if self.current_node and isinstance(self.current_node, PointNode):
            self.current_node.offset = value
            self.update_preview()
            
    def on_elevation_changed(self, value):
        """Handle elevation change"""
        if self.current_node and isinstance(self.current_node, PointNode):
            self.current_node.elevation = value
            self.update_preview()
            
    def on_delta_x_changed(self, value):
        """Handle delta X change"""
        if self.current_node and isinstance(self.current_node, PointNode):
            self.current_node.delta_x = value
            self.update_preview()
            
    def on_delta_y_changed(self, value):
        """Handle delta Y change"""
        if self.current_node and isinstance(self.current_node, PointNode):
            self.current_node.delta_y = value
            self.update_preview()
            
    def on_slope_changed(self, value):
        """Handle slope change"""
        if self.current_node and isinstance(self.current_node, PointNode):
            self.current_node.slope = value
            self.update_preview()
            
    def on_from_point_changed(self, index):
        """Handle from point change"""
        if self.current_node and isinstance(self.current_node, PointNode):
            self.current_node.from_point = self.from_point_combo.currentData()
            self.update_preview()
            
    def on_add_link_changed(self, state):
        """Handle add link checkbox change"""
        if self.current_node and isinstance(self.current_node, PointNode):
            self.current_node.add_link_to_from = (state == Qt.Checked)
            self.update_preview()
            
    def on_link_type_changed(self, index):
        """Handle link type change"""
        if self.current_node and isinstance(self.current_node, LinkNode):
            self.current_node.link_type = self.link_type_combo.currentData()
            self.update_preview()
            
    def on_start_point_changed(self, index):
        """Handle start point change"""
        if self.current_node and isinstance(self.current_node, LinkNode):
            self.current_node.start_point = self.start_point_combo.currentData()
            self.update_preview()
            
    def on_end_point_changed(self, index):
        """Handle end point change"""
        if self.current_node and isinstance(self.current_node, LinkNode):
            self.current_node.end_point = self.end_point_combo.currentData()
            self.update_preview()
            
    def on_material_changed(self, text):
        """Handle material change"""
        if self.current_node and isinstance(self.current_node, LinkNode):
            self.current_node.material = text
            self.update_preview()
            
    def on_thickness_changed(self, value):
        """Handle thickness change"""
        if self.current_node and isinstance(self.current_node, LinkNode):
            self.current_node.thickness = value
            self.update_preview()
            
    def on_point_codes_changed(self, text):
        """Handle point codes change"""
        if self.current_node and isinstance(self.current_node, PointNode):
            # Parse comma-separated quoted strings
            import re
            codes = re.findall(r'"([^"]*)"', text)
            self.current_node.point_codes = codes
            self.update_preview()
            
    def on_link_codes_changed(self, text):
        """Handle link codes change"""
        if self.current_node and isinstance(self.current_node, LinkNode):
            # Parse comma-separated quoted strings
            import re
            codes = re.findall(r'"([^"]*)"', text)
            self.current_node.link_codes = codes
            self.update_preview()
            
    def on_shape_codes_changed(self, text):
        """Handle shape codes change"""
        if self.current_node and isinstance(self.current_node, ShapeNode):
            # Parse comma-separated quoted strings
            import re
            codes = re.findall(r'"([^"]*)"', text)
            self.current_node.shape_codes = codes
            self.update_preview()
            
    def on_condition_changed(self):
        """Handle condition change"""
        if self.current_node and isinstance(self.current_node, DecisionNode):
            self.current_node.condition = self.condition_edit.toPlainText()
            self.update_preview()
            
    def update_flowchart_display(self):
        """Update flowchart visual display"""
        flowchart_scene = self.get_flowchart_scene()
        if not flowchart_scene:
            return
            
        # Update the visual representation of nodes
        for item in flowchart_scene.items():
            if isinstance(item, FlowchartNode):
                if item.node == self.current_node:
                    # Update text display
                    item.text.setPlainText(f"{item.node.type}\n{item.node.name}")
                    # Re-center text
                    text_rect = item.text.boundingRect()
                    text_x = (120 - text_rect.width()) / 2
                    text_y = (60 - text_rect.height()) / 2
                    item.text.setPos(text_x, text_y)
                    break

    def load_node(self, node):
        """Load node properties into panel"""
        self.current_node = node
        
        # Hide all groups
        self.point_group.hide()
        self.link_group.hide()
        self.shape_group.hide()
        self.decision_group.hide()
        
        if node is None:
            return
        
        # Temporarily block signals while loading
        self.blockSignals(True)
        self.block_all_signals(True)
        
        self.node_name.setText(node.name)
        
        # Update combo boxes with available nodes from flowchart
        self.update_node_combos()
        
        if isinstance(node, PointNode):
            self.point_group.show()
            # Load point properties
            index = self.geometry_type.findData(node.geometry_type)
            if index >= 0:
                self.geometry_type.setCurrentIndex(index)
            self.offset_spin.setValue(node.offset)
            self.elevation_spin.setValue(node.elevation)
            self.delta_x_spin.setValue(node.delta_x)
            self.delta_y_spin.setValue(node.delta_y)
            self.slope_spin.setValue(node.slope)
            self.add_link_check.setChecked(node.add_link_to_from)
            self.point_codes_edit.setText(','.join(f'"{c}"' for c in node.point_codes))
            
            # Set from_point if exists
            if node.from_point:
                index = self.from_point_combo.findData(node.from_point)
                if index >= 0:
                    self.from_point_combo.setCurrentIndex(index)
                else:
                    self.from_point_combo.setCurrentIndex(0)  # Set to "(None)"
            else:
                self.from_point_combo.setCurrentIndex(0)  # Set to "(None)"
            
        elif isinstance(node, LinkNode):
            self.link_group.show()
            # Load link properties
            index = self.link_type_combo.findData(node.link_type)
            if index >= 0:
                self.link_type_combo.setCurrentIndex(index)
            self.link_codes_edit.setText(','.join(f'"{c}"' for c in node.link_codes))
            self.material_combo.setCurrentText(node.material)
            self.thickness_spin.setValue(node.thickness)
            
            # Set start_point and end_point if exist
            if node.start_point:
                index = self.start_point_combo.findData(node.start_point)
                if index >= 0:
                    self.start_point_combo.setCurrentIndex(index)
                else:
                    self.start_point_combo.setCurrentIndex(0)  # Set to "(None)"
            else:
                self.start_point_combo.setCurrentIndex(0)  # Set to "(None)"
                
            if node.end_point:
                index = self.end_point_combo.findData(node.end_point)
                if index >= 0:
                    self.end_point_combo.setCurrentIndex(index)
                else:
                    self.end_point_combo.setCurrentIndex(0)  # Set to "(None)"
            else:
                self.end_point_combo.setCurrentIndex(0)  # Set to "(None)"
            
        elif isinstance(node, ShapeNode):
            self.shape_group.show()
            # Load shape properties
            self.shape_codes_edit.setText(','.join(f'"{c}"' for c in node.shape_codes))
            
        elif isinstance(node, DecisionNode):
            self.decision_group.show()
            # Load decision properties
            self.condition_edit.setText(node.condition)
        
        # Re-enable signals
        self.block_all_signals(False)
        self.blockSignals(False)

    def update_node_combos(self):
        """Update combo boxes with nodes from flowchart"""
        if not self.current_node:
            return
            
        # Get flowchart scene from parent hierarchy
        flowchart_scene = self.get_flowchart_scene()
        if not flowchart_scene:
            return
            
        # Clear combo boxes
        self.from_point_combo.clear()
        self.start_point_combo.clear()
        self.end_point_combo.clear()
        
        # Add "None" option
        self.from_point_combo.addItem("(None)", None)
        self.start_point_combo.addItem("(None)", None)
        self.end_point_combo.addItem("(None)", None)
        
        # Get all nodes that were added before current node
        nodes_before = []
        for node_id, node in flowchart_scene.nodes.items():
            # Only add nodes that come before current node
            if node.id == self.current_node.id:
                break
            nodes_before.append(node)
        
        # Add Point nodes to point combos
        for node in nodes_before:
            if isinstance(node, PointNode):
                display_name = f"{node.name} ({node.type})"
                self.from_point_combo.addItem(display_name, node.id)
                self.start_point_combo.addItem(display_name, node.id)
                self.end_point_combo.addItem(display_name, node.id)
                
    def get_flowchart_scene(self):
        """Get flowchart scene from main window"""
        # Traverse up the widget hierarchy to find main window
        widget = self.parentWidget()
        while widget:
            if hasattr(widget, 'flowchart'):
                return widget.flowchart.scene
            widget = widget.parentWidget()
        return None
    
    def update_preview(self):
        """Trigger preview update in main window"""
        # Get main window
        widget = self.parentWidget()
        while widget:
            if hasattr(widget, 'update_preview'):
                widget.update_preview()
                break
            widget = widget.parentWidget()
    

class ParametersPanel(QWidget):
    """Panel for managing Input/Output and Target parameters"""
    
    def __init__(self):
        super().__init__()
        self.input_output_params = []
        self.target_params = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Tab widget for different parameter types
        tabs = QTabWidget()
        
        # Component Settings tab
        component_tab = QWidget()
        component_layout = QFormLayout()
        self.component_name = QLineEdit()
        self.component_desc = QTextEdit()
        self.component_desc.setMaximumHeight(80)
        component_layout.addRow("Component Name:", self.component_name)
        component_layout.addRow("Description:", self.component_desc)
        component_tab.setLayout(component_layout)
        
        # Input/Output Parameters tab
        io_tab = QWidget()
        io_layout = QVBoxLayout()
        
        self.io_table = QTableWidget(0, 5)
        self.io_table.setHorizontalHeaderLabels(["Name", "Type", "Direction", "Default", "Display Name"])
        self.io_table.horizontalHeader().setStretchLastSection(True)
        
        io_buttons = QHBoxLayout()
        add_io_btn = QPushButton("Add Parameter")
        add_io_btn.clicked.connect(self.add_io_parameter)
        remove_io_btn = QPushButton("Remove Parameter")
        remove_io_btn.clicked.connect(self.remove_io_parameter)
        io_buttons.addWidget(add_io_btn)
        io_buttons.addWidget(remove_io_btn)
        io_buttons.addStretch()
        
        io_layout.addWidget(self.io_table)
        io_layout.addLayout(io_buttons)
        io_tab.setLayout(io_layout)
        
        # Target Parameters tab
        target_tab = QWidget()
        target_layout = QVBoxLayout()
        
        self.target_table = QTableWidget(0, 3)
        self.target_table.setHorizontalHeaderLabels(["Name", "Type", "Preview Value"])
        self.target_table.horizontalHeader().setStretchLastSection(True)
        
        target_buttons = QHBoxLayout()
        add_target_btn = QPushButton("Add Target")
        add_target_btn.clicked.connect(self.add_target_parameter)
        remove_target_btn = QPushButton("Remove Target")
        remove_target_btn.clicked.connect(self.remove_target_parameter)
        target_buttons.addWidget(add_target_btn)
        target_buttons.addWidget(remove_target_btn)
        target_buttons.addStretch()
        
        target_layout.addWidget(self.target_table)
        target_layout.addLayout(target_buttons)
        target_tab.setLayout(target_layout)
        
        tabs.addTab(component_tab, "Component Settings")
        tabs.addTab(io_tab, "I/O Parameters")
        tabs.addTab(target_tab, "Target Parameters")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
        
    def add_io_parameter(self):
        """Add new Input/Output parameter"""
        row = self.io_table.rowCount()
        self.io_table.insertRow(row)
        
        # Name
        name_item = QTableWidgetItem(f"Parameter{row+1}")
        self.io_table.setItem(row, 0, name_item)
        
        # Type
        type_combo = QComboBox()
        for pt in ParameterType:
            type_combo.addItem(pt.value, pt)
        self.io_table.setCellWidget(row, 1, type_combo)
        
        # Direction
        dir_combo = QComboBox()
        dir_combo.addItems(["Input", "Output", "InputOutput"])
        self.io_table.setCellWidget(row, 2, dir_combo)
        
        # Default value
        default_item = QTableWidgetItem("0.0")
        self.io_table.setItem(row, 3, default_item)
        
        # Display name
        display_item = QTableWidgetItem(f"Parameter {row+1}")
        self.io_table.setItem(row, 4, display_item)
        
    def remove_io_parameter(self):
        """Remove selected I/O parameter"""
        current_row = self.io_table.currentRow()
        if current_row >= 0:
            self.io_table.removeRow(current_row)
            
    def add_target_parameter(self):
        """Add new Target parameter"""
        row = self.target_table.rowCount()
        self.target_table.insertRow(row)
        
        # Name
        name_item = QTableWidgetItem(f"TargetParameter{row+1}")
        self.target_table.setItem(row, 0, name_item)
        
        # Type
        type_combo = QComboBox()
        for tt in TargetType:
            type_combo.addItem(tt.value, tt)
        self.target_table.setCellWidget(row, 1, type_combo)
        
        # Preview value
        preview_item = QTableWidgetItem("-1.0")
        self.target_table.setItem(row, 2, preview_item)
        
    def remove_target_parameter(self):
        """Remove selected target parameter"""
        current_row = self.target_table.currentRow()
        if current_row >= 0:
            self.target_table.removeRow(current_row)


class ToolboxPanel(QWidget):
    """Toolbox panel with geometry elements"""
    
    element_selected = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Category tree - use custom draggable tree
        self.tree = DraggableTreeWidget()
        self.tree.setHeaderLabel("Toolbox")
        
        # Geometry category
        geometry = QTreeWidgetItem(["Geometry"])
        geometry.addChild(QTreeWidgetItem(["Point"]))
        geometry.addChild(QTreeWidgetItem(["Link"]))
        geometry.addChild(QTreeWidgetItem(["Shape"]))
        self.tree.addTopLevelItem(geometry)
        
        # Advanced Geometry
        advanced = QTreeWidgetItem(["Advanced Geometry"])
        advanced.addChild(QTreeWidgetItem(["Arc Point"]))
        advanced.addChild(QTreeWidgetItem(["Parabola Point"]))
        self.tree.addTopLevelItem(advanced)
        
        # Auxiliary
        auxiliary = QTreeWidgetItem(["Auxiliary"])
        auxiliary.addChild(QTreeWidgetItem(["Auxiliary Point"]))
        auxiliary.addChild(QTreeWidgetItem(["Auxiliary Line"]))
        auxiliary.addChild(QTreeWidgetItem(["Auxiliary Curve"]))
        self.tree.addTopLevelItem(auxiliary)
        
        # Workflow
        workflow = QTreeWidgetItem(["Workflow"])
        workflow.addChild(QTreeWidgetItem(["Decision"]))
        workflow.addChild(QTreeWidgetItem(["Switch"]))
        workflow.addChild(QTreeWidgetItem(["Variable"]))
        self.tree.addTopLevelItem(workflow)
        
        # Miscellaneous
        misc = QTreeWidgetItem(["Miscellaneous"])
        misc.addChild(QTreeWidgetItem(["Mark Point"]))
        misc.addChild(QTreeWidgetItem(["Comment"]))
        self.tree.addTopLevelItem(misc)
        
        self.tree.expandAll()
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        layout.addWidget(self.tree)
        self.setLayout(layout)
        
    def on_item_double_clicked(self, item, column):
        """Handle element double-click"""
        if item.parent():  # Is a child item
            element_type = item.text(0)
            self.element_selected.emit(element_type)
