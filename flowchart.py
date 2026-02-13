"""
Flowchart Module for Component Designer
Contains flowchart scene, view, and draggable node items
"""

from PySide2.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsRectItem, 
                               QGraphicsTextItem, QGraphicsItem, QGraphicsLineItem, 
                               QGraphicsPolygonItem, QStyle)
from PySide2.QtCore import Qt, Signal, QPointF, QLineF
from PySide2.QtGui import QPainter, QBrush, QColor, QPen, QPolygonF, QMouseEvent
from models import PointNode, LinkNode, ShapeNode, DecisionNode, FlowchartNode


class ConnectionArrow(QGraphicsLineItem):
    """Arrow connecting flowchart nodes"""
    
    def __init__(self, start_item, end_item, parent=None):
        super().__init__(parent)
        self.start_item = start_item
        self.end_item = end_item
        self.arrow_head = QGraphicsPolygonItem(self)
        
        # Style
        self.setPen(QPen(QColor(100, 100, 100), 2))
        self.arrow_head.setBrush(QBrush(QColor(100, 100, 100)))
        self.arrow_head.setPen(QPen(QColor(100, 100, 100)))
        
        self.update_position()
        
    def update_position(self):
        """Update arrow position based on connected nodes"""
        if not self.start_item or not self.end_item:
            return
            
        # Get center points of both items
        start_pos = self.start_item.sceneBoundingRect().center()
        end_pos = self.end_item.sceneBoundingRect().center()
        
        # Set line
        self.setLine(QLineF(start_pos, end_pos))
        
        # Calculate arrow head
        line = self.line()
        angle = line.angle()
        
        # Arrow head points
        arrow_size = 10
        p1 = line.p2()
        
        import math
        angle_rad = math.radians(angle)
        p2 = QPointF(
            p1.x() - arrow_size * math.cos(angle_rad - math.pi / 6),
            p1.y() + arrow_size * math.sin(angle_rad - math.pi / 6)
        )
        p3 = QPointF(
            p1.x() - arrow_size * math.cos(angle_rad + math.pi / 6),
            p1.y() + arrow_size * math.sin(angle_rad + math.pi / 6)
        )
        
        arrow_head_polygon = QPolygonF([p1, p2, p3])
        self.arrow_head.setPolygon(arrow_head_polygon)

class FlowchartNodeItem(QGraphicsRectItem):
    """Draggable flowchart node item"""

    def __init__(self, node, x, y, parent=None):
        super().__init__(0, 0, 120, 60, parent)
        self.node = node
        self.setPos(x, y)
        self.setFlags(QGraphicsItem.ItemIsMovable | 
                     QGraphicsItem.ItemIsSelectable |
                     QGraphicsItem.ItemSendsGeometryChanges)
        
        # Set cache mode to avoid drawing artifacts
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        
        # Visual styling
        self.normal_pen = QPen(QColor(0, 0, 0), 2)
        self.selected_pen = QPen(QColor(255, 120, 0), 3)
        self.normal_brush = QBrush(QColor(200, 220, 255))
        self.selected_brush = QBrush(QColor(255, 230, 180))

        # Add text label - use relative positioning within the rectangle
        self.text = QGraphicsTextItem(f"{node.type}\n{node.name}", self)
        # Center the text within the rectangle
        text_rect = self.text.boundingRect()
        text_x = (120 - text_rect.width()) / 2
        text_y = (60 - text_rect.height()) / 2
        self.text.setPos(text_x, text_y)
        
        # Store node reference
        self.setData(0, node)
        
    def itemChange(self, change, value):
        """Handle item changes - update node position and arrows"""
        if change == QGraphicsItem.ItemPositionChange:
            # Update node position
            new_pos = value
            self.node.x = new_pos.x()
            self.node.y = new_pos.y()
            
            # Update connected arrows
            if self.scene():
                self.scene().update_arrows()
        
        elif change == QGraphicsItem.ItemSelectedChange:
            # Update visual style based on selection
            if value:  # Being selected
                self.setPen(self.selected_pen)
                self.setBrush(self.selected_brush)
            else:  # Being deselected
                self.setPen(self.normal_pen)
                self.setBrush(self.normal_brush)
                
        return super().itemChange(change, value)
    
    def paint(self, painter, option, widget=None):
        """Custom paint to show selection state"""
        # Remove the selection rectangle that Qt draws by default
        option.state &= ~QStyle.State_Selected
        
        # Enable antialiasing
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the rectangle
        if self.isSelected():
            painter.setPen(self.selected_pen)
            painter.setBrush(self.selected_brush)
        else:
            painter.setPen(self.normal_pen)
            painter.setBrush(self.normal_brush)
        
        painter.drawRect(self.rect())
        
        # Draw selection highlight if selected
        if self.isSelected():
            # Draw a glow effect
            glow_pen = QPen(QColor(255, 120, 0, 100), 6)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.rect().adjusted(-3, -3, 3, 3))

    def mousePressEvent(self, event):
        """Handle mouse press - select node"""
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_selected.emit(self.node)
            
    def mouseDoubleClickEvent(self, event):
        """Handle double click - edit node"""
        super().mouseDoubleClickEvent(event)
        if self.scene():
            self.scene().node_selected.emit(self.node)


