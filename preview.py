"""
Preview Module for Component Designer.

Key design decisions
--------------------
* Grid removed entirely.
* Axes, surface lines, elevation arrows and offset arrows are drawn in
  drawForeground() in *viewport* coordinates — so they always span the
  full visible area regardless of pan / zoom.
* Labels for target indicators are also drawn in the foreground so they
  stay inside the viewport at all times.
* Node geometry (points, links, text labels) still lives in scene
  coordinates as QGraphicsItems, just as before.
"""

import traceback
from collections import deque

from PySide2.QtWidgets import (
    QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsPolygonItem, QGraphicsItem, QGraphicsTextItem,
)
from PySide2.QtCore  import Qt, QPointF, QRectF, Signal
from PySide2.QtGui   import (
    QPainter, QBrush, QColor, QPen, QFont, QPolygonF, QFontMetrics,
)

from .models import PointNode, LinkNode
from .base_graphics_view import BaseGraphicsView
from .theme_dark import theme


BASE_FONT_NODE_LABEL = 9
BASE_FONT_CODE_LABEL = 7
BASE_FONT_ORIGIN     = 8

_AXIS_PEN_COLOR  = theme.AXIS_COLOR
_AXIS_PEN_WIDTH  = 1.5
_SURFACE_COLOR   = theme.SURFACE_COLOR
_SURFACE_DASH    = [10, 6]
_ELEV_COLOR      = theme.ELEVATION_COLOR
_OFFSET_COLOR    = theme.OFFSET_COLOR
_ARROW_HEAD      = 10
_ARROW_SHAFT     = 28
_LABEL_PAD       = 6
_EDGE_MARGIN     = 6


class PreviewTextItem(QGraphicsTextItem):

    def __init__(self, text, node,
                 anchor_scene=None,
                 offset_screen=None,
                 base_font_size=BASE_FONT_NODE_LABEL,
                 parent=None):
        super().__init__(text, parent)
        self.node           = node
        self.anchor_scene   = anchor_scene  or QPointF(0, 0)
        self.offset_screen  = offset_screen or QPointF(8, -25)
        self.base_font_size = base_font_size

        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setData(0, node)
        self.normal_color   = self.defaultTextColor()
        self.selected_color = theme.POINT_SEL_PEN

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

    def set_selected_style(self, selected: bool):
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
        self.setData(0, node)
        self.normal_pen     = QPen(theme.POINT_NORMAL_PEN, 1)
        self.normal_brush   = QBrush(theme.POINT_NORMAL_FILL)
        self.selected_pen   = QPen(theme.POINT_SEL_PEN, 3)
        self.selected_brush = QBrush(theme.POINT_SEL_FILL)
        self.setPen(self.normal_pen)
        self.setBrush(self.normal_brush)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_clicked.emit(self.node)

    def set_selected_style(self, selected: bool):
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
        self.setData(0, node)
        self.normal_pen   = QPen(theme.LINK_NORMAL_COLOR, 2)
        self.selected_pen = QPen(theme.LINK_SEL_COLOR, 4)
        self.setPen(self.normal_pen)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_clicked.emit(self.node)

    def set_selected_style(self, selected: bool):
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

        pen = QPen(theme.DASHED_LINK_COLOR, 1)
        pen.setStyle(Qt.DashLine)
        pen.setDashPattern([4, 4])
        self.normal_pen   = pen
        self.selected_pen = QPen(theme.DASHED_SEL_COLOR, 2)
        self.selected_pen.setStyle(Qt.DashLine)
        self.selected_pen.setDashPattern([4, 4])
        self.setPen(self.normal_pen)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_clicked.emit(self.node)

    def set_selected_style(self, selected: bool):
        if selected:
            self.setPen(self.selected_pen)
            self.setZValue(5)
        else:
            self.setPen(self.normal_pen)
            self.setZValue(-1)


