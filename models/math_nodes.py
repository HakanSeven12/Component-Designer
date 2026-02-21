"""
Math operation nodes for Component Designer.

Provides arithmetic, comparison, trigonometric, and utility math nodes
that can be wired together in the flowchart to compute derived values.

Node categories
---------------
Arithmetic   : AddNode, SubtractNode, MultiplyNode, DivideNode, ModuloNode, PowerNode
Unary        : AbsNode, NegateNode, SqrtNode, CeilNode, FloorNode, RoundNode
Trigonometry : SinNode, CosNode, TanNode, AsinNode, AcosNode, AtanNode, Atan2Node
Logarithm    : LogNode, Log10Node, ExpNode
Comparison   : MinNode, MaxNode, ClampNode
Utility      : InterpolateNode, MapRangeNode
"""

import math
from PySide2.QtGui import QColor
from .base import FlowchartNode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_div(a, b):
    """Division that returns 0 on division by zero."""
    return (a / b) if b != 0.0 else 0.0


def _safe_sqrt(a):
    """Square root that clamps negative inputs to 0."""
    return math.sqrt(max(0.0, a))


# ---------------------------------------------------------------------------
# Base class shared by all math nodes
# ---------------------------------------------------------------------------

class _MathNode(FlowchartNode):
    """
    Abstract base for math nodes.
    Subclasses only need to override ``_compute(*args) -> float``,
    ``_input_names``, and ``_output_name``.
    """

    # Override in each subclass ↓
    _input_names: tuple = ()       # ordered input port names
    _output_name: str   = "result" # single output port name

    def __init__(self, node_id, node_type, name=""):
        super().__init__(node_id, node_type, name)
        # Every input defaults to 0.0
        for n in self._input_names:
            setattr(self, n, 0.0)

    # -- Port declarations ---------------------------------------------------

    def get_input_ports(self) -> dict:
        return {n: "float" for n in self._input_names}

    def get_output_ports(self) -> dict:
        return {self._output_name: "float"}

    # -- Value accessors -----------------------------------------------------

    def get_port_value(self, port_name):
        if port_name == self._output_name:
            args = [getattr(self, n, 0.0) for n in self._input_names]
            return self._compute(*args)
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, float(value) if value is not None else 0.0)

    # -- Compute (override in subclass) -------------------------------------

    def _compute(self, *args) -> float:  # pragma: no cover
        raise NotImplementedError

    # -- Preview / theme -----------------------------------------------------

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(180, 140, 255)

    # -- Serialization -------------------------------------------------------

    def to_dict(self):
        d = super().to_dict()
        for n in self._input_names:
            d[n] = getattr(self, n, 0.0)
        return d

    @classmethod
    def from_dict(cls, data):
        node   = cls(data["id"], data.get("name", ""))
        node.x = data.get("x", 0)
        node.y = data.get("y", 0)
        for n in cls._input_names:
            setattr(node, n, float(data.get(n, 0.0)))
        return node


# ===========================================================================
# Arithmetic nodes
# ===========================================================================

class AddNode(_MathNode):
    """Outputs A + B."""
    _input_names = ("a", "b")
    _output_name = "sum"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Add", name)
    def _compute(self, a, b): return a + b

class SubtractNode(_MathNode):
    """Outputs A − B."""
    _input_names = ("a", "b")
    _output_name = "difference"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Subtract", name)
    def _compute(self, a, b): return a - b

class MultiplyNode(_MathNode):
    """Outputs A × B."""
    _input_names = ("a", "b")
    _output_name = "product"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Multiply", name)
    def _compute(self, a, b): return a * b

class DivideNode(_MathNode):
    """Outputs A ÷ B (returns 0 when B = 0)."""
    _input_names = ("a", "b")
    _output_name = "quotient"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Divide", name)
    def _compute(self, a, b): return _safe_div(a, b)

class ModuloNode(_MathNode):
    """Outputs A mod B (returns 0 when B = 0)."""
    _input_names = ("a", "b")
    _output_name = "remainder"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Modulo", name)
    def _compute(self, a, b): return (a % b) if b != 0.0 else 0.0

class PowerNode(_MathNode):
    """Outputs A ^ B (base raised to exponent)."""
    _input_names = ("base", "exponent")
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Power", name)
    def _compute(self, base, exponent):
        try:
            return math.pow(base, exponent)
        except (ValueError, OverflowError):
            return 0.0


# ===========================================================================
# Unary nodes (single input)
# ===========================================================================

class AbsNode(_MathNode):
    """Outputs |value|."""
    _input_names = ("value",)
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Abs", name)
    def _compute(self, value): return abs(value)

class NegateNode(_MathNode):
    """Outputs −value."""
    _input_names = ("value",)
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Negate", name)
    def _compute(self, value): return -value

class SqrtNode(_MathNode):
    """Outputs √value (clamps negative input to 0)."""
    _input_names = ("value",)
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Sqrt", name)
    def _compute(self, value): return _safe_sqrt(value)

class CeilNode(_MathNode):
    """Outputs ⌈value⌉ (ceiling)."""
    _input_names = ("value",)
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Ceil", name)
    def _compute(self, value): return float(math.ceil(value))

