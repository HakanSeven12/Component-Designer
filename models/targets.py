"""
Target nodes for Component Designer.

Three specialised target types:

  SurfaceTargetNode   – horizontal dashed green line across the full preview
  ElevationTargetNode – right-side leftward arrow at a given Y elevation
  OffsetTargetNode    – top-side downward arrow at a given X offset

Visual rendering is handled entirely in GeometryPreview.drawForeground()
so the indicators always span / stay inside the visible viewport area.
Each node exposes a 'preview_value' output port whose value drives the
indicator position.
"""

from PySide2.QtGui import QColor
from .base import FlowchartNode


class SurfaceTargetNode(FlowchartNode):
    """
    Represents a design surface.
    Preview: full-width dashed green line at elevation = preview_value.
    """

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Surface Target", name)
        self.preview_value = 0.0

    def get_input_ports(self) -> dict:
        return {}

    def get_output_ports(self) -> dict:
        return {"preview_value": "float"}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []   # drawn in GeometryPreview.drawForeground

    def get_preview_display_color(self):
        return QColor(0, 180, 60)

    def to_dict(self):
        d = super().to_dict()
        d["preview_value"] = self.preview_value
        return d

    @classmethod
    def from_dict(cls, data):
        node               = cls(data["id"], data.get("name", ""))
        node.x             = data.get("x", 0)
        node.y             = data.get("y", 0)
        node.preview_value = data.get("preview_value", 0.0)
        return node


class ElevationTargetNode(FlowchartNode):
    """
    Represents a fixed elevation constraint.
    Preview: right-edge leftward arrow at Y = preview_value.
    """

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Elevation Target", name)
        self.preview_value = 0.0

    def get_input_ports(self) -> dict:
        return {}

    def get_output_ports(self) -> dict:
        return {"preview_value": "float"}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []   # drawn in GeometryPreview.drawForeground

    def get_preview_display_color(self):
        return QColor(220, 60, 20)

    def to_dict(self):
        d = super().to_dict()
        d["preview_value"] = self.preview_value
        return d

    @classmethod
    def from_dict(cls, data):
        node               = cls(data["id"], data.get("name", ""))
        node.x             = data.get("x", 0)
        node.y             = data.get("y", 0)
        node.preview_value = data.get("preview_value", 0.0)
        return node


class OffsetTargetNode(FlowchartNode):
    """
    Represents a horizontal offset constraint.
    Preview: top-edge downward arrow at X = preview_value.
    """

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Offset Target", name)
        self.preview_value = 0.0

    def get_input_ports(self) -> dict:
        return {}

    def get_output_ports(self) -> dict:
        return {"preview_value": "float"}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []   # drawn in GeometryPreview.drawForeground

    def get_preview_display_color(self):
        return QColor(20, 80, 220)

    def to_dict(self):
        d = super().to_dict()
        d["preview_value"] = self.preview_value
        return d

    @classmethod
    def from_dict(cls, data):
        node               = cls(data["id"], data.get("name", ""))
        node.x             = data.get("x", 0)
        node.y             = data.get("y", 0)
        node.preview_value = data.get("preview_value", 0.0)
        return node