def _is_preview_node_item(item) -> bool:
    if isinstance(item, (QGraphicsEllipseItem, QGraphicsLineItem,
                         QGraphicsPolygonItem, QGraphicsTextItem)):
        return item.data(0) is not None
    return False


class PreviewScene(QGraphicsScene):
    node_clicked = Signal(object)
    def __init__(self):
        super().__init__()


# ---------------------------------------------------------------------------
# Viewport-space drawing helpers
# ---------------------------------------------------------------------------

def _draw_arrow_left(p, tip_x, tip_y, color, selected=False):
    """Left-pointing arrow (←) with tip at (tip_x, tip_y) in viewport px."""
    s  = _ARROW_HEAD
    sh = _ARROW_SHAFT
    poly = QPolygonF([
        QPointF(tip_x,           tip_y),
        QPointF(tip_x + s,       tip_y - s * 0.6),
        QPointF(tip_x + s,       tip_y - s * 0.25),
        QPointF(tip_x + s + sh,  tip_y - s * 0.25),
        QPointF(tip_x + s + sh,  tip_y + s * 0.25),
        QPointF(tip_x + s,       tip_y + s * 0.25),
        QPointF(tip_x + s,       tip_y + s * 0.6),
    ])
    fill = color.lighter(170) if selected else color
    p.setPen(QPen(color.darker(140), 1.5))
    p.setBrush(QBrush(fill))
    p.drawPolygon(poly)


def _draw_arrow_down(p, tip_x, tip_y, color, selected=False):
    """Downward-pointing arrow (↓) with tip at (tip_x, tip_y) in viewport px."""
    s  = _ARROW_HEAD
    sh = _ARROW_SHAFT
    poly = QPolygonF([
        QPointF(tip_x,             tip_y),
        QPointF(tip_x - s * 0.6,   tip_y - s),
        QPointF(tip_x - s * 0.25,  tip_y - s),
        QPointF(tip_x - s * 0.25,  tip_y - s - sh),
        QPointF(tip_x + s * 0.25,  tip_y - s - sh),
        QPointF(tip_x + s * 0.25,  tip_y - s),
        QPointF(tip_x + s * 0.6,   tip_y - s),
    ])
    fill = color.lighter(170) if selected else color
    p.setPen(QPen(color.darker(140), 1.5))
    p.setBrush(QBrush(fill))
    p.drawPolygon(poly)


def _draw_label(p, text, x, y, color, align_right=False, align_bottom=False):
    """Small dark-background label clamped inside the viewport."""
    fm  = QFontMetrics(p.font())
    tw  = fm.horizontalAdvance(text)
    th  = fm.height()
    pad = 3

    vp  = p.viewport()
    rx  = (x - tw - pad * 2) if align_right  else x
    ry  = (y - th - pad)     if align_bottom else y
    rx  = max(2.0, min(float(rx), vp.width()  - tw - pad * 2 - 2))
    ry  = max(2.0, min(float(ry), vp.height() - th - pad - 2))

    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(18, 20, 26, 210)))
    p.drawRoundedRect(QRectF(rx - pad, ry - pad, tw + pad*2, th + pad*2), 3, 3)
    p.setPen(color)
    p.setBrush(Qt.NoBrush)
    p.drawText(QRectF(rx, ry, tw + 1, th + 1), Qt.AlignLeft | Qt.AlignTop, text)


# ---------------------------------------------------------------------------
# Main view class
# ---------------------------------------------------------------------------

