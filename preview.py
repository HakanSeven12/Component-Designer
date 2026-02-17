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

        self.normal_color   = self.defaultTextColor()
        self.selected_color = QColor(255, 120, 0)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_clicked.emit(self.node)

    def set_selected_style(self, selected):
        if selected:
            self.setDefaultTextColor(self.selected_color)
            self.setZValue(10)
        else:
            self.setDefaultTextColor(self.normal_color)
            self.setZValue(0)


class PreviewPointItem(QGraphicsEllipseItem):
    """Selectable point item in preview"""

    def __init__(self, x, y, node, parent=None):
        super().__init__(x - 4, y - 4, 8, 8, parent)
        self.node = node
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setPen(QPen(Qt.black, 1))
        self.setBrush(QBrush(QColor(0, 120, 255)))
        self.setData(0, node)

        self.normal_pen    = QPen(Qt.black, 1)
        self.normal_brush  = QBrush(QColor(0, 120, 255))
        self.selected_pen  = QPen(QColor(255, 120, 0), 3)
        self.selected_brush = QBrush(QColor(255, 200, 100))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_clicked.emit(self.node)

    def set_selected_style(self, selected):
        if selected:
            self.setPen(self.selected_pen)
            self.setBrush(self.selected_brush)
            self.setZValue(10)
        else:
            self.setPen(self.normal_pen)
            self.setBrush(self.normal_brush)
            self.setZValue(0)


class PreviewLineItem(QGraphicsLineItem):
    """Selectable line item in preview (used by LinkNode)"""

    def __init__(self, x1, y1, x2, y2, node, parent=None):
        super().__init__(x1, y1, x2, y2, parent)
        self.node = node
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setPen(QPen(QColor(0, 150, 0), 2))
        self.setData(0, node)

        self.normal_pen   = QPen(QColor(0, 150, 0), 2)
        self.selected_pen = QPen(QColor(255, 120, 0), 4)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_clicked.emit(self.node)

    def set_selected_style(self, selected):
        if selected:
            self.setPen(self.selected_pen)
            self.setZValue(5)
        else:
            self.setPen(self.normal_pen)
            self.setZValue(0)


class PreviewLinkLine(QGraphicsLineItem):
    """
    Thin dashed line drawn from a reference point to this point when
    PointNode.add_link is True.  Visually shows the dependency chain
    without being confused with a real LinkNode geometry line.
    """

    def __init__(self, x1, y1, x2, y2, node, parent=None):
        super().__init__(x1, y1, x2, y2, parent)
        self.node = node
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setData(0, node)
        self.setZValue(-1)   # Draw behind points

        pen = QPen(QColor(160, 160, 200), 1)
        pen.setStyle(Qt.DashLine)
        pen.setDashPattern([4, 4])
        self.normal_pen   = pen
        self.selected_pen = QPen(QColor(255, 160, 60), 2)
        self.selected_pen.setStyle(Qt.DashLine)
        self.selected_pen.setDashPattern([4, 4])
        self.setPen(self.normal_pen)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_clicked.emit(self.node)

    def set_selected_style(self, selected):
        if selected:
            self.setPen(self.selected_pen)
            self.setZValue(5)
        else:
            self.setPen(self.normal_pen)
            self.setZValue(-1)


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

        self.scale_factor  = 20   # pixels per meter
        self.show_codes    = True
        self.show_comments = False
        self.preview_mode  = "Layout"   # Layout or Roadway

        self.points = []
        self.links  = []
        self.shapes = []

        self.setup_scene()

        self.scene.node_clicked.connect(self.on_node_clicked)

    def on_node_clicked(self, node):
        """Propagate node click up to the main window for cross-panel sync."""
        widget = self.parentWidget()
        while widget:
            if hasattr(widget, 'sync_selection_from_preview'):
                widget.sync_selection_from_preview(node)
                break
            widget = widget.parentWidget()

    def restore_drag_mode(self):
        self.setDragMode(QGraphicsView.NoDrag)

    def select_node_visually(self, node):
        """Highlight the preview items that belong to the given node."""
        self.selected_node = node
        for item in self.scene.items():
            if hasattr(item, 'set_selected_style'):
                item.set_selected_style(item.node == node)

    def setup_scene(self):
        """Initialize preview scene with grid and axes."""
        self.scene.setSceneRect(-300, -300, 600, 600)
        self.draw_grid()
        self.draw_axes()

    def draw_grid(self):
        pen = QPen(QColor(220, 220, 220), 0.5)
        pen.setStyle(Qt.DotLine)
        for x in range(-300, 301, 20):
            self.scene.addLine(x, -300, x, 300, pen)
        for y in range(-300, 301, 20):
            self.scene.addLine(-300, y, 300, y, pen)

    def draw_axes(self):
        axis_pen = QPen(QColor(150, 150, 150), 2)
        self.scene.addLine(-300, 0, 300, 0, axis_pen)
        self.scene.addLine(0, -300, 0, 300, axis_pen)
        origin_text = self.scene.addText("0,0")
        origin_text.setPos(5, 5)
        origin_text.setDefaultTextColor(QColor(100, 100, 100))

    def topological_sort_nodes(self, flowchart_nodes):
        """Sort nodes in dependency order (dependencies before dependents)."""
        from collections import deque

        in_degree  = {nid: 0 for nid in flowchart_nodes}
        adjacency  = {nid: [] for nid in flowchart_nodes}

        for node_id, node in flowchart_nodes.items():
            if isinstance(node, PointNode):
                if node.from_point and node.from_point in flowchart_nodes:
                    in_degree[node_id] += 1
                    adjacency[node.from_point].append(node_id)
            elif isinstance(node, LinkNode):
                if node.start_point and node.start_point in flowchart_nodes:
                    in_degree[node_id] += 1
                    adjacency[node.start_point].append(node_id)
                if node.end_point and node.end_point in flowchart_nodes:
                    in_degree[node_id] += 1
                    adjacency[node.end_point].append(node_id)

        queue = deque(nid for nid in flowchart_nodes if in_degree[nid] == 0)
        sorted_nodes = []

        while queue:
            nid = queue.popleft()
            sorted_nodes.append(flowchart_nodes[nid])
            for dep in adjacency[nid]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        if len(sorted_nodes) != len(flowchart_nodes):
            print("Warning: Circular dependency detected in flowchart")
            return list(flowchart_nodes.values())

        return sorted_nodes

    def update_preview(self, flowchart_nodes):
        """Rebuild the preview scene from the current flowchart nodes."""
        # Remove only geometry items (keep grid and axes)
        for item in list(self.scene.items()):
            if isinstance(item, (PreviewPointItem, PreviewLineItem,
                                 PreviewLinkLine, PreviewTextItem,
                                 QGraphicsPolygonItem)):
                if item.data(0) is not None:
                    self.scene.removeItem(item)
            elif hasattr(item, 'toPlainText'):
                if item.data(0) is not None and not isinstance(item, PreviewTextItem):
                    self.scene.removeItem(item)

        self.points.clear()
        self.links.clear()

        point_positions = {}
        sorted_nodes    = self.topological_sort_nodes(flowchart_nodes)

        for node in sorted_nodes:
            try:
                items = node.create_preview_items(
                    self.scene,
                    self.scale_factor,
                    self.show_codes,
                    point_positions,
                )
                for item in items:
                    self.scene.addItem(item)
            except Exception as e:
                print(f"Error creating preview for {node.type} {node.name}: {e}")
                import traceback
                traceback.print_exc()