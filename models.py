"""
Data Models for Component Designer
Improved architecture with node-specific behavior encapsulation
"""
from enum import Enum
from abc import ABC, abstractmethod


class PointGeometryType(Enum):
    """Point geometry definition methods"""
    OFFSET_ELEVATION = "Offset and Elevation"
    DELTA_XY = "Delta X and Y"
    DELTA_X_SLOPE = "Delta X and Slope"
    DELTA_Y_SLOPE = "Delta Y and Slope"
    DELTA_X_SURFACE = "Delta X on Surface"
    OFFSET_TARGET = "Offset to Target"
    ELEVATION_TARGET = "Elevation to Target"


class LinkType(Enum):
    """Link types"""
    LINE = "Line"
    ARC = "Arc"
    PARABOLA = "Parabola"


class TargetType(Enum):
    """Target parameter types"""
    SURFACE = "Surface"
    ALIGNMENT = "Alignment"
    PROFILE = "Profile"
    OFFSET = "Offset"
    ELEVATION = "Elevation"


class ParameterType(Enum):
    """Parameter types"""
    DISTANCE = "Distance"
    SLOPE = "Slope"
    WIDTH = "Width"
    DEPTH = "Depth"
    ANGLE = "Angle"
    NUMBER = "Number"


class FlowchartNode(ABC):
    """Base class for flowchart nodes with common behavior"""
    
    def __init__(self, node_id, node_type, name=""):
        self.id = node_id
        self.type = node_type
        self.name = name
        self.x = 0
        self.y = 0
        self.properties = {}
        self.next_nodes = []
        
    def to_dict(self):
        """Convert node to dictionary for serialization"""
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'properties': self.properties
        }
    
    @abstractmethod
    def get_properties_widgets(self, parent_widget):
        """Return dict of property name -> widget for properties panel
        
        Returns:
            dict: {
                'property_name': {
                    'label': 'Display Label',
                    'widget': QWidget instance,
                    'getter': lambda: value,
                    'setter': lambda value: None
                }
            }
        """
        pass
    
    @abstractmethod
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Create preview graphics items for this node
        
        Args:
            scene: QGraphicsScene to add items to
            scale_factor: Scale factor for preview
            show_codes: Whether to show code labels
            point_positions: Dict of node_id -> (x, y) positions
            
        Returns:
            list: List of created QGraphicsItem instances with data(0) set to self
        """
        pass
    
    @abstractmethod
    def get_preview_display_color(self):
        """Get the color used for displaying this node type in preview
        
        Returns:
            QColor: Color for this node type
        """
        pass
    
    def get_flowchart_display_text(self):
        """Get text to display in flowchart node
        
        Returns:
            str: Display text (default: type\\nname)
        """
        return f"{self.type}\n{self.name}"
    
    @classmethod
    def from_dict(cls, data):
        """Create node instance from dictionary
        
        Args:
            data: Dictionary with node data
            
        Returns:
            FlowchartNode: New node instance
        """
        # This should be overridden by subclasses for proper deserialization
        node = cls(data['id'], data.get('name', ''))
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        node.properties = data.get('properties', {})
        return node


class PointNode(FlowchartNode):
    """Point geometry node"""
    
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Point", name)
        self.geometry_type = PointGeometryType.OFFSET_ELEVATION
        self.offset = 0.0
        self.elevation = 0.0
        self.delta_x = 0.0
        self.delta_y = 0.0
        self.slope = 0.0
        self.from_point = None
        self.point_codes = []
        self.add_link_to_from = True
        self.computed_x = 0.0
        self.computed_y = 0.0
        
    def compute_position(self, from_point_pos=None):
        """Compute point position based on geometry type"""
        if self.geometry_type == PointGeometryType.OFFSET_ELEVATION:
            self.computed_x = self.offset
            self.computed_y = self.elevation
        elif self.geometry_type == PointGeometryType.DELTA_XY:
            if from_point_pos:
                self.computed_x = from_point_pos[0] + self.delta_x
                self.computed_y = from_point_pos[1] + self.delta_y
        elif self.geometry_type == PointGeometryType.DELTA_X_SLOPE:
            if from_point_pos:
                self.computed_x = from_point_pos[0] + self.delta_x
                self.computed_y = from_point_pos[1] + (self.delta_x * self.slope)
                
        return (self.computed_x, self.computed_y)
    
    def get_properties_widgets(self, parent_widget):
        """Return property widgets for Point node"""
        from PySide2.QtWidgets import QComboBox, QDoubleSpinBox, QCheckBox, QLineEdit
        
        widgets = {}
        
        # Geometry type
        geometry_combo = QComboBox(parent_widget)
        for gt in PointGeometryType:
            geometry_combo.addItem(gt.value, gt)
        widgets['geometry_type'] = {
            'label': 'Geometry Type:',
            'widget': geometry_combo,
            'getter': lambda: geometry_combo.currentData(),
            'setter': lambda v: geometry_combo.setCurrentIndex(geometry_combo.findData(v))
        }
        
        # Offset
        offset_spin = QDoubleSpinBox(parent_widget)
        offset_spin.setRange(-1000, 1000)
        offset_spin.setDecimals(3)
        widgets['offset'] = {
            'label': 'Offset:',
            'widget': offset_spin,
            'getter': lambda: offset_spin.value(),
            'setter': lambda v: offset_spin.setValue(v)
        }
        
        # Elevation
        elevation_spin = QDoubleSpinBox(parent_widget)
        elevation_spin.setRange(-1000, 1000)
        elevation_spin.setDecimals(3)
        widgets['elevation'] = {
            'label': 'Elevation:',
            'widget': elevation_spin,
            'getter': lambda: elevation_spin.value(),
            'setter': lambda v: elevation_spin.setValue(v)
        }
        
        # Delta X
        delta_x_spin = QDoubleSpinBox(parent_widget)
        delta_x_spin.setRange(-1000, 1000)
        delta_x_spin.setDecimals(3)
        widgets['delta_x'] = {
            'label': 'Delta X:',
            'widget': delta_x_spin,
            'getter': lambda: delta_x_spin.value(),
            'setter': lambda v: delta_x_spin.setValue(v)
        }
        
        # Delta Y
        delta_y_spin = QDoubleSpinBox(parent_widget)
        delta_y_spin.setRange(-1000, 1000)
        delta_y_spin.setDecimals(3)
        widgets['delta_y'] = {
            'label': 'Delta Y:',
            'widget': delta_y_spin,
            'getter': lambda: delta_y_spin.value(),
            'setter': lambda v: delta_y_spin.setValue(v)
        }
        
        # Slope
        slope_spin = QDoubleSpinBox(parent_widget)
        slope_spin.setRange(-10, 10)
        slope_spin.setDecimals(3)
        widgets['slope'] = {
            'label': 'Slope:',
            'widget': slope_spin,
            'getter': lambda: slope_spin.value(),
            'setter': lambda v: slope_spin.setValue(v)
        }
        
        # From Point (combo will be populated by properties panel)
        from_point_combo = QComboBox(parent_widget)
        widgets['from_point'] = {
            'label': 'From Point:',
            'widget': from_point_combo,
            'getter': lambda: from_point_combo.currentData(),
            'setter': lambda v: from_point_combo.setCurrentIndex(from_point_combo.findData(v)),
            'populate': 'points'  # Signal that this needs point list
        }
        
        # Add link to from
        add_link_check = QCheckBox("Add Link to From Point", parent_widget)
        widgets['add_link_to_from'] = {
            'label': '',
            'widget': add_link_check,
            'getter': lambda: add_link_check.isChecked(),
            'setter': lambda v: add_link_check.setChecked(v)
        }
        
        # Point codes
        codes_edit = QLineEdit(parent_widget)
        codes_edit.setPlaceholderText('"Code1","Code2"')
        widgets['point_codes'] = {
            'label': 'Point Codes:',
            'widget': codes_edit,
            'getter': lambda: self._parse_codes(codes_edit.text()),
            'setter': lambda v: codes_edit.setText(','.join(f'"{c}"' for c in v))
        }
        
        return widgets
    
    def _parse_codes(self, text):
        """Parse comma-separated quoted strings"""
        import re
        return re.findall(r'"([^"]*)"', text)
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Create preview items for point"""
        from PySide2.QtGui import QFont, QColor, QPen, QBrush
        from PySide2.QtCore import Qt
        
        # Import here to avoid circular dependency
        import sys
        if '/home/claude' not in sys.path:
            sys.path.insert(0, '/home/claude')
        
        items = []
        
        # Compute position
        from_pos = None
        if self.from_point and self.from_point in point_positions:
            from_pos = point_positions[self.from_point]
        
        pos = self.compute_position(from_pos)
        point_positions[self.id] = pos
        
        x = pos[0] * scale_factor
        y = -pos[1] * scale_factor
        
        # Import PreviewPointItem and PreviewTextItem
        from preview import PreviewPointItem, PreviewTextItem
        
        # Create point
        point_item = PreviewPointItem(x, y, self)
        items.append(point_item)
        
        # Add name
        name_text = PreviewTextItem(self.name, self)
        name_font = QFont()
        name_font.setPointSize(8)
        name_font.setBold(True)
        name_text.setFont(name_font)
        name_text.setPos(x + 8, y - 25)
        name_text.setDefaultTextColor(QColor(0, 0, 180))
        items.append(name_text)
        
        # Add codes if enabled
        if show_codes and self.point_codes:
            code_text = PreviewTextItem(f"[{','.join(self.point_codes)}]", self)
            code_font = QFont()
            code_font.setPointSize(7)
            code_text.setFont(code_font)
            code_text.setPos(x + 8, y - 10)
            code_text.setDefaultTextColor(QColor(0, 0, 255))
            items.append(code_text)
        
        return items
    
    def get_preview_display_color(self):
        """Get display color for point"""
        from PySide2.QtGui import QColor
        return QColor(0, 120, 255)
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['geometry_type'] = self.geometry_type.value
        data['offset'] = self.offset
        data['elevation'] = self.elevation
        data['delta_x'] = self.delta_x
        data['delta_y'] = self.delta_y
        data['slope'] = self.slope
        data['from_point'] = self.from_point
        data['point_codes'] = self.point_codes
        data['add_link_to_from'] = self.add_link_to_from
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        node = cls(data['id'], data['name'])
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        
        # Load geometry type
        geo_type_str = data.get('geometry_type', 'Offset and Elevation')
        for gt in PointGeometryType:
            if gt.value == geo_type_str:
                node.geometry_type = gt
                break
        
        node.offset = data.get('offset', 0.0)
        node.elevation = data.get('elevation', 0.0)
        node.delta_x = data.get('delta_x', 0.0)
        node.delta_y = data.get('delta_y', 0.0)
        node.slope = data.get('slope', 0.0)
        node.from_point = data.get('from_point')
        node.point_codes = data.get('point_codes', [])
        node.add_link_to_from = data.get('add_link_to_from', True)
        
        return node