class GeometryPreview(BaseGraphicsView):

    def __init__(self):
        super().__init__()
        self._pscene = PreviewScene()
        self.scene   = self._pscene
        self.setScene(self._pscene)
        self.setRenderHint(QPainter.Antialiasing)

        self.scale_factor   = 20
        self.show_codes     = True
        self.show_comments  = False
        self._current_scale = 1.0

        self.points = []
        self.links  = []

        self._target_overlays = []

        self.setBackgroundBrush(QBrush(theme.PREVIEW_BG))
        self.setStyleSheet(theme.SCROLLBAR_STYLE)

        self.setup_scene()
        self._pscene.node_clicked.connect(self.on_node_clicked)

    def wheelEvent(self, event):
        zoom_factor = 1.15
        if event.modifiers() & Qt.ControlModifier:
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - event.angleDelta().y())
            return
        if event.modifiers() & Qt.ShiftModifier:
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - event.angleDelta().y())
            return

        scene_pos = self.mapToScene(event.pos())
        factor    = zoom_factor if event.angleDelta().y() > 0 else 1.0 / zoom_factor
        self._current_scale *= factor
        self.scale(factor, factor)

        new_vp = self.mapFromScene(scene_pos)
        delta  = new_vp - event.pos()
        self.horizontalScrollBar().setValue(
            self.horizontalScrollBar().value() + delta.x())
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().value() + delta.y())

        self._rescale_text_items()
        event.accept()

    def _rescale_text_items(self):
        scale = self.transform().m11()
        for item in self._pscene.items():
            if isinstance(item, PreviewTextItem):
                item.apply_scale(scale)

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
        for item in self._pscene.items():
            if hasattr(item, 'set_selected_style'):
                item.set_selected_style(getattr(item, 'node', None) == node)
        self.viewport().update()

    def setup_scene(self):
        pass  # No grid, no static axes — all drawn in drawForeground

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def _origin_vp(self):
        p = self.mapFromScene(QPointF(0.0, 0.0))
        return float(p.x()), float(p.y())

    def _sy_to_vpy(self, scene_y: float) -> float:
        return float(self.mapFromScene(QPointF(0.0, scene_y)).y())

    def _sx_to_vpx(self, scene_x: float) -> float:
        return float(self.mapFromScene(QPointF(scene_x, 0.0)).x())

    # ------------------------------------------------------------------
    # Foreground overlay
    # ------------------------------------------------------------------

    def drawForeground(self, painter: QPainter, rect):
        super().drawForeground(painter, rect)
        painter.save()
        painter.resetTransform()
        painter.setRenderHint(QPainter.Antialiasing, True)

        vp_w = self.viewport().width()
        vp_h = self.viewport().height()

        self._draw_axes_fg(painter, vp_w, vp_h)

        for ov in self._target_overlays:
            t, val, name, sel = ov['type'], ov['value'], ov['name'], ov.get('selected', False)
            if t == 'surface':
                self._draw_surface_fg(painter, val, name, sel, vp_w, vp_h)
            elif t == 'elevation':
                self._draw_elevation_fg(painter, val, name, sel, vp_w, vp_h)
            elif t == 'offset':
                self._draw_offset_fg(painter, val, name, sel, vp_w, vp_h)

        painter.restore()

    def _draw_axes_fg(self, p, vp_w, vp_h):
        ox, oy = self._origin_vp()
        pen = QPen(_AXIS_PEN_COLOR, _AXIS_PEN_WIDTH)
        pen.setCosmetic(True)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawLine(0, int(oy), vp_w, int(oy))
        p.drawLine(int(ox), 0, int(ox), vp_h)

    def _draw_surface_fg(self, p, value, name, selected, vp_w, vp_h):
        vy = self._sy_to_vpy(-value * self.scale_factor)
        if vy < -2 or vy > vp_h + 2:
            return
        color = _SURFACE_COLOR.lighter(130) if selected else _SURFACE_COLOR
        pen   = QPen(color, 2.0)
        pen.setStyle(Qt.DashLine)
        pen.setDashPattern(_SURFACE_DASH)
        pen.setCosmetic(True)
        p.setPen(pen)
        p.drawLine(0, int(vy), vp_w, int(vy))

        p.setFont(QFont("", 8, QFont.Bold))
        _draw_label(p, f"Surface: {name}  [{value:+.3f}]",
                    x=_EDGE_MARGIN + 4, y=vy - 4,
                    color=color, align_bottom=True)

    def _draw_elevation_fg(self, p, value, name, selected, vp_w, vp_h):
        vy     = self._sy_to_vpy(-value * self.scale_factor)
        off_sc = vy < 0 or vy > vp_h
        vy_c   = max(float(_EDGE_MARGIN + _ARROW_HEAD + _ARROW_SHAFT + 4),
                     min(vy, float(vp_h - _EDGE_MARGIN - _ARROW_HEAD - _ARROW_SHAFT - 4)))

        color = _ELEV_COLOR.lighter(150) if selected else _ELEV_COLOR
        tip_x = float(vp_w) - _EDGE_MARGIN
        p.setFont(QFont("", 8))
        _draw_arrow_left(p, tip_x, vy_c, color, selected)

        label = f"{'↕ ' if off_sc else ''}Elev: {name}  [{value:+.3f}]"
        _draw_label(p, label,
                    x=tip_x - _ARROW_SHAFT - _ARROW_HEAD - _LABEL_PAD, y=vy_c - 7,
                    color=color, align_right=True)

    def _draw_offset_fg(self, p, value, name, selected, vp_w, vp_h):
        vx     = self._sx_to_vpx(value * self.scale_factor)
        off_sc = vx < 0 or vx > vp_w
        vx_c   = max(float(_EDGE_MARGIN + _ARROW_HEAD + _ARROW_SHAFT + 4),
                     min(vx, float(vp_w - _EDGE_MARGIN - _ARROW_HEAD - _ARROW_SHAFT - 4)))

        color = _OFFSET_COLOR.lighter(150) if selected else _OFFSET_COLOR
        tip_y = float(_EDGE_MARGIN + _ARROW_SHAFT + _ARROW_HEAD)
        p.setFont(QFont("", 8))
        _draw_arrow_down(p, vx_c, tip_y, color, selected)

        label = f"{'↔ ' if off_sc else ''}Offset: {name}  [{value:+.3f}]"
        _draw_label(p, label,
                    x=vx_c - 4, y=tip_y + _LABEL_PAD,
                    color=color)

    # ------------------------------------------------------------------
    # Topology sort
    # ------------------------------------------------------------------

    def topological_sort_nodes(self, flowchart_nodes):
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

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_preview(self, flowchart_nodes):
        from .models.targets import (SurfaceTargetNode,
                                     ElevationTargetNode,
                                     OffsetTargetNode)

        for item in list(self._pscene.items()):
            if _is_preview_node_item(item):
                self._pscene.removeItem(item)

        self.points.clear()
        self.links.clear()
        self._target_overlays.clear()

        selected_node   = getattr(self, 'selected_node', None)
        point_positions = {}
        sorted_nodes    = self.topological_sort_nodes(flowchart_nodes)

        for node in sorted_nodes:
            if isinstance(node, SurfaceTargetNode):
                self._target_overlays.append({
                    'type': 'surface', 'value': node.preview_value,
                    'name': node.name, 'selected': node is selected_node,
                })
                continue
            if isinstance(node, ElevationTargetNode):
                self._target_overlays.append({
                    'type': 'elevation', 'value': node.preview_value,
                    'name': node.name, 'selected': node is selected_node,
                })
                continue
            if isinstance(node, OffsetTargetNode):
                self._target_overlays.append({
                    'type': 'offset', 'value': node.preview_value,
                    'name': node.name, 'selected': node is selected_node,
                })
                continue

            try:
                items = node.create_preview_items(
                    self._pscene, self.scale_factor,
                    self.show_codes, point_positions,
                )
                for item in items:
                    self._pscene.addItem(item)
            except Exception as e:
                print(f"Error creating preview for {node.type} {node.name}: {e}")
                traceback.print_exc()

        self._rescale_text_items()
        self.viewport().update()
