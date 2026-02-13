"""
Data Models for Component Designer
Contains all node types, parameters, and geometry definitions
"""
from enum import Enum


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


class FlowchartNode:
    """Base class for flowchart nodes"""
    def __init__(self, node_id, node_type, name=""):
        self.id = node_id
        self.type = node_type
        self.name = name
        self.x = 0
        self.y = 0
        self.properties = {}
        self.next_nodes = []
        
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'properties': self.properties
        }


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
        
        
class ShapeNode(FlowchartNode):
    """Shape geometry node"""
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Shape", name)
        self.shape_codes = []
        self.links = []  # List of link nodes that form the shape
        self.material = "Asphalt"
        

class DecisionNode(FlowchartNode):
    """Decision/condition node for branching logic"""
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Decision", name)
        self.condition = ""
        self.true_branch = []
        self.false_branch = []


class VariableNode(FlowchartNode):
    """Variable calculation node"""
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Variable", name)
        self.variable_name = ""
        self.expression = ""


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
