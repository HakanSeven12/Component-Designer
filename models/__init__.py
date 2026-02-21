"""
models package — re-exports every public symbol so existing imports like
    from .models import PointNode, create_node_from_dict
continue to work without modification.
"""

# --- Enums & helpers ---------------------------------------------------------
from .base import (
    PointGeometryType,
    LinkType,
    TargetType,
    DataType,
    FlowchartNode,
)

# --- Geometry ----------------------------------------------------------------
from .geometry import (
    PointNode,
    LinkNode,
    ShapeNode,
)

# --- Parameters --------------------------------------------------------------
from .parameters import (
    InputParameterNode,
    OutputParameterNode,
    TargetParameterNode,   # kept for backward-compat with old JSON files
)

# --- Target nodes (specialised) ----------------------------------------------
from .targets import (
    SurfaceTargetNode,
    ElevationTargetNode,
    OffsetTargetNode,
)

# --- Typed inputs ------------------------------------------------------------
from .typed_inputs import (
    IntegerInputNode,
    DoubleInputNode,
    StringInputNode,
    GradeInputNode,
    SlopeInputNode,
    YesNoInputNode,
    SuperelevationInputNode,
)

# --- Math nodes --------------------------------------------------------------
from .math_nodes import (
    # Arithmetic
    AddNode, SubtractNode, MultiplyNode, DivideNode, ModuloNode, PowerNode,
    # Unary
    AbsNode, NegateNode, SqrtNode, CeilNode, FloorNode, RoundNode,
    # Trigonometry
    SinNode, CosNode, TanNode, AsinNode, AcosNode, AtanNode, Atan2Node,
    # Logarithm / exponential
    LogNode, Log10Node, ExpNode,
    # Comparison
    MinNode, MaxNode, ClampNode,
    # Utility
    InterpolateNode, MapRangeNode,
)

# --- Logic nodes -------------------------------------------------------------
from .logic_nodes import (
    # Boolean
    AndNode, OrNode, NotNode, XorNode, NandNode, NorNode,
    # Comparison
    EqualNode, NotEqualNode, GreaterNode, GreaterEqualNode,
    LessNode, LessEqualNode,
    # Utility
    IfElseNode, SwitchNode, AllNode, AnyNode,
)

# --- Workflow ----------------------------------------------------------------
from .workflow import (
    StartNode,
    DecisionNode,
    VariableNode,
    GenericNode,
)

# --- Registry & factories ----------------------------------------------------
from .registry import (
    NODE_REGISTRY,
    create_node_from_type,
    create_node_from_dict,
)

__all__ = [
    # enums
    "PointGeometryType", "LinkType", "TargetType", "DataType",
    # base
    "FlowchartNode",
    # geometry
    "PointNode", "LinkNode", "ShapeNode",
    # parameters
    "InputParameterNode", "OutputParameterNode", "TargetParameterNode",
    # targets
    "SurfaceTargetNode", "ElevationTargetNode", "OffsetTargetNode",
    # typed inputs
    "IntegerInputNode", "DoubleInputNode", "StringInputNode",
    "GradeInputNode", "SlopeInputNode", "YesNoInputNode",
    "SuperelevationInputNode",
    # math nodes
    "AddNode", "SubtractNode", "MultiplyNode", "DivideNode",
    "ModuloNode", "PowerNode",
    "AbsNode", "NegateNode", "SqrtNode", "CeilNode", "FloorNode", "RoundNode",
    "SinNode", "CosNode", "TanNode", "AsinNode", "AcosNode", "AtanNode", "Atan2Node",
    "LogNode", "Log10Node", "ExpNode",
    "MinNode", "MaxNode", "ClampNode",
    "InterpolateNode", "MapRangeNode",
    # logic nodes
    "AndNode", "OrNode", "NotNode", "XorNode", "NandNode", "NorNode",
    "EqualNode", "NotEqualNode", "GreaterNode", "GreaterEqualNode",
    "LessNode", "LessEqualNode",
    "IfElseNode", "SwitchNode", "AllNode", "AnyNode",
    # workflow
    "StartNode", "DecisionNode", "VariableNode", "GenericNode",
    # registry
    "NODE_REGISTRY", "create_node_from_type", "create_node_from_dict",
]