class LinkNode(FlowchartNode):
    """Link geometry node"""
    
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Link", name)
        self.link_type = LinkType.LINE
        self.start_point = None
        self.end_point = None
        self.link_codes = []
        self.material = "Asphalt"
        self.thickness = 0.0
    
    def get_properties_widgets(self, parent_widget):
        """Return property widgets for Link node"""
        from PySide2.QtWidgets import QComboBox, QDoubleSpinBox, QLineEdit
        
        widgets = {}
        
        # Link type
        link_type_combo = QComboBox(parent_widget)
        for lt in LinkType:
            link_type_combo.addItem(lt.value, lt)
        widgets['link_type'] = {
            'label': 'Link Type:',
            'widget': link_type_combo,
            'getter': lambda: link_type_combo.currentData(),
            'setter': lambda v: link_type_combo.setCurrentIndex(link_type_combo.findData(v))
        }
        
        # Start point
        start_combo = QComboBox(parent_widget)
        widgets['start_point'] = {
            'label': 'Start Point:',
            'widget': start_combo,
            'getter': lambda: start_combo.currentData(),
            'setter': lambda v: start_combo.setCurrentIndex(start_combo.findData(v)),
            'populate': 'points'
        }
        
        # End point
        end_combo = QComboBox(parent_widget)
        widgets['end_point'] = {
            'label': 'End Point:',
            'widget': end_combo,
            'getter': lambda: end_combo.currentData(),
            'setter': lambda v: end_combo.setCurrentIndex(end_combo.findData(v)),
            'populate': 'points'
        }
        
        # Link codes
        codes_edit = QLineEdit(parent_widget)
        codes_edit.setPlaceholderText('"Top","Pave"')
        widgets['link_codes'] = {
            'label': 'Link Codes:',
            'widget': codes_edit,
            'getter': lambda: self._parse_codes(codes_edit.text()),
            'setter': lambda v: codes_edit.setText(','.join(f'"{c}"' for c in v))
        }
        
        # Material
        material_combo = QComboBox(parent_widget)
        material_combo.addItems(["Asphalt", "Concrete", "Granular", "Soil"])
        widgets['material'] = {
            'label': 'Material:',
            'widget': material_combo,
            'getter': lambda: material_combo.currentText(),
            'setter': lambda v: material_combo.setCurrentText(v)
        }
        
        # Thickness
        thickness_spin = QDoubleSpinBox(parent_widget)
        thickness_spin.setRange(0, 10)
        thickness_spin.setDecimals(3)
        thickness_spin.setSuffix(" m")
        widgets['thickness'] = {
            'label': 'Thickness:',
            'widget': thickness_spin,
            'getter': lambda: thickness_spin.value(),
            'setter': lambda v: thickness_spin.setValue(v)
        }
        
        return widgets
    
    def _parse_codes(self, text):
        """Parse comma-separated quoted strings"""
        import re
        return re.findall(r'"([^"]*)"', text)
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Create preview items for link"""
        from PySide2.QtGui import QFont, QColor
        
        items = []
        
        if self.start_point and self.end_point:
            if self.start_point in point_positions and self.end_point in point_positions:
                start_pos = point_positions[self.start_point]
                end_pos = point_positions[self.end_point]
                
                x1 = start_pos[0] * scale_factor
                y1 = -start_pos[1] * scale_factor
                x2 = end_pos[0] * scale_factor
                y2 = -end_pos[1] * scale_factor
                
                # Import PreviewLineItem and PreviewTextItem
                from preview import PreviewLineItem, PreviewTextItem
                
                # Create line
                line_item = PreviewLineItem(x1, y1, x2, y2, self)
                items.append(line_item)
                
                # Add name
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                name_text = PreviewTextItem(self.name, self)
                name_font = QFont()
                name_font.setPointSize(8)
                name_font.setBold(True)
                name_text.setFont(name_font)
                name_text.setPos(mid_x, mid_y - 30)
                name_text.setDefaultTextColor(QColor(0, 100, 0))
                items.append(name_text)
                
                # Add codes if enabled
                if show_codes and self.link_codes:
                    code_text = PreviewTextItem(f"[{','.join(self.link_codes)}]", self)
                    code_font = QFont()
                    code_font.setPointSize(7)
                    code_text.setFont(code_font)
                    code_text.setPos(mid_x, mid_y - 15)
                    code_text.setDefaultTextColor(QColor(0, 150, 0))
                    items.append(code_text)
        
        return items
    
    def get_preview_display_color(self):
        """Get display color for link"""
        from PySide2.QtGui import QColor
        return QColor(0, 150, 0)
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['link_type'] = self.link_type.value
        data['start_point'] = self.start_point
        data['end_point'] = self.end_point
        data['link_codes'] = self.link_codes
        data['material'] = self.material
        data['thickness'] = self.thickness
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        node = cls(data['id'], data['name'])
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        
        # Load link type
        link_type_str = data.get('link_type', 'Line')
        for lt in LinkType:
            if lt.value == link_type_str:
                node.link_type = lt
                break
        
        node.start_point = data.get('start_point')
        node.end_point = data.get('end_point')
        node.link_codes = data.get('link_codes', [])
        node.material = data.get('material', 'Asphalt')
        node.thickness = data.get('thickness', 0.0)
        
        return node


class ShapeNode(FlowchartNode):
    """Shape geometry node"""
    
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Shape", name)
        self.shape_codes = []
        self.links = []
        self.material = "Asphalt"
    
    def get_properties_widgets(self, parent_widget):
        """Return property widgets for Shape node"""
        from PySide2.QtWidgets import QLineEdit, QListWidget, QPushButton
        
        widgets = {}
        
        # Shape codes
        codes_edit = QLineEdit(parent_widget)
        codes_edit.setPlaceholderText('"Pave"')
        widgets['shape_codes'] = {
            'label': 'Shape Codes:',
            'widget': codes_edit,
            'getter': lambda: self._parse_codes(codes_edit.text()),
            'setter': lambda v: codes_edit.setText(','.join(f'"{c}"' for c in v))
        }
        
        # Links list
        links_list = QListWidget(parent_widget)
        widgets['links'] = {
            'label': 'Links:',
            'widget': links_list,
            'getter': lambda: self.links,
            'setter': lambda v: None  # Read-only for now
        }
        
        return widgets
    
    def _parse_codes(self, text):
        """Parse comma-separated quoted strings"""
        import re
        return re.findall(r'"([^"]*)"', text)
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Create preview items for shape"""
        from PySide2.QtGui import QFont, QColor, QPen, QBrush, QPolygonF
        from PySide2.QtCore import QPointF
        from PySide2.QtWidgets import QGraphicsPolygonItem
        
        items = []
        
        # This would need access to flowchart_nodes to resolve links
        # For now, return empty list
        # TODO: Improve this to handle shape rendering
        
        return items
    
    def get_preview_display_color(self):
        """Get display color for shape"""
        from PySide2.QtGui import QColor
        return QColor(200, 200, 150)
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['shape_codes'] = self.shape_codes
        data['links'] = self.links
        data['material'] = self.material
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        node = cls(data['id'], data['name'])
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        node.shape_codes = data.get('shape_codes', [])
        node.links = data.get('links', [])
        node.material = data.get('material', 'Asphalt')
        return node


