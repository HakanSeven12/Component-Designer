"""
Base classes and shared enums for Component Designer models.

Port definition format
----------------------
Each port in get_input_ports() / get_output_ports() maps a port name to
one of the following values:

  None
      Node-ref port — no type, no editor, just a connection dot.

  'float' | 'int' | 'string' | 'bool' | 'percent'
      Plain scalar string (legacy / shorthand).
      Equivalent to {'type': 'float', 'editor': True}.

  {'type': 'float', 'editor': True}
      Explicit dict form — preferred for new code.
      'editor' key is optional and defaults to True.

  {'type': 'float', 'editor': False}
      Port has a known type and can be wired, but no inline editor
      widget is rendered.  The row shows dot + label only.

  [{'label': '...', 'value': ...}, ...]
      Combo-box options list.  Rendered as a ComboField, not a PortRow.

Convenience helpers
-------------------
  port('float')                    → {'type': 'float', 'editor': True}
  port('float', editor=False)      → {'type': 'float', 'editor': False}
  unpack_port(any_form)            → (type_str_or_none, editor: bool)
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

#: Scalar type strings recognised by the editor factory in node.py.
SCALAR_TYPES = frozenset(('float', 'int', 'string', 'bool', 'percent'))


def port(ptype, editor=False):
    """
    Convenience constructor that returns a port-definition dict.

    Prefer this over writing raw dicts so the call sites read naturally
    and typos in key names are avoided:

        'delta_x':  port('float')                 # spinbox shown (default)
        'x':        port('float', editor=False)   # dot + label only
        'add_link': port('bool',  editor=False)   # dot + label only

    Parameters
    ----------
    ptype : str
        One of the SCALAR_TYPES strings.
    editor : bool
        When False the inline editor widget is suppressed; the port row
        still renders its dot and label so the port remains wireable.

    Returns
    -------
    dict  {'type': ptype, 'editor': bool}
    """
    return {'type': ptype, 'editor': bool(editor)}


def unpack_port(port_def):
    """
    Normalise any port definition to the canonical ``(type, editor)`` pair.

    Parameters
    ----------
    port_def : None | str | dict | list

    Returns
    -------
    type_str : str | list | None
    editor   : bool   — True when an inline editor widget should be shown

    Conversion table
    ----------------
    None                                → (None,   False)
    'float'          (plain string)     → ('float', True)
    {'type': 'float'}                   → ('float', True)   editor defaults True
    {'type': 'float', 'editor': False}  → ('float', False)
    [{'label':…, 'value':…}, …]        → (list,    False)   combo field
    """
    if port_def is None:
        return None, False

    if isinstance(port_def, list):
        # Combo-box options list — rendered as ComboField, not a PortRow editor
        return port_def, False

    if isinstance(port_def, dict):
        ptype  = port_def.get('type', None)
        editor = port_def.get('editor', False)
        return ptype, bool(editor)

    # Plain string shorthand: 'float', 'int', 'string', 'bool', 'percent'
    return port_def, False


def port_type(port_def):
    """Return the type string (or None / list) for *port_def*."""
    t, _ = unpack_port(port_def)
    return t


def port_editor(port_def) -> bool:
    """Return True when the port definition requests an inline editor."""
    _, ed = unpack_port(port_def)
    return ed


# ---------------------------------------------------------------------------
# Abstract base node
# ---------------------------------------------------------------------------

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
