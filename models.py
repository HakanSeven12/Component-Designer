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
    
    def get_input_ports(self):
        """Get list of input port types this node has
        
        Returns:
            list: List of input port type strings
        """
        return []  # Default: no input ports
    
    def get_output_ports(self):
        """Get list of output port types this node has
        
        Returns:
            list: List of output port type strings
        """
        return []  # Default: no output ports
        
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
    
    def get_inline_properties(self):
        """Get properties for inline editing in flowchart
        
        Returns:
            list: List of property definitions for inline editing
        """
        return [
            {
                'name': 'name',
                'label': 'Name',
                'type': 'string',
                'value': self.name
            }
        ]
    
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
    
    def get_input_ports(self):
        """Point nodes have 'to' as input port"""
        return ['to']
    
    def get_output_ports(self):
        """Point nodes have 'from' as output port"""
        return ['from']
    
    def get_inline_properties(self):
        """Get properties for inline editing in flowchart"""
        properties = [
            {
                'name': 'name',
                'label': 'Name',
                'type': 'string',
                'value': self.name
            },
            {
                'name': 'geometry_type',
                'label': 'Type',
                'type': 'combo',
                'value': self.geometry_type,
                'options': [{'label': gt.value, 'value': gt} for gt in PointGeometryType]
            }
        ]
        
        # Add relevant properties based on geometry type
        if self.geometry_type == PointGeometryType.OFFSET_ELEVATION:
            properties.extend([
                {
                    'name': 'offset',
                    'label': 'Offset',
                    'type': 'float',
                    'value': self.offset
                },
                {
                    'name': 'elevation',
                    'label': 'Elevation',
                    'type': 'float',
                    'value': self.elevation
                }
            ])
        elif self.geometry_type == PointGeometryType.DELTA_XY:
            properties.extend([
                {
                    'name': 'delta_x',
                    'label': 'Delta X',
                    'type': 'float',
                    'value': self.delta_x
                },
                {
                    'name': 'delta_y',
                    'label': 'Delta Y',
                    'type': 'float',
                    'value': self.delta_y
                }
            ])
        elif self.geometry_type == PointGeometryType.DELTA_X_SLOPE:
            properties.extend([
                {
                    'name': 'delta_x',
                    'label': 'Delta X',
                    'type': 'float',
                    'value': self.delta_x
                },
                {
                    'name': 'slope',
                    'label': 'Slope',
                    'type': 'float',
                    'value': self.slope
                }
            ])
        elif self.geometry_type == PointGeometryType.DELTA_Y_SLOPE:
            properties.extend([
                {
                    'name': 'delta_y',
                    'label': 'Delta Y',
                    'type': 'float',
                    'value': self.delta_y
                },
                {
                    'name': 'slope',
                    'label': 'Slope',
                    'type': 'float',
                    'value': self.slope
                }
            ])
        elif self.geometry_type == PointGeometryType.DELTA_X_SURFACE:
            properties.extend([
                {
                    'name': 'delta_x',
                    'label': 'Delta X',
                    'type': 'float',
                    'value': self.delta_x
                }
            ])
        elif self.geometry_type == PointGeometryType.OFFSET_TARGET:
            properties.extend([
                {
                    'name': 'offset',
                    'label': 'Offset',
                    'type': 'float',
                    'value': self.offset
                }
            ])
        elif self.geometry_type == PointGeometryType.ELEVATION_TARGET:
            properties.extend([
                {
                    'name': 'elevation',
                    'label': 'Elevation',
                    'type': 'float',
                    'value': self.elevation
                }
            ])
        
        return properties
        
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
    
    def get_input_ports(self):
        """Link nodes have 'start' and 'end' as input ports"""
        return ['start', 'end']
    
    def get_output_ports(self):
        """Link nodes have no output ports"""
        return []
    
    def get_inline_properties(self):
        """Get properties for inline editing in flowchart"""
        properties = [
            {
                'name': 'name',
                'label': 'Name',
                'type': 'string',
                'value': self.name
            },
            {
                'name': 'link_type',
                'label': 'Type',
                'type': 'combo',
                'value': self.link_type,
                'options': [{'label': lt.value, 'value': lt} for lt in LinkType]
            },
            {
                'name': 'thickness',
                'label': 'Thickness',
                'type': 'float',
                'value': self.thickness
            }
        ]
        return properties
    
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
    
    def get_input_ports(self):
        """Shape nodes have no ports"""
        return []
    
    def get_output_ports(self):
        """Shape nodes have no ports"""
        return []
    
    def get_inline_properties(self):
        """Get properties for inline editing in flowchart"""
        properties = [
            {
                'name': 'name',
                'label': 'Name',
                'type': 'string',
                'value': self.name
            },
            {
                'name': 'material',
                'label': 'Material',
                'type': 'string',
                'value': self.material
            }
        ]
        return properties
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Create preview items for shape"""
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
    
    def get_input_ports(self):
        """Decision nodes have no ports for now"""
        return []
    
    def get_output_ports(self):
        """Decision nodes have no ports for now"""
        return []
    
    def get_inline_properties(self):
        """Get properties for inline editing in flowchart"""
        properties = [
            {
                'name': 'name',
                'label': 'Name',
                'type': 'string',
                'value': self.name
            }
        ]
        return properties
    
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
    
    def get_input_ports(self):
        """Start node has no input ports"""
        return []
    
    def get_output_ports(self):
        """Start node has 'from' as output port"""
        return ['from']
    
    def get_inline_properties(self):
        """Get properties for inline editing in flowchart"""
        return []  # START node has no editable properties
    
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
    
    def get_input_ports(self):
        """Variable nodes have no ports"""
        return []
    
    def get_output_ports(self):
        """Variable nodes have no ports"""
        return []
    
    def get_inline_properties(self):
        """Get properties for inline editing in flowchart"""
        properties = [
            {
                'name': 'name',
                'label': 'Name',
                'type': 'string',
                'value': self.name
            },
            {
                'name': 'variable_name',
                'label': 'Variable',
                'type': 'string',
                'value': self.variable_name
            },
            {
                'name': 'expression',
                'label': 'Expression',
                'type': 'string',
                'value': self.expression
            }
        ]
        return properties
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Variable nodes don't appear in preview"""
        return []
    
    def get_preview_display_color(self):
        """Get display color for variable"""
        from PySide2.QtGui import QColor
        return QColor(200, 200, 255)
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['variable_name'] = self.variable_name
        data['expression'] = self.expression
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        node = cls(data['id'], data['name'])
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        node.variable_name = data.get('variable_name', '')
        node.expression = data.get('expression', '')
        return node


