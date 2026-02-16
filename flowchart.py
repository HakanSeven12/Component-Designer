"""
Flowchart Module for Component Designer
Contains flowchart scene, view, and connection items
"""

from PySide2.QtWidgets import QGraphicsScene, QGraphicsPathItem, QGraphicsView
from PySide2.QtCore import Qt, Signal, QPointF
from PySide2.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath
from models import PointNode, LinkNode, ShapeNode, DecisionNode, FlowchartNode
from base_graphics_view import BaseGraphicsView
from node import FlowchartNodeItem


class ConnectionWire(QGraphicsPathItem):
    """Bezier curve connection between ports"""
    
    def __init__(self, start_pos, end_pos, parent=None):
        super().__init__(parent)
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.from_node = None
        self.to_node = None
        
        # Style
        pen = QPen(QColor(100, 100, 100), 3)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)
        
        self.update_path()
        self.setZValue(-1)
    
    def update_path(self):
        """Update bezier curve path"""
        path = QPainterPath()
        path.moveTo(self.start_pos)
        
        # Calculate control points for smooth curve
        dx = self.end_pos.x() - self.start_pos.x()
        
        ctrl1 = QPointF(self.start_pos.x() + abs(dx) * 0.5, self.start_pos.y())
        ctrl2 = QPointF(self.end_pos.x() - abs(dx) * 0.5, self.end_pos.y())
        
        path.cubicTo(ctrl1, ctrl2, self.end_pos)
        self.setPath(path)
    
    def set_end_pos(self, pos):
        """Update end position (for dragging)"""
        self.end_pos = pos
        self.update_path()


