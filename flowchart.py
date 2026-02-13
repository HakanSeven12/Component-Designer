"""
Flowchart Module for Component Designer
Contains flowchart scene, view, and draggable node items
"""
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem, QApplication
from PySide2.QtCore import Qt, Signal, QPointF
from PySide2.QtGui import QPainter, QBrush, QColor, QPen

from models import PointNode, LinkNode, ShapeNode, DecisionNode, FlowchartNode


class FlowchartNodeItem(QGraphicsRectItem):
    """Draggable flowchart node item"""
    
    def __init__(self, node, x, y, parent=None):
        super().__init__(x, y, 120, 60, parent)
        self.node = node
        self.setFlags(QGraphicsItem.ItemIsMovable | 
                     QGraphicsItem.ItemIsSelectable |
                     QGraphicsItem.ItemSendsGeometryChanges)
        
        # Visual styling
        self.setPen(QPen(QColor(0, 0, 0), 2))
        self.setBrush(QBrush(QColor(200, 220, 255)))
        
        # Add text label
        self.text = QGraphicsTextItem(f"{node.type}\n{node.name}", self)
        self.text.setPos(10, 10)
        
        # Store node reference
        self.setData(0, node)
        
    def mousePressEvent(self, event):
        """Handle mouse press - select node"""
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_selected.emit(self.node)
            
    def itemChange(self, change, value):
        """Handle item changes - update node position"""
        if change == QGraphicsItem.ItemPositionChange:
            # Update node position
            new_pos = value
            self.node.x = new_pos.x()
            self.node.y = new_pos.y()
        return super().itemChange(change, value)
        
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
        self.selected_node = None
        
    def add_flowchart_node(self, node, x, y):
        """Add a node to the flowchart"""
        self.nodes[node.id] = node
        node.x = x
        node.y = y
        
        # Create draggable node item
        node_item = FlowchartNodeItem(node, x, y)
        self.addItem(node_item)
        
        return node_item


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
        
        # Connect scene signals
        self.scene.node_selected.connect(self.on_node_selected)
        
        # Set background
        self.setBackgroundBrush(QBrush(QColor(240, 240, 245)))
        
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
        
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Delete:
            # Delete selected items
            for item in self.scene.selectedItems():
                if isinstance(item, FlowchartNodeItem):
                    node_id = item.node.id
                    if node_id in self.scene.nodes:
                        del self.scene.nodes[node_id]
                    self.scene.removeItem(item)
        else:
            super().keyPressEvent(event)
            
    def wheelEvent(self, event):
        """Handle zoom with mouse wheel"""
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1/factor, 1/factor)
