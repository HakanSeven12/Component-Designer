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
