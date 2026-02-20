"""
Base classes and shared enums for Component Designer models.
"""

from abc import ABC, abstractmethod
from enum import Enum


class PointGeometryType(Enum):
    ANGLE_DELTA_X    = "Angle and Delta X"
    ANGLE_DELTA_Y    = "Angle and Delta Y"
    ANGLE_DISTANCE   = "Angle and Distance"
    DELTA_XY         = "Delta X and Delta Y"
    DELTA_X_SURFACE  = "Delta X on Surface"
    INTERPOLATE      = "Interpolate Point"
    SLOPE_DELTA_X    = "Slope and Delta X"
    SLOPE_DELTA_Y    = "Slope and Delta Y"
    SLOPE_TO_SURFACE = "Slope to Surface"


class LinkType(Enum):
    LINE     = "Line"
    ARC      = "Arc"
    PARABOLA = "Parabola"


class TargetType(Enum):
    SURFACE   = "Surface"
    ALIGNMENT = "Alignment"
    PROFILE   = "Profile"
    OFFSET    = "Offset"
    ELEVATION = "Elevation"


class DataType(Enum):
    INTEGER        = "Integer"
    DOUBLE         = "Double"
    STRING         = "String"
    GRADE          = "Grade"
    SLOPE          = "Slope"
    YES_NO         = "Yes\\No"
    SIDE           = "Side"
    SUPERELEVATION = "Superelevation"


def _enum_options(enum_cls):
    """Convert an Enum class into a list of label/value dicts for combo fields."""
    return [{'label': e.value, 'value': e} for e in enum_cls]


class FlowchartNode(ABC):
    """Abstract base class for all flowchart nodes."""

    def __init__(self, node_id, node_type, name=""):
        self.id         = node_id
        self.type       = node_type
        self.name       = name
        self.x          = 0
        self.y          = 0
        self.properties = {}
        self.next_nodes = []

    def get_input_ports(self) -> dict:
        return {}

    def get_output_ports(self) -> dict:
        return {}

    @abstractmethod
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        pass

    @abstractmethod
    def get_preview_display_color(self):
        pass

    def get_flowchart_display_text(self):
        return f"{self.type}\n{self.name}"

    def to_dict(self):
        return {
            'id':         self.id,
            'type':       self.type,
            'name':       self.name,
            'x':          self.x,
            'y':          self.y,
            'properties': self.properties,
        }
