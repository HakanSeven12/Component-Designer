"""
UI Panels for Component Designer
Contains Properties, Parameters, and Toolbox panels
"""
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                               QLineEdit, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit,
                               QPushButton, QTableWidget, QTableWidgetItem, QListWidget,
                               QTabWidget, QTreeWidget, QTreeWidgetItem, QAbstractItemView,
                               QApplication, QScrollArea)
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
        self.property_widgets = {}
        self.widget_connections = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup basic UI structure"""
        main_layout = QVBoxLayout()
        
        # Scroll area for properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        # Container for dynamic content
        self.container = QWidget()
        self.container_layout = QVBoxLayout()
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container.setLayout(self.container_layout)
        
        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)
        
        self.setLayout(main_layout)
        
    def load_node(self, node):
        """Load node properties dynamically"""
        if node is None:
            self.clear_properties()
            return
        
        self.current_node = node
        self.clear_properties()
        
        # Create general group
        general_group = QGroupBox("General")
        general_layout = QFormLayout()
        
        # Node name (always present)
        self.node_name = QLineEdit()
        self.node_name.setText(node.name)
        self.node_name.textChanged.connect(self.on_name_changed)
        general_layout.addRow("Name:", self.node_name)
        
        general_group.setLayout(general_layout)
        self.container_layout.addWidget(general_group)
        
        # Get node-specific widgets
        try:
            widgets_info = node.get_properties_widgets(self.container)
        except NotImplementedError:
            # Node doesn't implement properties
            self.container_layout.addStretch()
            return
        
        if not widgets_info:
            self.container_layout.addStretch()
            return
        
        # Create properties group
        properties_group = QGroupBox(f"{node.type} Properties")
        properties_layout = QFormLayout()
        
        self.property_widgets = {}
        
        for prop_name, widget_info in widgets_info.items():
            widget = widget_info['widget']
            label = widget_info['label']
            getter = widget_info['getter']
            setter = widget_info['setter']
            
            # Store widget info
            self.property_widgets[prop_name] = {
                'widget': widget,
                'getter': getter,
                'setter': setter,
                'node_attr': prop_name
            }
            
            # Set initial value from node
            if hasattr(node, prop_name):
                try:
                    setter(getattr(node, prop_name))
                except:
                    pass
            
            # Check if this widget needs population (like combo boxes with point list)
            if 'populate' in widget_info and widget_info['populate'] == 'points':
                self.populate_point_combo(widget)
            
            # Connect to update handler
            self.connect_widget_signal(widget, prop_name)
            
            # Add to layout
            if label:
                properties_layout.addRow(label, widget)
            else:
                properties_layout.addRow(widget)
        
        properties_group.setLayout(properties_layout)
        self.container_layout.addWidget(properties_group)
        self.container_layout.addStretch()
        
    def connect_widget_signal(self, widget, prop_name):
        """Connect appropriate signal based on widget type"""
        from PySide2.QtWidgets import (QComboBox, QDoubleSpinBox, QSpinBox, 
                                        QLineEdit, QCheckBox, QTextEdit)
        
        if isinstance(widget, QComboBox):
            connection = widget.currentIndexChanged.connect(
                lambda: self.on_property_changed(prop_name)
            )
        elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
            connection = widget.valueChanged.connect(
                lambda: self.on_property_changed(prop_name)
            )
        elif isinstance(widget, QLineEdit):
            connection = widget.textChanged.connect(
                lambda: self.on_property_changed(prop_name)
            )
        elif isinstance(widget, QCheckBox):
            connection = widget.stateChanged.connect(
                lambda: self.on_property_changed(prop_name)
            )
        elif isinstance(widget, QTextEdit):
            connection = widget.textChanged.connect(
                lambda: self.on_property_changed(prop_name)
            )
        
        self.widget_connections.append(connection)
    
    def on_name_changed(self, text):
        """Handle node name change"""
        if self.current_node:
            self.current_node.name = text
            self.update_flowchart_display()
            self.update_preview()
    
    def on_property_changed(self, prop_name):
        """Handle property value change"""
        if not self.current_node:
            return
        
        widget_info = self.property_widgets.get(prop_name)
        if not widget_info:
            return
        
        # Get value from widget using getter
        try:
            value = widget_info['getter']()
            
            # Set value on node
            if hasattr(self.current_node, prop_name):
                setattr(self.current_node, prop_name, value)
            
            # Trigger updates
            self.update_preview()
            
        except Exception as e:
            print(f"Error updating property {prop_name}: {e}")
    
    def populate_point_combo(self, combo):
        """Populate combo box with available points"""
        flowchart_scene = self.get_flowchart_scene()
        if not flowchart_scene or not self.current_node:
            return
        
        combo.clear()
        combo.addItem("(None)", None)
        
        # Get nodes before current node
        from models import PointNode
        for node_id, node in flowchart_scene.nodes.items():
            if node.id == self.current_node.id:
                break
            if isinstance(node, PointNode):
                display_name = f"{node.name} ({node.type})"
                combo.addItem(display_name, node.id)
    
    def clear_properties(self):
        """Clear all dynamic property widgets"""
        # Disconnect all signals
        for connection in self.widget_connections:
            try:
                connection.disconnect()
            except:
                pass
        self.widget_connections.clear()
        
        # Clear widgets
        self.property_widgets.clear()
        
        # Remove all widgets from container
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def get_flowchart_scene(self):
        """Get flowchart scene from main window"""
        widget = self.parentWidget()
        while widget:
            if hasattr(widget, 'flowchart'):
                return widget.flowchart.scene
            widget = widget.parentWidget()
        return None
    
    def update_flowchart_display(self):
        """Update flowchart visual display"""
        flowchart_scene = self.get_flowchart_scene()
        if not flowchart_scene:
            return
        
        # Update the visual representation
        from flowchart import FlowchartNodeItem
        for item in flowchart_scene.items():
            if isinstance(item, FlowchartNodeItem):
                if item.node == self.current_node:
                    # Update text display
                    item.text.setPlainText(self.current_node.get_flowchart_display_text())
                    # Re-center text
                    text_rect = item.text.boundingRect()
                    text_x = (120 - text_rect.width()) / 2
                    text_y = (60 - text_rect.height()) / 2
                    item.text.setPos(text_x, text_y)
                    break
    
    def update_preview(self):
        """Trigger preview update in main window"""
        widget = self.parentWidget()
        while widget:
            if hasattr(widget, 'update_preview'):
                widget.update_preview()
                break
            widget = widget.parentWidget()

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
