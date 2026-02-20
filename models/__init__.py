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
    TargetParameterNode,
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
    # typed inputs
    "IntegerInputNode", "DoubleInputNode", "StringInputNode",
    "GradeInputNode", "SlopeInputNode", "YesNoInputNode",
    "SuperelevationInputNode",
    # workflow
    "StartNode", "DecisionNode", "VariableNode", "GenericNode",
    # registry
    "NODE_REGISTRY", "create_node_from_type", "create_node_from_dict",
]