class GenericNode(FlowchartNode):
    """Generic node for unknown/custom node types"""
    
    def __init__(self, node_id, node_type, name=""):
        super().__init__(node_id, node_type, name)
    
    def get_input_ports(self):
        """Generic nodes have no ports"""
        return []
    
    def get_output_ports(self):
        """Generic nodes have no ports"""
        return []
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Generic nodes don't appear in preview"""
        return []
    
    def get_preview_display_color(self):
        """Get display color for generic node"""
        from PySide2.QtGui import QColor
        return QColor(150, 150, 150)
    
class InputParameterNode(FlowchartNode):
    """Input parameter node"""
    
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Input Parameter", name)
        self.parameter_type = ParameterType.DISTANCE
        self.default_value = 0.0
        self.display_name = name
        self.description = ""
    
    def get_input_ports(self):
        """Input parameter nodes have no input ports"""
        return []
    
    def get_output_ports(self):
        """Input parameter nodes have 'value' as output port"""
        return ['value']
    
    def get_inline_properties(self):
        """Get properties for inline editing in flowchart"""
        properties = [
            {
                'name': 'name',
                'label': 'Name',
                'type': 'string',
                'value': self.name
            },
            {
                'name': 'parameter_type',
                'label': 'Type',
                'type': 'combo',
                'value': self.parameter_type,
                'options': [{'label': pt.value, 'value': pt} for pt in ParameterType]
            },
            {
                'name': 'default_value',
                'label': 'Default',
                'type': 'float',
                'value': self.default_value
            }
        ]
        return properties
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Input parameter nodes don't appear in preview"""
        return []
    
    def get_preview_display_color(self):
        """Get display color for input parameter"""
        from PySide2.QtGui import QColor
        return QColor(100, 150, 255)
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['parameter_type'] = self.parameter_type.value
        data['default_value'] = self.default_value
        data['display_name'] = self.display_name
        data['description'] = self.description
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        node = cls(data['id'], data['name'])
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        
        # Load parameter type
        param_type_str = data.get('parameter_type', 'Distance')
        for pt in ParameterType:
            if pt.value == param_type_str:
                node.parameter_type = pt
                break
        
        node.default_value = data.get('default_value', 0.0)
        node.display_name = data.get('display_name', node.name)
        node.description = data.get('description', '')
        return node