class FloorNode(_MathNode):
    """Outputs ⌊value⌋ (floor)."""
    _input_names = ("value",)
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Floor", name)
    def _compute(self, value): return float(math.floor(value))

class RoundNode(_MathNode):
    """Rounds value to the nearest integer."""
    _input_names = ("value",)
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Round", name)
    def _compute(self, value): return float(round(value))


# ===========================================================================
# Trigonometry nodes  (angles in degrees)
# ===========================================================================

class SinNode(_MathNode):
    """Outputs sin(degrees)."""
    _input_names = ("degrees",)
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Sin", name)
    def _compute(self, degrees): return math.sin(math.radians(degrees))

class CosNode(_MathNode):
    """Outputs cos(degrees)."""
    _input_names = ("degrees",)
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Cos", name)
    def _compute(self, degrees): return math.cos(math.radians(degrees))

class TanNode(_MathNode):
    """Outputs tan(degrees)."""
    _input_names = ("degrees",)
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Tan", name)
    def _compute(self, degrees):
        try:
            return math.tan(math.radians(degrees))
        except (ValueError, OverflowError):
            return 0.0

class AsinNode(_MathNode):
    """Outputs arcsin(value) in degrees (clamps input to [-1, 1])."""
    _input_names = ("value",)
    _output_name = "degrees"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Asin", name)
    def _compute(self, value):
        return math.degrees(math.asin(max(-1.0, min(1.0, value))))

class AcosNode(_MathNode):
    """Outputs arccos(value) in degrees (clamps input to [-1, 1])."""
    _input_names = ("value",)
    _output_name = "degrees"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Acos", name)
    def _compute(self, value):
        return math.degrees(math.acos(max(-1.0, min(1.0, value))))

class AtanNode(_MathNode):
    """Outputs arctan(value) in degrees."""
    _input_names = ("value",)
    _output_name = "degrees"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Atan", name)
    def _compute(self, value): return math.degrees(math.atan(value))

class Atan2Node(_MathNode):
    """Outputs arctan2(y, x) in degrees (full 360° angle)."""
    _input_names = ("y", "x")
    _output_name = "degrees"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Atan2", name)
    def _compute(self, y, x): return math.degrees(math.atan2(y, x))


# ===========================================================================
# Logarithm / exponential nodes
# ===========================================================================

class LogNode(_MathNode):
    """Outputs natural log ln(value).  Returns 0 for non-positive input."""
    _input_names = ("value",)
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Ln", name)
    def _compute(self, value):
        return math.log(value) if value > 0.0 else 0.0

class Log10Node(_MathNode):
    """Outputs log₁₀(value).  Returns 0 for non-positive input."""
    _input_names = ("value",)
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Log10", name)
    def _compute(self, value):
        return math.log10(value) if value > 0.0 else 0.0

class ExpNode(_MathNode):
    """Outputs e^value."""
    _input_names = ("value",)
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Exp", name)
    def _compute(self, value):
        try:
            return math.exp(value)
        except OverflowError:
            return float("inf")


# ===========================================================================
# Comparison / selection nodes
# ===========================================================================

class MinNode(_MathNode):
    """Outputs min(A, B)."""
    _input_names = ("a", "b")
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Min", name)
    def _compute(self, a, b): return min(a, b)

class MaxNode(_MathNode):
    """Outputs max(A, B)."""
    _input_names = ("a", "b")
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Max", name)
    def _compute(self, a, b): return max(a, b)

class ClampNode(_MathNode):
    """Outputs value clamped to [min_val, max_val]."""
    _input_names = ("value", "min_val", "max_val")
    _output_name = "result"
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Clamp", name)
        self.min_val = 0.0
        self.max_val = 1.0
    def _compute(self, value, min_val, max_val):
        lo, hi = (min_val, max_val) if min_val <= max_val else (max_val, min_val)
        return max(lo, min(hi, value))


# ===========================================================================
# Utility nodes
# ===========================================================================

class InterpolateNode(_MathNode):
    """
    Linear interpolation: outputs A + t*(B - A).
    t = 0 → A,  t = 1 → B,  t between 0 and 1 → blend.
    """
    _input_names = ("a", "b", "t")
    _output_name = "result"
    def __init__(self, node_id, name=""): super().__init__(node_id, "Interpolate", name)
    def _compute(self, a, b, t): return a + t * (b - a)

class MapRangeNode(_MathNode):
    """
    Re-maps a value from [in_min, in_max] into [out_min, out_max].
    Returns out_min when the input range is zero-width.
    """
    _input_names = ("value", "in_min", "in_max", "out_min", "out_max")
    _output_name = "result"
    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Map Range", name)
        self.in_min  = 0.0
        self.in_max  = 1.0
        self.out_min = 0.0
        self.out_max = 1.0
    def _compute(self, value, in_min, in_max, out_min, out_max):
        span = in_max - in_min
        if span == 0.0:
            return out_min
        t = (value - in_min) / span
        return out_min + t * (out_max - out_min)
