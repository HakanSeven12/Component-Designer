"""
Parameter nodes: InputParameterNode, OutputParameterNode, TargetParameterNode.
"""

from PySide2.QtGui import QColor

from .base import FlowchartNode, DataType, TargetType, _enum_options


class InputParameterNode(FlowchartNode):
    """Generic user-facing input parameter with a selectable data type."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Input", name)
        self.data_type     = DataType.DOUBLE
        self.default_value = 0.0

    def get_input_ports(self) -> dict:
        return {
            'data_type':     _enum_options(DataType),
            'default_value': 'float',
        }

    def get_output_ports(self) -> dict:
        return {'value': None}

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
        d.update({'data_type':     self.data_type.value,
                  'default_value': self.default_value})
        return d

    @classmethod
    def from_dict(cls, data):
        node = cls(data['id'], data['name'])
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        dt_str = data.get('data_type', 'Double')
        node.data_type = next(
            (dt for dt in DataType if dt.value == dt_str), DataType.DOUBLE)
        node.default_value = data.get('default_value', 0.0)
        return node


class OutputParameterNode(FlowchartNode):
    """Receives a computed value and exposes it as a named output parameter."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Output", name)
        self.data_type = DataType.DOUBLE

    def get_input_ports(self) -> dict:
        return {
            'value':     None,
            'data_type': _enum_options(DataType),
        }

    def get_output_ports(self) -> dict:
        return {}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(255, 150, 100)

    def to_dict(self):
        d = super().to_dict()
        d.update({'data_type': self.data_type.value})
        return d

    @classmethod
    def from_dict(cls, data):
        node = cls(data['id'], data['name'])
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        dt_str = data.get('data_type', 'Double')
        node.data_type = next(
            (dt for dt in DataType if dt.value == dt_str), DataType.DOUBLE)
        return node


class TargetParameterNode(FlowchartNode):
    """References an external design target (surface, alignment, etc.)."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Target", name)
        self.target_type   = TargetType.SURFACE
        self.preview_value = -1.0

    def get_input_ports(self) -> dict:
        return {
            'target_type':   _enum_options(TargetType),
            'preview_value': 'float',
        }

    def get_output_ports(self) -> dict:
        return {'target': None}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(150, 255, 150)

    def to_dict(self):
        d = super().to_dict()
        d.update({'target_type':   self.target_type.value,
                  'preview_value': self.preview_value})
        return d

    @classmethod
    def from_dict(cls, data):
        node = cls(data['id'], data['name'])
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        tt_str = data.get('target_type', 'Surface')
        node.target_type = next(
            (tt for tt in TargetType if tt.value == tt_str), TargetType.SURFACE)
        node.preview_value = data.get('preview_value', -1.0)
        return node
