"""
Preview Module for Component Designer
Handles geometry preview with Layout and Roadway modes
"""
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsItem, QGraphicsTextItem
from PySide2.QtCore import Qt, QPointF
from PySide2.QtGui import QPainter, QBrush, QColor, QPen, QPolygonF, QFont

from models import PointNode, LinkNode, ShapeNode
from base_graphics_view import BaseGraphicsView


class PreviewTextItem(QGraphicsTextItem):
    """Selectable text item in preview"""
    
    def __init__(self, text, node, parent=None):
        super().__init__(text, parent)
        self.node = node
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setData(0, node)
        
        # Store original color
        self.normal_color = self.defaultTextColor()
        self.selected_color = QColor(255, 120, 0)
        
    def mousePressEvent(self, event):
        """Handle mouse press - select node"""
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_clicked.emit(self.node)
            
    def set_selected_style(self, selected):
        """Update visual style based on selection"""
        if selected:
            self.setDefaultTextColor(self.selected_color)
            self.setZValue(10)  # Bring to front
        else:
            self.setDefaultTextColor(self.normal_color)
            self.setZValue(0)


class PreviewPointItem(QGraphicsEllipseItem):
    """Selectable point item in preview"""
    
    def __init__(self, x, y, node, parent=None):
        super().__init__(x-4, y-4, 8, 8, parent)
        self.node = node
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setPen(QPen(Qt.black, 1))
        self.setBrush(QBrush(QColor(0, 120, 255)))
        self.setData(0, node)
        
        # Normal and selected styles
        self.normal_pen = QPen(Qt.black, 1)
        self.normal_brush = QBrush(QColor(0, 120, 255))
        self.selected_pen = QPen(QColor(255, 120, 0), 3)
        self.selected_brush = QBrush(QColor(255, 200, 100))
        
    def mousePressEvent(self, event):
        """Handle mouse press - select node"""
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_clicked.emit(self.node)
            
    def set_selected_style(self, selected):
        """Update visual style based on selection"""
        if selected:
            self.setPen(self.selected_pen)
            self.setBrush(self.selected_brush)
            self.setZValue(10)  # Bring to front
        else:
            self.setPen(self.normal_pen)
            self.setBrush(self.normal_brush)
            self.setZValue(0)


class PreviewLineItem(QGraphicsLineItem):
    """Selectable line item in preview"""
    
    def __init__(self, x1, y1, x2, y2, node, parent=None):
        super().__init__(x1, y1, x2, y2, parent)
        self.node = node
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setPen(QPen(QColor(0, 150, 0), 2))
        self.setData(0, node)
        
        # Normal and selected styles
        self.normal_pen = QPen(QColor(0, 150, 0), 2)
        self.selected_pen = QPen(QColor(255, 120, 0), 4)
        
    def mousePressEvent(self, event):
        """Handle mouse press - select node"""
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_clicked.emit(self.node)
            
    def set_selected_style(self, selected):
        """Update visual style based on selection"""
        if selected:
            self.setPen(self.selected_pen)
            self.setZValue(5)
        else:
            self.setPen(self.normal_pen)
            self.setZValue(0)


class PreviewScene(QGraphicsScene):
    """Custom scene for preview with selection support"""
    
    from PySide2.QtCore import Signal
    node_clicked = Signal(object)
    
    def __init__(self):
        super().__init__()