class DecisionNode(FlowchartNode):
    """Decision/condition node for branching logic"""
    
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Decision", name)
        self.condition = ""
        self.true_branch = []
        self.false_branch = []
    
    def get_properties_widgets(self, parent_widget):
        """Return property widgets for Decision node"""
        from PySide2.QtWidgets import QTextEdit
        
        widgets = {}
        
        # Condition
        condition_edit = QTextEdit(parent_widget)
        condition_edit.setMaximumHeight(60)
        condition_edit.setPlaceholderText('e.g.: EG_Elevation > P1_Elevation')
        widgets['condition'] = {
            'label': 'Condition:',
            'widget': condition_edit,
            'getter': lambda: condition_edit.toPlainText(),
            'setter': lambda v: condition_edit.setText(v)
        }
        
        return widgets
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Decision nodes don't appear in preview"""
        return []
    
    def get_preview_display_color(self):
        """Get display color for decision"""
        from PySide2.QtGui import QColor
        return QColor(255, 200, 100)
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['condition'] = self.condition
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        node = cls(data['id'], data['name'])
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        node.condition = data.get('condition', '')
        return node


class StartNode(FlowchartNode):
    """Start node - special node for workflow beginning"""
    
    def __init__(self, node_id, name="START"):
        super().__init__(node_id, "Start", name)
    
    def get_properties_widgets(self, parent_widget):
        """Start node has no editable properties"""
        return {}
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Start nodes don't appear in preview"""
        return []
    
    def get_preview_display_color(self):
        """Get display color for start node"""
        from PySide2.QtGui import QColor
        return QColor(100, 200, 100)
    
    def get_flowchart_display_text(self):
        """Override to show just START"""
        return "START"
    
    def to_dict(self):
        """Convert to dictionary"""
        return super().to_dict()
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        node = cls(data['id'], data.get('name', 'START'))
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        return node