class FlowchartScene(QGraphicsScene):
    """Custom scene for flowchart editing"""
    
    node_selected = Signal(object)
    
    def __init__(self):
        super().__init__()
        self.nodes = {}
        self.connections = []
        self.arrows = []  # Store arrow items
        self.selected_node = None
        self.last_added_node = None  # Track last added node
        
    def add_flowchart_node(self, node, x, y):
        """Add a node to the flowchart"""
        self.nodes[node.id] = node
        node.x = x
        node.y = y
        
        # Create draggable node item
        node_item = FlowchartNodeItem(node, x, y)
        self.addItem(node_item)
        
        # Connect to previous node if exists
        if self.last_added_node and self.last_added_node != node:
            self.connect_nodes(self.last_added_node, node)
        
        # Update last added node
        self.last_added_node = node
        
        return node_item
        
    def connect_nodes(self, from_node, to_node):
        """Create arrow connection between two nodes"""
        # Find the graphics items for these nodes
        from_item = None
        to_item = None
        
        for item in self.items():
            if isinstance(item, FlowchartNodeItem):
                if item.node == from_node:
                    from_item = item
                elif item.node == to_node:
                    to_item = item
                    
        if from_item and to_item:
            arrow = ConnectionArrow(from_item, to_item)
            self.addItem(arrow)
            self.arrows.append(arrow)
            arrow.setZValue(-1)  # Put arrows behind nodes
            
            # Store connection data
            self.connections.append({
                'from': from_node.id,
                'to': to_node.id
            })
            
    def update_arrows(self):
        """Update all arrow positions"""
        for arrow in self.arrows:
            arrow.update_position()


class FlowchartView(QGraphicsView):
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
        self.temp_line = None
        self.connecting_mode = False
        self.connection_start = None
        
        # Pan mode variables
        self.is_panning = False
        self.pan_start_pos = None
        
        # Connect scene signals
        self.scene.node_selected.connect(self.on_node_selected)
        
        # Set background
        self.setBackgroundBrush(QBrush(QColor(240, 240, 245)))
        
        # Create START node
        self.create_start_node()
        
    def create_start_node(self):
        """Create initial START node"""
        start_node = FlowchartNode("START", "Start", "START")
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
            elif element_type == "Arc Point":
                node = self.create_point_node_at(pos.x(), pos.y())
                node.name = f"AP{self.node_counter}"
            elif element_type == "Parabola Point":
                node = self.create_point_node_at(pos.x(), pos.y())
                node.name = f"PP{self.node_counter}"
            elif element_type in ["Variable", "Switch", "Auxiliary Point", 
                                 "Auxiliary Line", "Auxiliary Curve", "Mark Point", "Comment"]:
                # Create generic nodes for these types
                node = self.create_generic_node_at(element_type, pos.x(), pos.y())
            
            if node:
                event.acceptProposedAction()
                # Notify that node was created
                if hasattr(self, 'parentWidget'):
                    parent = self.parentWidget()
                    # Import here to avoid circular dependency
                    from main_window import ComponentDesigner
                    while parent and not isinstance(parent, ComponentDesigner):
                        parent = parent.parentWidget()
                    if parent:
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
    
    def mousePressEvent(self, event):
        """Handle mouse press for panning"""
        if event.button() == Qt.MiddleButton:
            # Start panning - switch to ScrollHandDrag mode
            self.is_panning = True
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.ClosedHandCursor)
            # Create a fake left button event to start the drag
            fake_event = QMouseEvent(
                event.type(),
                event.localPos(),
                Qt.LeftButton,
                Qt.LeftButton,
                event.modifiers()
            )
            super().mousePressEvent(fake_event)
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for panning"""
        if self.is_panning:
            # Pass through as left button for ScrollHandDrag
            fake_event = QMouseEvent(
                event.type(),
                event.localPos(),
                Qt.LeftButton,
                Qt.LeftButton,
                event.modifiers()
            )
            super().mouseMoveEvent(fake_event)
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release to end panning"""
        if event.button() == Qt.MiddleButton and self.is_panning:
            # End panning - restore RubberBandDrag mode
            self.is_panning = False
            # Create fake left button release
            fake_event = QMouseEvent(
                event.type(),
                event.localPos(),
                Qt.LeftButton,
                Qt.LeftButton,
                event.modifiers()
            )
            super().mouseReleaseEvent(fake_event)
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """Handle zoom with mouse wheel (scroll) or pan with Shift+wheel"""
        # Check if Shift is pressed for horizontal pan
        if event.modifiers() & Qt.ShiftModifier:
            # Horizontal pan with Shift+wheel
            delta = event.angleDelta().y()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta
            )
        # Check if Ctrl is pressed for zoom
        elif event.modifiers() & Qt.ControlModifier:
            # Zoom with Ctrl+wheel
            factor = 1.15
            if event.angleDelta().y() > 0:
                self.scale(factor, factor)
            else:
                self.scale(1/factor, 1/factor)
        else:
            # Default: vertical pan with wheel
            delta = event.angleDelta().y()
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta
            )