class FlowchartScene(QGraphicsScene):
    """Custom scene for flowchart editing"""
    
    node_selected = Signal(object)
    preview_update_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.nodes = {}
        self.connections = []
        self.port_wires = []  # Store port-based connections
        self.selected_node = None
        self.last_added_node = None
        
        # Connection state
        self.connection_in_progress = False
        self.connection_start_item = None
        self.connection_start_port = None
        self.temp_wire = None
    
    def can_connect_ports(self, from_port_type, to_port_type):
        """Check if two port types can be connected
        
        Valid connections - from output ports to input ports:
        - 'from' -> 'to' (Point OUT to Point IN)
        - 'from' -> 'start' (Point OUT to Link START IN)
        - 'from' -> 'end' (Point OUT to Link END IN)
        """
        valid_connections = [
            ('from', 'to'),      # Point OUT to Point IN
            ('from', 'start'),   # Point OUT to Link START IN
            ('from', 'end'),     # Point OUT to Link END IN
        ]
        return (from_port_type, to_port_type) in valid_connections
        
    def handle_port_click(self, node_item, port_type):
        """Handle port click for connection"""
        # Check if this is an input or output port
        is_output = port_type in node_item.node.get_output_ports()
        is_input = port_type in node_item.node.get_input_ports()
        
        if not self.connection_in_progress:
            # Start connection only from output ports
            if is_output:
                self.start_connection(node_item, port_type)
        else:
            # Finish connection at input ports
            if is_input and node_item != self.connection_start_item:
                # Check if connection is valid
                if self.can_connect_ports(self.connection_start_port, port_type):
                    self.finish_connection(node_item, port_type)
                else:
                    # Invalid connection
                    self.cancel_connection()
            else:
                # Cancel connection
                self.cancel_connection()
    
    def start_connection(self, node_item, port_type):
        """Start creating a connection - only from output ports"""
        # Only allow starting connections from output ports
        if port_type not in node_item.node.get_output_ports():
            return
            
        self.connection_in_progress = True
        self.connection_start_item = node_item
        self.connection_start_port = port_type
        
        # Create temporary wire
        start_pos = node_item.get_port_scene_pos(port_type)
        self.temp_wire = ConnectionWire(start_pos, start_pos)
        self.addItem(self.temp_wire)
    
    def finish_connection(self, node_item, port_type):
        """Finish creating a connection"""
        if not self.connection_in_progress:
            return
        
        # Create permanent wire
        start_pos = self.connection_start_item.get_port_scene_pos(self.connection_start_port)
        end_pos = node_item.get_port_scene_pos(port_type)
        
        wire = ConnectionWire(start_pos, end_pos)
        wire.from_node = self.connection_start_item.node
        wire.to_node = node_item.node
        wire.from_port = self.connection_start_port
        wire.to_port = port_type
        self.addItem(wire)
        self.port_wires.append({
            'wire': wire,
            'from_item': self.connection_start_item,
            'to_item': node_item,
            'from_port': self.connection_start_port,
            'to_port': port_type
        })
        
        # Update node references based on connection type
        from models import PointNode, LinkNode
        if isinstance(node_item.node, PointNode) and port_type == 'to':
            # Point receiving connection
            node_item.node.from_point = self.connection_start_item.node.id
        elif isinstance(node_item.node, LinkNode):
            # Link receiving connection
            if port_type == 'start':
                node_item.node.start_point = self.connection_start_item.node.id
            elif port_type == 'end':
                node_item.node.end_point = self.connection_start_item.node.id
        
        # Store connection data
        self.connections.append({
            'from': self.connection_start_item.node.id,
            'to': node_item.node.id,
            'from_port': self.connection_start_port,
            'to_port': port_type
        })
        
        # Clean up
        if self.temp_wire:
            self.removeItem(self.temp_wire)
            self.temp_wire = None
        
        self.connection_in_progress = False
        self.connection_start_item = None
        self.connection_start_port = None
        
        # Update preview
        self.request_preview_update()
    
    def cancel_connection(self):
        """Cancel connection in progress"""
        if self.temp_wire:
            self.removeItem(self.temp_wire)
            self.temp_wire = None
        
        self.connection_in_progress = False
        self.connection_start_item = None
        self.connection_start_port = None
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for connection preview"""
        if self.connection_in_progress and self.temp_wire:
            self.temp_wire.set_end_pos(event.scenePos())
        super().mouseMoveEvent(event)
    
    def add_flowchart_node(self, node, x, y):
        """Add a node to the flowchart"""
        self.nodes[node.id] = node
        node.x = x
        node.y = y
        
        # Create draggable node item AT THE SPECIFIED POSITION
        node_item = FlowchartNodeItem(node, x, y)
        self.addItem(node_item)
        
        # Auto-connect to previous node if it's a Point node
        from models import StartNode, PointNode
        if isinstance(node, PointNode) and self.last_added_node:
            # Check if last node has output ports
            if self.last_added_node.get_output_ports():
                # Find node items
                last_item = None
                current_item = None
                
                for item in self.items():
                    if isinstance(item, FlowchartNodeItem):
                        if item.node == self.last_added_node:
                            last_item = item
                        elif item.node == node:
                            current_item = item
                
                # Create auto connection from 'from' to 'to'
                if (last_item and current_item and 
                    'from' in last_item.ports and 'to' in current_item.ports):
                    start_pos = last_item.get_port_scene_pos('from')
                    end_pos = current_item.get_port_scene_pos('to')
                    
                    wire = ConnectionWire(start_pos, end_pos)
                    wire.from_node = last_item.node
                    wire.to_node = current_item.node
                    wire.from_port = 'from'
                    wire.to_port = 'to'
                    self.addItem(wire)
                    self.port_wires.append({
                        'wire': wire,
                        'from_item': last_item,
                        'to_item': current_item,
                        'from_port': 'from',
                        'to_port': 'to'
                    })
                    
                    # Update node's from_point reference
                    node.from_point = self.last_added_node.id
                    
                    # Store connection data
                    self.connections.append({
                        'from': self.last_added_node.id,
                        'to': node.id,
                        'from_port': 'from',
                        'to_port': 'to'
                    })
        
        # Update last added node (don't update for START nodes)
        if not isinstance(node, StartNode):
            self.last_added_node = node
        
        return node_item
    def delete_selected_node(self):
        """Delete the currently selected node and its connections"""
        from models import StartNode
        
        # Find selected node item
        selected_items = [item for item in self.selectedItems() 
                        if isinstance(item, FlowchartNodeItem)]
        
        if not selected_items:
            return False
        
        node_item = selected_items[0]
        node = node_item.node
        
        # Don't allow deleting START node
        if isinstance(node, StartNode):
            return False
        
        # Remove all connections involving this node
        wires_to_remove = []
        for wire_data in self.port_wires:
            if wire_data['from_item'] == node_item or wire_data['to_item'] == node_item:
                wires_to_remove.append(wire_data)
        
        for wire_data in wires_to_remove:
            self.removeItem(wire_data['wire'])
            self.port_wires.remove(wire_data)
        
        # Remove from connections list
        connections_to_remove = []
        for conn in self.connections:
            if conn['from'] == node.id or conn['to'] == node.id:
                connections_to_remove.append(conn)
        
        for conn in connections_to_remove:
            self.connections.remove(conn)
        
        # Remove node from nodes dict
        if node.id in self.nodes:
            del self.nodes[node.id]
        
        # Remove graphics item from scene
        self.removeItem(node_item)
        
        # Update last_added_node if this was it
        if self.last_added_node == node:
            self.last_added_node = None
        
        # Request preview update
        self.request_preview_update()
        
        return True
    
    def update_port_wires(self, moved_node_item):
        """Update wire positions when a node is moved"""
        for wire_data in self.port_wires:
            if wire_data['from_item'] == moved_node_item:
                # Update start position
                new_start_pos = moved_node_item.get_port_scene_pos(wire_data['from_port'])
                wire_data['wire'].start_pos = new_start_pos
                wire_data['wire'].update_path()
            
            if wire_data['to_item'] == moved_node_item:
                # Update end position
                new_end_pos = moved_node_item.get_port_scene_pos(wire_data['to_port'])
                wire_data['wire'].end_pos = new_end_pos
                wire_data['wire'].update_path()
    
    def request_preview_update(self):
        """Request preview update"""
        self.preview_update_requested.emit()
    
    def connect_nodes_with_wire(self, from_node, to_node, from_port='from', to_port='to'):
        """Create wire connection between two nodes (used when loading from file)"""
        # Find the graphics items for these nodes
        from_item = None
        to_item = None
        
        for item in self.items():
            if isinstance(item, FlowchartNodeItem):
                if item.node == from_node:
                    from_item = item
                elif item.node == to_node:
                    to_item = item
        
        # Create wire if both items have the required ports
        if (from_item and to_item and 
            from_port in from_item.ports and to_port in to_item.ports):
            
            start_pos = from_item.get_port_scene_pos(from_port)
            end_pos = to_item.get_port_scene_pos(to_port)
            
            wire = ConnectionWire(start_pos, end_pos)
            wire.from_node = from_node
            wire.to_node = to_node
            wire.from_port = from_port
            wire.to_port = to_port
            self.addItem(wire)
            self.port_wires.append({
                'wire': wire,
                'from_item': from_item,
                'to_item': to_item,
                'from_port': from_port,
                'to_port': to_port
            })
            
            # Update node references
            from models import PointNode, LinkNode
            if isinstance(to_node, PointNode) and to_port == 'to':
                to_node.from_point = from_node.id
            elif isinstance(to_node, LinkNode):
                if to_port == 'start':
                    to_node.start_point = from_node.id
                elif to_port == 'end':
                    to_node.end_point = from_node.id


class FlowchartView(BaseGraphicsView):
    """Flowchart editor view"""
    
    def __init__(self):
        super().__init__()
        self.scene = FlowchartScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        
        # Enable rubber band selection
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Accept drops
        self.setAcceptDrops(True)
        
        self.node_counter = 0
        
        # Connect scene signals
        self.scene.node_selected.connect(self.on_node_selected)
        
        # Set background
        self.setBackgroundBrush(QBrush(QColor(240, 240, 245)))
        
        # Create START node
        self.create_start_node()
        
    def restore_drag_mode(self):
        """Restore drag mode after panning"""
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
    def select_node_visually(self, node):
        """Select a node visually in the flowchart"""
        self.selected_node = node
        
        # Clear all selections first
        for item in self.scene.items():
            if isinstance(item, FlowchartNodeItem):
                item.setSelected(False)
        
        # Select the target node
        for item in self.scene.items():
            if isinstance(item, FlowchartNodeItem) and item.node == node:
                item.setSelected(True)
                # Ensure it's visible
                self.centerOn(item)
                break
            
    def create_start_node(self):
        """Create initial START node"""
        from models import StartNode
        start_node = StartNode("START", "START")
        self.scene.add_flowchart_node(start_node, 50, 50)
        
    def on_node_selected(self, node):
        """Handle node selection"""
        # Emit signal to update properties panel
        self.scene.selected_node = node
        
    def dragEnterEvent(self, event):
        """Handle drag enter"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            
    def dragMoveEvent(self, event):
        """Handle drag move"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        """Handle drop - create node at drop position"""
        if event.mimeData().hasText():
            element_type = event.mimeData().text()
            pos = self.mapToScene(event.pos())
            
            # Create appropriate node type
            node = None
            if element_type == "Point":
                node = self.create_point_node_at(pos.x(), pos.y())
            elif element_type == "Link":
                node = self.create_link_node_at(pos.x(), pos.y())
            elif element_type == "Shape":
                node = self.create_shape_node_at(pos.x(), pos.y())
            elif element_type == "Decision":
                node = self.create_decision_node_at(pos.x(), pos.y())
            elif element_type == "Input Parameter":
                node = self.create_input_parameter_node_at(pos.x(), pos.y())
            elif element_type == "Output Parameter":
                node = self.create_output_parameter_node_at(pos.x(), pos.y())
            elif element_type == "Target Parameter":
                node = self.create_target_parameter_node_at(pos.x(), pos.y())
            elif element_type in ["Variable", "Switch", "Auxiliary Point", 
                                "Auxiliary Line", "Auxiliary Curve", "Mark Point", "Comment"]:
                # Create generic nodes for these types
                node = self.create_generic_node_at(element_type, pos.x(), pos.y())
            
            if node:
                event.acceptProposedAction()
                # Notify that node was created
                if hasattr(self, 'parent') and self.parent():
                    parent = self.parent()
                    # Import here to avoid circular dependency
                    from main_window import ComponentDesigner
                    while parent and not isinstance(parent, ComponentDesigner):
                        parent = parent.parent()
                    if parent and hasattr(parent, 'statusBar'):
                        parent.statusBar().showMessage(f"{element_type} added")
            else:
                event.ignore()
            
    def create_point_node_at(self, x, y):
        """Create point node at specific position"""
        node_id = self.get_next_node_id()
        point = PointNode(node_id, f"P{self.node_counter}")
        self.scene.add_flowchart_node(point, x, y)
        return point
        
    def create_link_node_at(self, x, y):
        """Create link node at specific position"""
        node_id = self.get_next_node_id()
        link = LinkNode(node_id, f"L{self.node_counter}")
        self.scene.add_flowchart_node(link, x, y)
        return link
        
    def create_shape_node_at(self, x, y):
        """Create shape node at specific position"""
        node_id = self.get_next_node_id()
        shape = ShapeNode(node_id, f"S{self.node_counter}")
        self.scene.add_flowchart_node(shape, x, y)
        return shape
        
    def create_decision_node_at(self, x, y):
        """Create decision node at specific position"""
        node_id = self.get_next_node_id()
        decision = DecisionNode(node_id, f"D{self.node_counter}")
        self.scene.add_flowchart_node(decision, x, y)
        return decision
    
    def create_input_parameter_node_at(self, x, y):
        """Create input parameter node at specific position"""
        from models import InputParameterNode
        node_id = self.get_next_node_id()
        node = InputParameterNode(node_id, f"IP{self.node_counter}")
        self.scene.add_flowchart_node(node, x, y)
        return node

    def create_output_parameter_node_at(self, x, y):
        """Create output parameter node at specific position"""
        from models import OutputParameterNode
        node_id = self.get_next_node_id()
        node = OutputParameterNode(node_id, f"OP{self.node_counter}")
        self.scene.add_flowchart_node(node, x, y)
        return node

    def create_target_parameter_node_at(self, x, y):
        """Create target parameter node at specific position"""
        from models import TargetParameterNode
        node_id = self.get_next_node_id()
        node = TargetParameterNode(node_id, f"TP{self.node_counter}")
        self.scene.add_flowchart_node(node, x, y)
        return node
    
    def create_generic_node_at(self, node_type, x, y):
        """Create generic node at specific position"""
        node_id = self.get_next_node_id()
        node = FlowchartNode(node_id, node_type, f"{node_type[0]}{self.node_counter}")
        self.scene.add_flowchart_node(node, x, y)
        return node
        
    def get_next_node_id(self):
        """Generate unique node ID"""
        self.node_counter += 1
        return f"N{self.node_counter:04d}"
        
    def add_point_node(self):
        """Add a point node to flowchart"""
        node_id = self.get_next_node_id()
        point = PointNode(node_id, f"P{self.node_counter}")
        
        x = 50 + (self.node_counter * 150) % 600
        y = 50 + ((self.node_counter * 150) // 600) * 100
        
        self.scene.add_flowchart_node(point, x, y)
        return point
        
    def add_link_node(self):
        """Add a link node to flowchart"""
        node_id = self.get_next_node_id()
        link = LinkNode(node_id, f"L{self.node_counter}")
        
        x = 50 + (self.node_counter * 150) % 600
        y = 50 + ((self.node_counter * 150) // 600) * 100
        
        self.scene.add_flowchart_node(link, x, y)
        return link
        
    def add_shape_node(self):
        """Add a shape node to flowchart"""
        node_id = self.get_next_node_id()
        shape = ShapeNode(node_id, f"S{self.node_counter}")
        
        x = 50 + (self.node_counter * 150) % 600
        y = 50 + ((self.node_counter * 150) // 600) * 100
        
        self.scene.add_flowchart_node(shape, x, y)
        return shape
        
    def add_decision_node(self):
        """Add a decision node to flowchart"""
        node_id = self.get_next_node_id()
        decision = DecisionNode(node_id, f"D{self.node_counter}")
        
        x = 50 + (self.node_counter * 150) % 600
        y = 50 + ((self.node_counter * 150) // 600) * 100
        
        self.scene.add_flowchart_node(decision, x, y)
        return decision