class VariableNode(FlowchartNode):
    """Variable calculation node"""
    
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Variable", name)
        self.variable_name = ""
        self.expression = ""
    
    def get_properties_widgets(self, parent_widget):
        """Return property widgets for Variable node"""
        from PySide2.QtWidgets import QLineEdit
        
        widgets = {}
        
        widgets['variable_name'] = {
            'label': 'Variable Name:',
            'widget': QLineEdit(parent_widget),
            'getter': lambda: widgets['variable_name']['widget'].text(),
            'setter': lambda v: widgets['variable_name']['widget'].setText(v)
        }
        
        widgets['expression'] = {
            'label': 'Expression:',
            'widget': QLineEdit(parent_widget),
            'getter': lambda: widgets['expression']['widget'].text(),
            'setter': lambda v: widgets['expression']['widget'].setText(v)
        }
        
        return widgets
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Variable nodes don't appear in preview"""
        return []
    
    def get_preview_display_color(self):
        """Get display color for variable"""
        from PySide2.QtGui import QColor
        return QColor(200, 200, 255)


class GenericNode(FlowchartNode):
    """Generic node for unknown/custom node types"""
    
    def __init__(self, node_id, node_type, name=""):
        super().__init__(node_id, node_type, name)
    
    def get_properties_widgets(self, parent_widget):
        """Generic node has no specific properties"""
        return {}
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Generic nodes don't appear in preview"""
        return []
    
    def get_preview_display_color(self):
        """Get display color for generic node"""
        from PySide2.QtGui import QColor
        return QColor(150, 150, 150)


