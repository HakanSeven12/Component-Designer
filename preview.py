"""
Preview Module for Component Designer
"""
from PySide2.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
                               QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsItem,
                               QGraphicsTextItem)
from PySide2.QtCore import Qt, QPointF
from PySide2.QtGui import QPainter, QBrush, QColor, QPen, QFont

from .models import PointNode, LinkNode
from .base_graphics_view import BaseGraphicsView


BASE_FONT_NODE_LABEL = 9
BASE_FONT_CODE_LABEL = 7
BASE_FONT_ORIGIN     = 8


class PreviewTextItem(QGraphicsTextItem):

    def __init__(self, text, node,
                 anchor_scene=None,
                 offset_screen=None,
                 base_font_size=BASE_FONT_NODE_LABEL,
                 parent=None):
        super().__init__(text, parent)
        self.node            = node
        self.anchor_scene    = anchor_scene   or QPointF(0, 0)
        self.offset_screen   = offset_screen  or QPointF(8, -25)
        self.base_font_size  = base_font_size

        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setData(0, node)

        self.normal_color   = self.defaultTextColor()
        self.selected_color = QColor(255, 120, 0)

        f = QFont()
        f.setPointSizeF(base_font_size)
        self.setFont(f)

        self.setPos(self.anchor_scene + self.offset_screen)

    def apply_scale(self, view_scale: float):
        f = self.font()
        f.setPointSizeF(max(1.0, self.base_font_size / view_scale))
        self.setFont(f)

        scene_offset = QPointF(
            self.offset_screen.x() / view_scale,
            self.offset_screen.y() / view_scale,
        )
        self.setPos(self.anchor_scene + scene_offset)

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

    def __init__(self, x, y, node, parent=None):
        super().__init__(x - 4, y - 4, 8, 8, parent)
        self.node = node
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setPen(QPen(Qt.black, 1))
        self.setBrush(QBrush(QColor(0, 120, 255)))
        self.setData(0, node)

        self.normal_pen     = QPen(Qt.black, 1)
        self.normal_brush   = QBrush(QColor(0, 120, 255))
        self.selected_pen   = QPen(QColor(255, 120, 0), 3)
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

    def __init__(self, x1, y1, x2, y2, node, parent=None):
        super().__init__(x1, y1, x2, y2, parent)
        self.node = node
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setData(0, node)
        self.setZValue(-1)

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

    from PySide2.QtCore import Signal
    node_clicked = Signal(object)

    def __init__(self):
        super().__init__()


class GeometryPreview(BaseGraphicsView):

    def __init__(self):
        super().__init__()
        self.scene = PreviewScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)

        self.scale_factor   = 20
        self.show_codes     = True
        self.show_comments  = False
        self._current_scale = 1.0

        self.points = []
        self.links  = []

        self.setup_scene()
        self.scene.node_clicked.connect(self.on_node_clicked)

    def wheelEvent(self, event):
        zoom_factor = 1.15

        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta)
            return

        if event.modifiers() & Qt.ShiftModifier:
            delta = event.angleDelta().y()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta)
            return

        scene_pos = self.mapToScene(event.pos())
        factor    = zoom_factor if event.angleDelta().y() > 0 else 1.0 / zoom_factor

        self._current_scale *= factor
        self.scale(factor, factor)

        new_view_pos = self.mapFromScene(scene_pos)
        delta = new_view_pos - event.pos()
        self.horizontalScrollBar().setValue(
            self.horizontalScrollBar().value() + delta.x())
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().value() + delta.y())

        self._rescale_text_items()
        event.accept()

    def _rescale_text_items(self):
        for item in self.scene.items():
            if isinstance(item, PreviewTextItem):
                item.apply_scale(self._current_scale)

    def on_node_clicked(self, node):
        widget = self.parentWidget()
        while widget:
            if hasattr(widget, 'sync_selection_from_preview'):
                widget.sync_selection_from_preview(node)
                break
            widget = widget.parentWidget()

    def restore_drag_mode(self):
        self.setDragMode(QGraphicsView.NoDrag)

    def select_node_visually(self, node):
        self.selected_node = node
        for item in self.scene.items():
            if hasattr(item, 'set_selected_style'):
                item.set_selected_style(item.node == node)

    def setup_scene(self):
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
        f = QFont()
        f.setPointSize(BASE_FONT_ORIGIN)
        origin_text.setFont(f)

    def topological_sort_nodes(self, flowchart_nodes):
        from collections import deque

        in_degree = {nid: 0 for nid in flowchart_nodes}
        adjacency = {nid: [] for nid in flowchart_nodes}

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

        self._rescale_text_items()