class GeometryPreview(BaseGraphicsView):
    """Preview panel showing the component geometry"""
    
    def __init__(self):
        super().__init__()
        self.scene = PreviewScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        
        self.scale_factor = 20  # pixels per meter
        self.show_codes = True
        self.show_comments = False
        self.preview_mode = "Layout"  # Layout or Roadway
        
        self.points = []
        self.links = []
        self.shapes = []
        
        self.setup_scene()
        
        # Connect scene signals
        self.scene.node_clicked.connect(self.on_node_clicked)
        
    def on_node_clicked(self, node):
        """Handle node click in preview"""
        # Propagate selection to main window
        widget = self.parentWidget()
        while widget:
            if hasattr(widget, 'sync_selection_from_preview'):
                widget.sync_selection_from_preview(node)
                break
            widget = widget.parentWidget()
        
    def restore_drag_mode(self):
        """Restore drag mode after panning"""
        self.setDragMode(QGraphicsView.NoDrag)
        
    def select_node_visually(self, node):
        """Select a node visually in the preview"""
        self.selected_node = node
        
        # Update visual style of all items
        for item in self.scene.items():
            if hasattr(item, 'set_selected_style'):
                item.set_selected_style(item.node == node)
        
    def setup_scene(self):
        """Initialize preview scene"""
        self.scene.setSceneRect(-300, -300, 600, 600)
        self.draw_grid()
        self.draw_axes()
        
    def draw_grid(self):
        """Draw background grid"""
        pen = QPen(QColor(220, 220, 220), 0.5)
        pen.setStyle(Qt.DotLine)
        
        for x in range(-300, 301, 20):
            self.scene.addLine(x, -300, x, 300, pen)
        for y in range(-300, 301, 20):
            self.scene.addLine(-300, y, 300, y, pen)
            
    def draw_axes(self):
        """Draw coordinate axes"""
        axis_pen = QPen(QColor(150, 150, 150), 2)
        self.scene.addLine(-300, 0, 300, 0, axis_pen)
        self.scene.addLine(0, -300, 0, 300, axis_pen)
        
        # Add labels
        origin_text = self.scene.addText("0,0")
        origin_text.setPos(5, 5)
        origin_text.setDefaultTextColor(QColor(100, 100, 100))
    
    def topological_sort_nodes(self, flowchart_nodes):
        """Sort nodes in dependency order using topological sort
        
        Returns nodes in order where dependencies come before dependents.
        For example, if Point B depends on Point A, A will come before B.
        """
        from collections import deque
        
        # Build dependency graph
        # in_degree[node_id] = number of nodes this node depends on
        # adjacency[node_id] = list of nodes that depend on this node
        in_degree = {}
        adjacency = {}
        
        # Initialize
        for node_id, node in flowchart_nodes.items():
            in_degree[node_id] = 0
            adjacency[node_id] = []
        
        # Build graph based on node type dependencies
        for node_id, node in flowchart_nodes.items():
            if isinstance(node, PointNode):
                # Point depends on its from_point
                if node.from_point and node.from_point in flowchart_nodes:
                    in_degree[node_id] += 1
                    adjacency[node.from_point].append(node_id)
                    
            elif isinstance(node, LinkNode):
                # Link depends on its start_point and end_point
                if node.start_point and node.start_point in flowchart_nodes:
                    in_degree[node_id] += 1
                    adjacency[node.start_point].append(node_id)
                if node.end_point and node.end_point in flowchart_nodes:
                    in_degree[node_id] += 1
                    adjacency[node.end_point].append(node_id)
        
        # Kahn's algorithm for topological sort
        queue = deque()
        
        # Start with nodes that have no dependencies
        for node_id in flowchart_nodes:
            if in_degree[node_id] == 0:
                queue.append(node_id)
        
        sorted_nodes = []
        
        while queue:
            node_id = queue.popleft()
            sorted_nodes.append(flowchart_nodes[node_id])
            
            # Reduce in-degree for dependent nodes
            for dependent_id in adjacency[node_id]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)
        
        # Check for cycles (if sorted_nodes doesn't contain all nodes)
        if len(sorted_nodes) != len(flowchart_nodes):
            # Cycle detected - return original order and log warning
            print("Warning: Circular dependency detected in flowchart")
            return list(flowchart_nodes.values())
        
        return sorted_nodes
        
    def update_preview(self, flowchart_nodes):
        """Update preview based on flowchart - GENERIC VERSION with topological sorting
        
        This method sorts nodes in dependency order before processing them.
        """
        # Clear existing geometry (keep grid and axes)
        for item in list(self.scene.items()):
            if isinstance(item, (PreviewPointItem, PreviewLineItem, PreviewTextItem, QGraphicsPolygonItem)):
                if item.data(0) is not None:  # Has node data
                    self.scene.removeItem(item)
            elif hasattr(item, 'toPlainText'):  # Text items with node data
                if item.data(0) is not None and not isinstance(item, PreviewTextItem):
                    self.scene.removeItem(item)
        
        self.points.clear()
        self.links.clear()
        
        # Process flowchart nodes in TOPOLOGICAL ORDER
        point_positions = {}
        
        # Sort nodes by dependencies
        sorted_nodes = self.topological_sort_nodes(flowchart_nodes)
        
        for node in sorted_nodes:
            try:
                # Ask node to create its own preview items
                items = node.create_preview_items(
                    self.scene,
                    self.scale_factor,
                    self.show_codes,
                    point_positions
                )
                
                # Add all items to scene
                for item in items:
                    self.scene.addItem(item)
                    
            except Exception as e:
                # Log error but continue with other nodes
                print(f"Error creating preview for {node.type} {node.name}: {e}")
                import traceback
                traceback.print_exc()