# Node registry for factory pattern
NODE_REGISTRY = {
    'Point': PointNode,
    'Link': LinkNode,
    'Shape': ShapeNode,
    'Decision': DecisionNode,
    'Variable': VariableNode,
    'Start': StartNode,
}


def create_node_from_type(node_type, node_id, name=""):
    """Factory method to create nodes by type
    
    Args:
        node_type: String type of node ('Point', 'Link', etc)
        node_id: Unique identifier
        name: Display name
        
    Returns:
        FlowchartNode: New node instance
    """
    node_class = NODE_REGISTRY.get(node_type)
    if node_class is None:
        # Create a generic node for unknown types
        return GenericNode(node_id, node_type, name)
    return node_class(node_id, name)


def create_node_from_dict(data):
    """Factory method to create nodes from dictionary
    
    Args:
        data: Dictionary with node data including 'type'
        
    Returns:
        FlowchartNode: Deserialized node instance
    """
    node_type = data.get('type')
    node_class = NODE_REGISTRY.get(node_type)
    
    if node_class is None:
        # Unknown node type - use GenericNode
        node = GenericNode(data['id'], node_type, data.get('name', ''))
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        node.properties = data.get('properties', {})
        return node
    
    return node_class.from_dict(data)


class ComponentParameter:
    """Input/Output parameter definition"""
    def __init__(self, name, param_type, direction="Input", default_value=0.0):
        self.name = name
        self.type = param_type
        self.direction = direction  # Input, Output, InputOutput
        self.default_value = default_value
        self.display_name = name
        self.description = ""
        self.current_value = default_value


class TargetParameter:
    """Target parameter for surface/alignment/profile references"""
    def __init__(self, name, target_type):
        self.name = name
        self.type = target_type
        self.preview_value = -1.0