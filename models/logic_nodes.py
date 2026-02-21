"""
Logic / boolean operation nodes for Component Designer.

Provides comparison, boolean algebra, and conditional nodes that can
be wired together in the flowchart to compute branching or gating logic.

Node categories
---------------
Boolean   : AndNode, OrNode, NotNode, XorNode, NandNode, NorNode
Comparison: EqualNode, NotEqualNode, GreaterNode, GreaterEqualNode,
            LessNode, LessEqualNode
Utility   : IfElseNode, SwitchNode, AllNode, AnyNode
"""

from PySide2.QtGui import QColor
from .base import FlowchartNode, port


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_bool(v) -> bool:
    """Coerce any port value to bool (0 / 0.0 / None / False → False)."""
    if v is None:
        return False
    return bool(v)


# ---------------------------------------------------------------------------
# Abstract base shared by all logic nodes
# ---------------------------------------------------------------------------

class _LogicNode(FlowchartNode):
    """
    Abstract base for logic nodes.

    Subclasses override:
        _input_names : tuple[str, ...]   — ordered input port names
        _output_name : str               — single output port name
        _output_type : str               — 'bool' or 'float'
        _compute(*args)                  — core calculation
    """

    _input_names: tuple = ()
    _output_name: str   = "result"
    _output_type: str   = "bool"

    def __init__(self, node_id, node_type, name=""):
        super().__init__(node_id, node_type, name)
        for n in self._input_names:
            setattr(self, n, False)

    # -- Port declarations ---------------------------------------------------

    def get_input_ports(self) -> dict:
        return {n: "bool" for n in self._input_names}

    def get_output_ports(self) -> dict:
        return {self._output_name: self._output_type}

    # -- Value accessors -----------------------------------------------------

    def get_port_value(self, port_name):
        if port_name == self._output_name:
            args = [getattr(self, n, False) for n in self._input_names]
            return self._compute(*args)
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    # -- Compute (override in subclass) -------------------------------------

    def _compute(self, *args):
        raise NotImplementedError

    # -- Preview / theme -----------------------------------------------------

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(255, 180, 60)

    # -- Serialization -------------------------------------------------------

    def to_dict(self):
        d = super().to_dict()
        for n in self._input_names:
            d[n] = getattr(self, n, False)
        return d

    @classmethod
    def from_dict(cls, data):
        node   = cls(data["id"], data.get("name", ""))
        node.x = data.get("x", 0)
        node.y = data.get("y", 0)
        for n in cls._input_names:
            raw = data.get(n, False)
            # Accept bool, int, or float coming from JSON
            if isinstance(raw, float):
                raw = bool(raw)
            setattr(node, n, raw)
        return node


# ===========================================================================
# Boolean nodes
# ===========================================================================

class AndNode(_LogicNode):
    """Outputs A AND B (true only when both inputs are true)."""
    _input_names = ("a", "b")
    _output_name = "result"
    _output_type = "bool"
    def __init__(self, node_id, name=""): super().__init__(node_id, "And", name)
    def _compute(self, a, b): return _to_bool(a) and _to_bool(b)


class OrNode(_LogicNode):
    """Outputs A OR B (true when at least one input is true)."""
    _input_names = ("a", "b")
    _output_name = "result"
    _output_type = "bool"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Or", name)
    def _compute(self, a, b): return _to_bool(a) or _to_bool(b)


class NotNode(_LogicNode):
    """Outputs NOT value (inverts the boolean input)."""
    _input_names = ("value",)
    _output_name = "result"
    _output_type = "bool"
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Not", name)
        self.value = False
    def _compute(self, value): return not _to_bool(value)


class XorNode(_LogicNode):
    """Outputs A XOR B (true when exactly one input is true)."""
    _input_names = ("a", "b")
    _output_name = "result"
    _output_type = "bool"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Xor", name)
    def _compute(self, a, b): return _to_bool(a) ^ _to_bool(b)


class NandNode(_LogicNode):
    """Outputs NOT (A AND B)."""
    _input_names = ("a", "b")
    _output_name = "result"
    _output_type = "bool"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Nand", name)
    def _compute(self, a, b): return not (_to_bool(a) and _to_bool(b))


class NorNode(_LogicNode):
    """Outputs NOT (A OR B)."""
    _input_names = ("a", "b")
    _output_name = "result"
    _output_type = "bool"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Nor", name)
    def _compute(self, a, b): return not (_to_bool(a) or _to_bool(b))


# ===========================================================================
# Comparison nodes  (numeric inputs → boolean output)
# ===========================================================================

class _CompareNode(_LogicNode):
    """
    Base for two-input numeric comparison nodes.
    Inputs are coerced to float before comparison.
    """

    def get_input_ports(self) -> dict:
        # Override to use float inputs instead of bool
        return {n: "float" for n in self._input_names}

    def get_port_value(self, port_name):
        if port_name == self._output_name:
            a = float(getattr(self, self._input_names[0], 0.0) or 0.0)
            b = float(getattr(self, self._input_names[1], 0.0) or 0.0)
            return self._compare(a, b)
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, float(value) if value is not None else 0.0)

    def _compare(self, a: float, b: float) -> bool:
        raise NotImplementedError

    def _compute(self, *args):
        return self._compare(*args)

    def to_dict(self):
        d = super(FlowchartNode, self).to_dict(self) if False else FlowchartNode.to_dict(self)
        for n in self._input_names:
            d[n] = float(getattr(self, n, 0.0))
        return d

    @classmethod
    def from_dict(cls, data):
        node   = cls(data["id"], data.get("name", ""))
        node.x = data.get("x", 0)
        node.y = data.get("y", 0)
        for n in cls._input_names:
            setattr(node, n, float(data.get(n, 0.0)))
        return node


