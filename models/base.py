"""
Base classes and shared enums for Component Designer models.

Unified port value system
-------------------------
Every node exposes get_port_value(name) and set_port_value(name, value).
Wire connections are the ONLY data transport mechanism — there are no
special-case node references (from_point, start_point, end_point) that
bypass the wire system.

Port definition format
----------------------
  None
      Generic connectable port — no type, no inline editor.
      Can carry any Python value (tuple, node, float, …).

  'float' | 'int' | 'string' | 'bool' | 'percent'
      Scalar shorthand — renders an inline editor widget.

  {'type': 'float', 'editor': True}
      Explicit dict form. 'editor' defaults to False when omitted.

  {'type': 'float', 'editor': False}
      Connectable port with known type, no inline editor.

  [{'label': '...', 'value': ...}, ...]
      Combo-box options list. Rendered as a ComboField.
"""

from abc import ABC, abstractmethod
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Port-definition helpers
# ---------------------------------------------------------------------------

SCALAR_TYPES = frozenset(('float', 'int', 'string', 'bool', 'percent'))


def port(ptype, editor=False):
    """
    Convenience constructor for a port-definition dict.

        port('float')                → {'type': 'float', 'editor': False}
        port('float', editor=True)   → {'type': 'float', 'editor': True}
    """
    return {'type': ptype, 'editor': bool(editor)}


def unpack_port(port_def):
    """
    Normalise any port definition to (type_str_or_None, editor: bool).

    None                                → (None,   False)
    'float'                             → ('float', False)
    {'type': 'float'}                   → ('float', False)
    {'type': 'float', 'editor': True}   → ('float', True)
    [{'label':…, 'value':…}, …]        → (list,    False)
    """
    if port_def is None:
        return None, False
    if isinstance(port_def, list):
        return port_def, False
    if isinstance(port_def, dict):
        return port_def.get('type', None), bool(port_def.get('editor', False))
    # Plain string shorthand
    return port_def, False


def port_type(port_def):
    t, _ = unpack_port(port_def)
    return t


def port_editor(port_def) -> bool:
    _, ed = unpack_port(port_def)
    return ed


# ---------------------------------------------------------------------------
# Abstract base node
# ---------------------------------------------------------------------------

class FlowchartNode(ABC):
    """
    Abstract base class for all flowchart nodes.

    Data flow contract
    ------------------
    * get_port_value(name)      — return the current value for port *name*.
                                  For output ports this usually means computing
                                  a result on the fly.
    * set_port_value(name, val) — accept an incoming value from a wire.
                                  For input ports this stores the value so
                                  get_port_value can use it later.

    Nodes must NOT maintain hard-coded ID references to other nodes
    (e.g. from_point, start_point).  All data travels via wires.
    """

    def __init__(self, node_id, node_type, name=""):
        self.id         = node_id
        self.type       = node_type
        self.name       = name
        self.x          = 0
        self.y          = 0
        self.properties = {}
        self.next_nodes = []

    # ------------------------------------------------------------------
    # Port declarations  (override in subclasses)
    # ------------------------------------------------------------------

    def get_input_ports(self) -> dict:
        return {}

    def get_output_ports(self) -> dict:
        return {}

    # ------------------------------------------------------------------
    # Unified value accessors  (override in subclasses)
    # ------------------------------------------------------------------

    def get_port_value(self, port_name):
        """Return the current value for *port_name* (input or output)."""
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        """Accept a value delivered by a wire into input port *port_name*."""
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    # ------------------------------------------------------------------
    # Preview / display
    # ------------------------------------------------------------------

    @abstractmethod
    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        pass

    @abstractmethod
    def get_preview_display_color(self):
        pass

    def get_flowchart_display_text(self):
        return f"{self.type}\n{self.name}"

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self):
        return {
            'id':         self.id,
            'type':       self.type,
            'name':       self.name,
            'x':          self.x,
            'y':          self.y,
            'properties': self.properties,
        }
