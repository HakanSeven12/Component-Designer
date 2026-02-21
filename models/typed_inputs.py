"""
Typed input nodes for direct value entry:
IntegerInputNode, DoubleInputNode, StringInputNode,
GradeInputNode, SlopeInputNode, YesNoInputNode, SuperelevationInputNode.
"""

from PySide2.QtGui import QColor

from .base import FlowchartNode, port


class IntegerInputNode(FlowchartNode):
    """A node that holds a single integer value."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Integer Input", name)
        self.value = 0

    def get_input_ports(self) -> dict:
        return {}

    def get_output_ports(self) -> dict:
        return {'value': port('int', editor=True)}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(130, 160, 255)

    def to_dict(self):
        d = super().to_dict()
        d['value'] = self.value
        return d

    @classmethod
    def from_dict(cls, data):
        node       = cls(data['id'], data.get('name', ''))
        node.x     = data.get('x', 0)
        node.y     = data.get('y', 0)
        node.value = data.get('value', 0)
        return node


class DoubleInputNode(FlowchartNode):
    """A node that holds a single floating-point value."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Double Input", name)
        self.value = 0.0

    def get_input_ports(self) -> dict:
        return {}

    def get_output_ports(self) -> dict:
        return {'value': port('float', editor=True)}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(100, 150, 255)

    def to_dict(self):
        d = super().to_dict()
        d['value'] = self.value
        return d

    @classmethod
    def from_dict(cls, data):
        node       = cls(data['id'], data.get('name', ''))
        node.x     = data.get('x', 0)
        node.y     = data.get('y', 0)
        node.value = data.get('value', 0.0)
        return node


class StringInputNode(FlowchartNode):
    """A node that holds a single text string value."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "String Input", name)
        self.value = ""

    def get_input_ports(self) -> dict:
        return {}

    def get_output_ports(self) -> dict:
        return {'value': port('string', editor=True)}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(160, 200, 255)

    def to_dict(self):
        d = super().to_dict()
        d['value'] = self.value
        return d

    @classmethod
    def from_dict(cls, data):
        node       = cls(data['id'], data.get('name', ''))
        node.x     = data.get('x', 0)
        node.y     = data.get('y', 0)
        node.value = data.get('value', '')
        return node


class GradeInputNode(FlowchartNode):
    """Computes a grade percentage from rise and run values."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Grade Input", name)
        self.rise = 1.0
        self.run  = 2.0

    @property
    def percent(self) -> float:
        """Grade as a percentage (rise / run * 100)."""
        return (self.rise / self.run * 100.0) if self.run != 0.0 else 0.0

    def get_input_ports(self) -> dict:
        return {'rise': port('float', editor=True),
                'run': port('float', editor=True)}

    def get_output_ports(self) -> dict:
        return {'percent': 'percent'}

    def get_port_value(self, port_name):
        if port_name == 'percent':
            return self.percent
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if port_name in ('rise', 'run'):
            setattr(self, port_name, float(value) if value is not None else 0.0)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(100, 210, 180)

    def to_dict(self):
        d = super().to_dict()
        d['rise'] = self.rise
        d['run']  = self.run
        return d

    @classmethod
    def from_dict(cls, data):
        node      = cls(data['id'], data.get('name', ''))
        node.x    = data.get('x', 0)
        node.y    = data.get('y', 0)
        node.rise = data.get('rise', 1.0)
        node.run  = data.get('run',  2.0)
        return node


class SlopeInputNode(FlowchartNode):
    """A node that holds a slope value expressed as a percentage."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Slope Input", name)
        self.value = 0.0

    def get_input_ports(self) -> dict:
        return {}

    def get_output_ports(self) -> dict:
        return {'value': port('percent', editor=True)}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(80, 190, 160)

    def to_dict(self):
        d = super().to_dict()
        d['value'] = self.value
        return d

    @classmethod
    def from_dict(cls, data):
        node       = cls(data['id'], data.get('name', ''))
        node.x     = data.get('x', 0)
        node.y     = data.get('y', 0)
        node.value = data.get('value', 0.0)
        return node


class YesNoInputNode(FlowchartNode):
    """A boolean (yes/no) toggle node."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Yes\\No Input", name)
        self.value = False

    def get_input_ports(self) -> dict:
        return {}

    def get_output_ports(self) -> dict:
        return {'value': port('bool', editor=True)}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(255, 210, 120)

    def to_dict(self):
        d = super().to_dict()
        d['value'] = self.value
        return d

    @classmethod
    def from_dict(cls, data):
        node       = cls(data['id'], data.get('name', ''))
        node.x     = data.get('x', 0)
        node.y     = data.get('y', 0)
        node.value = data.get('value', False)
        return node


class SuperelevationInputNode(FlowchartNode):
    """Provides a superelevation percentage for a specific lane position."""

    _LANE_OPTIONS = [
        {'label': 'Left Inside Lane',       'value': 'Left Inside Lane'},
        {'label': 'Left Outside Lane',      'value': 'Left Outside Lane'},
        {'label': 'Right Inside Lane',      'value': 'Right Inside Lane'},
        {'label': 'Right Outside Lane',     'value': 'Right Outside Lane'},
        {'label': 'Left Inside Shoulder',   'value': 'Left Inside Shoulder'},
        {'label': 'Left Outside Shoulder',  'value': 'Left Outside Shoulder'},
        {'label': 'Right Inside Shoulder',  'value': 'Right Inside Shoulder'},
        {'label': 'Right Outside Shoulder', 'value': 'Right Outside Shoulder'},
    ]

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Superelevation Input", name)
        self.lane  = 'Left Inside Lane'
        self.value = 0.0

    def get_input_ports(self) -> dict:
        return {'lane': self._LANE_OPTIONS}

    def get_output_ports(self) -> dict:
        return {'value': port('percent', editor=True)}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(180, 130, 255)

    def to_dict(self):
        d = super().to_dict()
        d['lane']  = self.lane
        d['value'] = self.value
        return d

    @classmethod
    def from_dict(cls, data):
        node       = cls(data['id'], data.get('name', ''))
        node.x     = data.get('x', 0)
        node.y     = data.get('y', 0)
        node.lane  = data.get('lane',  'Left Inside Lane')
        node.value = data.get('value', 0.0)
        return node