class EqualNode(_CompareNode):
    """Outputs true when A == B (within floating-point tolerance)."""
    _input_names = ("a", "b")
    _output_name = "result"
    _output_type = "bool"
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Equal", name)
        self.a = 0.0
        self.b = 0.0
    def _compare(self, a, b): return abs(a - b) < 1e-9


class NotEqualNode(_CompareNode):
    """Outputs true when A != B."""
    _input_names = ("a", "b")
    _output_name = "result"
    _output_type = "bool"
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Not Equal", name)
        self.a = 0.0
        self.b = 0.0
    def _compare(self, a, b): return abs(a - b) >= 1e-9


class GreaterNode(_CompareNode):
    """Outputs true when A > B."""
    _input_names = ("a", "b")
    _output_name = "result"
    _output_type = "bool"
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Greater", name)
        self.a = 0.0
        self.b = 0.0
    def _compare(self, a, b): return a > b


class GreaterEqualNode(_CompareNode):
    """Outputs true when A >= B."""
    _input_names = ("a", "b")
    _output_name = "result"
    _output_type = "bool"
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Greater Equal", name)
        self.a = 0.0
        self.b = 0.0
    def _compare(self, a, b): return a >= b


class LessNode(_CompareNode):
    """Outputs true when A < B."""
    _input_names = ("a", "b")
    _output_name = "result"
    _output_type = "bool"
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Less", name)
        self.a = 0.0
        self.b = 0.0
    def _compare(self, a, b): return a < b


class LessEqualNode(_CompareNode):
    """Outputs true when A <= B."""
    _input_names = ("a", "b")
    _output_name = "result"
    _output_type = "bool"
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Less Equal", name)
        self.a = 0.0
        self.b = 0.0
    def _compare(self, a, b): return a <= b


# ===========================================================================
# Utility nodes
# ===========================================================================

class IfElseNode(FlowchartNode):
    """
    Returns *true_val* when *condition* is truthy, else *false_val*.
    Inputs and outputs are float so numeric values can be routed
    through conditional logic without additional cast nodes.
    """

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "If Else", name)
        self.condition  = False
        self.true_val   = 1.0
        self.false_val  = 0.0

    def get_input_ports(self) -> dict:
        return {
            "condition": "bool",
            "true_val":  port("float", editor=True),
            "false_val": port("float", editor=True),
        }

    def get_output_ports(self) -> dict:
        return {"result": port("float", editor=False)}

    def get_port_value(self, port_name):
        if port_name == "result":
            return self.true_val if _to_bool(self.condition) else self.false_val
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if port_name == "condition":
            self.condition = _to_bool(value)
        elif port_name in ("true_val", "false_val"):
            setattr(self, port_name, float(value) if value is not None else 0.0)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(255, 180, 60)

    def to_dict(self):
        d = super().to_dict()
        d["condition"]  = self.condition
        d["true_val"]   = self.true_val
        d["false_val"]  = self.false_val
        return d

    @classmethod
    def from_dict(cls, data):
        node            = cls(data["id"], data.get("name", ""))
        node.x          = data.get("x", 0)
        node.y          = data.get("y", 0)
        node.condition  = bool(data.get("condition", False))
        node.true_val   = float(data.get("true_val",  1.0))
        node.false_val  = float(data.get("false_val", 0.0))
        return node


class SwitchNode(FlowchartNode):
    """
    Routes one of two float inputs to the output based on a boolean switch.
    When *enabled* is true → passes *on_val*; otherwise passes *off_val*.
    Semantically identical to IfElse but labelled for signal-routing intent.
    """

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Switch", name)
        self.enabled  = False
        self.on_val   = 1.0
        self.off_val  = 0.0

    def get_input_ports(self) -> dict:
        return {
            "enabled": "bool",
            "on_val":  port("float", editor=True),
            "off_val": port("float", editor=True),
        }

    def get_output_ports(self) -> dict:
        return {"result": port("float", editor=False)}

    def get_port_value(self, port_name):
        if port_name == "result":
            return self.on_val if _to_bool(self.enabled) else self.off_val
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if port_name == "enabled":
            self.enabled = _to_bool(value)
        elif port_name in ("on_val", "off_val"):
            setattr(self, port_name, float(value) if value is not None else 0.0)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(255, 160, 40)

    def to_dict(self):
        d = super().to_dict()
        d["enabled"]  = self.enabled
        d["on_val"]   = self.on_val
        d["off_val"]  = self.off_val
        return d

    @classmethod
    def from_dict(cls, data):
        node          = cls(data["id"], data.get("name", ""))
        node.x        = data.get("x", 0)
        node.y        = data.get("y", 0)
        node.enabled  = bool(data.get("enabled", False))
        node.on_val   = float(data.get("on_val",  1.0))
        node.off_val  = float(data.get("off_val", 0.0))
        return node


class AllNode(_LogicNode):
    """
    Outputs true only when ALL three boolean inputs are true.
    Useful for multi-condition gates without chaining multiple AND nodes.
    """
    _input_names = ("a", "b", "c")
    _output_name = "result"
    _output_type = "bool"

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "All", name)
        self.a = False
        self.b = False
        self.c = False

    def _compute(self, a, b, c):
        return _to_bool(a) and _to_bool(b) and _to_bool(c)


class AnyNode(_LogicNode):
    """
    Outputs true when ANY of the three boolean inputs is true.
    Useful for multi-source OR gates.
    """
    _input_names = ("a", "b", "c")
    _output_name = "result"
    _output_type = "bool"

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Any", name)
        self.a = False
        self.b = False
        self.c = False

    def _compute(self, a, b, c):
        return _to_bool(a) or _to_bool(b) or _to_bool(c)
