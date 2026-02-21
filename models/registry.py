"""
Node registry and factory functions for creating nodes by type name or dict.
"""

from .geometry     import PointNode, LinkNode, ShapeNode
from .parameters   import InputParameterNode, OutputParameterNode, TargetParameterNode
from .targets      import SurfaceTargetNode, ElevationTargetNode, OffsetTargetNode
from .typed_inputs import (IntegerInputNode, DoubleInputNode, StringInputNode,
                           GradeInputNode, SlopeInputNode,
                           YesNoInputNode, SuperelevationInputNode)
from .workflow     import StartNode, DecisionNode, VariableNode, GenericNode
from .math_nodes   import (
    AddNode, SubtractNode, MultiplyNode, DivideNode, ModuloNode, PowerNode,
    AbsNode, NegateNode, SqrtNode, CeilNode, FloorNode, RoundNode,
    SinNode, CosNode, TanNode, AsinNode, AcosNode, AtanNode, Atan2Node,
    LogNode, Log10Node, ExpNode,
    MinNode, MaxNode, ClampNode,
    InterpolateNode, MapRangeNode,
)
from .logic_nodes  import (
    AndNode, OrNode, NotNode, XorNode, NandNode, NorNode,
    EqualNode, NotEqualNode, GreaterNode, GreaterEqualNode,
    LessNode, LessEqualNode,
    IfElseNode, SwitchNode, AllNode, AnyNode,
)


# Maps the node's 'type' string to its class for serialization/deserialization.
NODE_REGISTRY = {
    # Geometry
    'Point':    PointNode,
    'Link':     LinkNode,
    'Shape':    ShapeNode,
    # Workflow
    'Decision': DecisionNode,
    'Variable': VariableNode,
    'Start':    StartNode,
    # Parameters
    'Input':    InputParameterNode,
    'Output':   OutputParameterNode,
    'Target':   TargetParameterNode,   # legacy – kept for old JSON files
    # Target nodes (new)
    'Surface Target':   SurfaceTargetNode,
    'Elevation Target': ElevationTargetNode,
    'Offset Target':    OffsetTargetNode,
    # Typed inputs
    'Integer Input':        IntegerInputNode,
    'Double Input':         DoubleInputNode,
    'String Input':         StringInputNode,
    'Grade Input':          GradeInputNode,
    'Slope Input':          SlopeInputNode,
    'Yes\\No Input':        YesNoInputNode,
    'Superelevation Input': SuperelevationInputNode,
    # Math — Arithmetic
    'Add':      AddNode,
    'Subtract': SubtractNode,
    'Multiply': MultiplyNode,
    'Divide':   DivideNode,
    'Modulo':   ModuloNode,
    'Power':    PowerNode,
    # Math — Unary
    'Abs':    AbsNode,
    'Negate': NegateNode,
    'Sqrt':   SqrtNode,
    'Ceil':   CeilNode,
    'Floor':  FloorNode,
    'Round':  RoundNode,
    # Math — Trigonometry
    'Sin':   SinNode,
    'Cos':   CosNode,
    'Tan':   TanNode,
    'Asin':  AsinNode,
    'Acos':  AcosNode,
    'Atan':  AtanNode,
    'Atan2': Atan2Node,
    # Math — Logarithm / Exponential
    'Ln':    LogNode,
    'Log10': Log10Node,
    'Exp':   ExpNode,
    # Math — Comparison
    'Min':   MinNode,
    'Max':   MaxNode,
    'Clamp': ClampNode,
    # Math — Utility
    'Interpolate': InterpolateNode,
    'Map Range':   MapRangeNode,
    # Logic — Boolean
    'And':  AndNode,
    'Or':   OrNode,
    'Not':  NotNode,
    'Xor':  XorNode,
    'Nand': NandNode,
    'Nor':  NorNode,
    # Logic — Comparison
    'Equal':         EqualNode,
    'Not Equal':     NotEqualNode,
    'Greater':       GreaterNode,
    'Greater Equal': GreaterEqualNode,
    'Less':          LessNode,
    'Less Equal':    LessEqualNode,
    # Logic — Utility
    'If Else': IfElseNode,
    'Switch':  SwitchNode,
    'All':     AllNode,
    'Any':     AnyNode,
}


def create_node_from_type(node_type: str, node_id: str, name: str = ""):
    """Instantiate a node by its type string. Falls back to GenericNode."""
    cls = NODE_REGISTRY.get(node_type)
    return cls(node_id, name) if cls else GenericNode(node_id, node_type, name)


def create_node_from_dict(data: dict):
    """Deserialize a node from a saved dict. Falls back to GenericNode."""
    node_type = data.get('type')
    cls       = NODE_REGISTRY.get(node_type)
    if cls is None:
        node            = GenericNode(data['id'], node_type, data.get('name', ''))
        node.x          = data.get('x', 0)
        node.y          = data.get('y', 0)
        node.properties = data.get('properties', {})
        return node
    return cls.from_dict(data)
