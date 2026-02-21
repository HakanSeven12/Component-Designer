"""
Workflow control nodes: StartNode, DecisionNode, VariableNode, GenericNode.
"""

from PySide2.QtGui import QColor

from .base import FlowchartNode, port


class StartNode(FlowchartNode):
    """Entry point of every flowchart; always present and cannot be deleted."""

    def __init__(self, node_id, name="START"):
        super().__init__(node_id, "Start", name)

    def get_output_ports(self) -> dict:
        return {'vector': None}

    def get_flowchart_display_text(self):
        return "START"

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(100, 200, 100)

    @classmethod
    def from_dict(cls, data):
        node   = cls(data['id'], data.get('name', 'START'))
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        return node


class DecisionNode(FlowchartNode):
    """
    Branching node that evaluates a numeric/boolean condition.

    Ports
    -----
    Inputs:
        condition : float — any non-zero value is treated as True.
                            Wire a math/input node here to drive branching.
    Outputs:
        yes : None (node-ref) — nodes connected here are rendered when
                                condition != 0.
        no  : None (node-ref) — nodes connected here are rendered when
                                condition == 0 (or falsy).

    The preview renderer inspects which output port a downstream node is
    connected to and shows/hides it accordingly.
    """

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Decision", name)
        # Stores the evaluated numeric condition value (updated from wiring).
        self.condition = 0.0

    # ------------------------------------------------------------------
    # Port declarations
    # ------------------------------------------------------------------

    def get_input_ports(self) -> dict:
        # 'condition' accepts a float value; an inline spinbox lets the user
        # set a static value without wiring.
        return {
            'condition': port('float', editor=True),
        }

    def get_output_ports(self) -> dict:
        # Node-ref ports — downstream nodes connect to 'yes' or 'no'.
        return {
            'yes': None,
            'no':  None,
        }

    # ------------------------------------------------------------------
    # Value accessors (used by the connection resolver)
    # ------------------------------------------------------------------

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if port_name == 'condition':
            try:
                self.condition = float(value) if value is not None else 0.0
            except (TypeError, ValueError):
                self.condition = 0.0

    # ------------------------------------------------------------------
    # Convenience: evaluate condition as boolean
    # ------------------------------------------------------------------

    @property
    def condition_is_true(self) -> bool:
        """Return True when condition is non-zero."""
        return bool(self.condition)

    # ------------------------------------------------------------------
    # Preview / theme
    # ------------------------------------------------------------------

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        # Decision nodes themselves have no visual geometry in the preview.
        return []

    def get_preview_display_color(self):
        return QColor(255, 200, 100)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self):
        d = super().to_dict()
        d['condition'] = self.condition
        return d

    @classmethod
    def from_dict(cls, data):
        node           = cls(data['id'], data['name'])
        node.x         = data.get('x', 0)
        node.y         = data.get('y', 0)
        node.condition = float(data.get('condition', 0.0))
        return node


class VariableNode(FlowchartNode):
    """Stores a named variable computed from an expression."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Variable", name)
        self.variable_name = ""
        self.expression    = ""

    def get_input_ports(self) -> dict:
        return {'variable_name': 'string', 'expression': 'string'}

    def get_output_ports(self) -> dict:
        return {'value': 'float'}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(200, 200, 255)

    def to_dict(self):
        d = super().to_dict()
        d.update({'variable_name': self.variable_name,
                  'expression':    self.expression})
        return d

    @classmethod
    def from_dict(cls, data):
        node               = cls(data['id'], data['name'])
        node.x             = data.get('x', 0)
        node.y             = data.get('y', 0)
        node.variable_name = data.get('variable_name', '')
        node.expression    = data.get('expression', '')
        return node


class GenericNode(FlowchartNode):
    """Fallback node for unknown or future node types."""

    def __init__(self, node_id, node_type, name=""):
        super().__init__(node_id, node_type, name)

    def get_input_ports(self)  -> dict: return {}
    def get_output_ports(self) -> dict: return {}

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(150, 150, 150)