class OutputParameterNode(FlowchartNode):
    """Output parameter node"""
    
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Output Parameter", name)
        self.parameter_type = ParameterType.DISTANCE
        self.display_name = name
        self.description = ""
    
    def get_input_ports(self):
        """Output parameter nodes have 'value' as input port"""
        return ['value']
    
    def get_output_ports(self):
        """Output parameter nodes have no output ports"""
        return []
    
    def get_inline_properties(self):
        """Get properties for inline editing in flowchart"""
        properties = [
            {
                'name': 'name',
                'label': 'Name',
                'type': 'string',
                'value': self.name
            },
            {
                'name': 'parameter_type',
                'label': 'Type',
                'type': 'combo',
                'value': self.parameter_type,
                'options': [{'label': pt.value, 'value': pt} for pt in ParameterType]
            }
        ]
        return properties
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Output parameter nodes don't appear in preview"""
        return []
    
    def get_preview_display_color(self):
        """Get display color for output parameter"""
        from PySide2.QtGui import QColor
        return QColor(255, 150, 100)
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['parameter_type'] = self.parameter_type.value
        data['display_name'] = self.display_name
        data['description'] = self.description
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        node = cls(data['id'], data['name'])
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        
        # Load parameter type
        param_type_str = data.get('parameter_type', 'Distance')
        for pt in ParameterType:
            if pt.value == param_type_str:
                node.parameter_type = pt
                break
        
        node.display_name = data.get('display_name', node.name)
        node.description = data.get('description', '')
        return node


class TargetParameterNode(FlowchartNode):
    """Target parameter node"""
    
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Target Parameter", name)
        self.target_type = TargetType.SURFACE
        self.preview_value = -1.0
    
    def get_input_ports(self):
        """Target parameter nodes have no input ports"""
        return []
    
    def get_output_ports(self):
        """Target parameter nodes have 'target' as output port"""
        return ['target']
    
    def get_inline_properties(self):
        """Get properties for inline editing in flowchart"""
        properties = [
            {
                'name': 'name',
                'label': 'Name',
                'type': 'string',
                'value': self.name
            },
            {
                'name': 'target_type',
                'label': 'Type',
                'type': 'combo',
                'value': self.target_type,
                'options': [{'label': tt.value, 'value': tt} for tt in TargetType]
            },
            {
                'name': 'preview_value',
                'label': 'Preview Value',
                'type': 'float',
                'value': self.preview_value
            }
        ]
        return properties
    
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        """Target parameter nodes don't appear in preview"""
        return []
    
    def get_preview_display_color(self):
        """Get display color for target parameter"""
        from PySide2.QtGui import QColor
        return QColor(150, 255, 150)
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data['target_type'] = self.target_type.value
        data['preview_value'] = self.preview_value
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        node = cls(data['id'], data['name'])
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        
        # Load target type
        target_type_str = data.get('target_type', 'Surface')
        for tt in TargetType:
            if tt.value == target_type_str:
                node.target_type = tt
                break
        
        node.preview_value = data.get('preview_value', -1.0)
        return node

# Node registry for factory pattern
NODE_REGISTRY = {
    'Point': PointNode,
    'Link': LinkNode,
    'Shape': ShapeNode,
    'Decision': DecisionNode,
    'Variable': VariableNode,
    'Start': StartNode,
    'Input Parameter': InputParameterNode,
    'Output Parameter': OutputParameterNode,
    'Target Parameter': TargetParameterNode,
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