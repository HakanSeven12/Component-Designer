"""
Preview Module for Component Designer.

Data flow
---------
All node positions are already resolved by FlowchartScene.resolve_all_wires()
before update_preview() is called.  The preview renderer's only job is to
call create_preview_items() on each node in topological order and add the
resulting QGraphicsItems to the scene.

The shared ``point_positions`` dict maps node_id → (x, y) world coords and
is populated incrementally during the render pass.  Nodes read it via the
``_wire_ref_id`` / ``_wire_start_id`` / ``_wire_end_id`` attributes that the
wire resolver stamps on them.
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
from .models.workflow import DecisionNode
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
                 anchor_scene=None, offset_screen=None,
                 base_font_size=BASE_FONT_NODE_LABEL, parent=None):
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
# Viewport helpers
# ---------------------------------------------------------------------------

def _draw_arrow_left(p, tip_x, tip_y, color, selected=False):
    s, sh = _ARROW_HEAD, _ARROW_SHAFT
    poly = QPolygonF([
        QPointF(tip_x,          tip_y),
        QPointF(tip_x+s,        tip_y - s*0.6),
        QPointF(tip_x+s,        tip_y - s*0.25),
        QPointF(tip_x+s+sh,     tip_y - s*0.25),
        QPointF(tip_x+s+sh,     tip_y + s*0.25),
        QPointF(tip_x+s,        tip_y + s*0.25),
        QPointF(tip_x+s,        tip_y + s*0.6),
    ])
    fill = color.lighter(170) if selected else color
    p.setPen(QPen(color.darker(140), 1.5))
    p.setBrush(QBrush(fill))
    p.drawPolygon(poly)


def _draw_arrow_down(p, tip_x, tip_y, color, selected=False):
    s, sh = _ARROW_HEAD, _ARROW_SHAFT
    poly = QPolygonF([
        QPointF(tip_x,           tip_y),
        QPointF(tip_x-s*0.6,     tip_y-s),
        QPointF(tip_x-s*0.25,    tip_y-s),
        QPointF(tip_x-s*0.25,    tip_y-s-sh),
        QPointF(tip_x+s*0.25,    tip_y-s-sh),
        QPointF(tip_x+s*0.25,    tip_y-s),
        QPointF(tip_x+s*0.6,     tip_y-s),
    ])
    fill = color.lighter(170) if selected else color
    p.setPen(QPen(color.darker(140), 1.5))
    p.setBrush(QBrush(fill))
    p.drawPolygon(poly)


def _draw_label(p, text, x, y, color, align_right=False, align_bottom=False):
    fm  = QFontMetrics(p.font())
    tw  = fm.horizontalAdvance(text)
    th  = fm.height()
    pad = 3
    vp  = p.viewport()
    rx  = (x - tw - pad*2) if align_right  else x
    ry  = (y - th - pad)   if align_bottom else y
    rx  = max(2.0, min(float(rx), vp.width()  - tw - pad*2 - 2))
    ry  = max(2.0, min(float(ry), vp.height() - th - pad  - 2))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(18, 20, 26, 210)))
    p.drawRoundedRect(QRectF(rx-pad, ry-pad, tw+pad*2, th+pad*2), 3, 3)
    p.setPen(color)
    p.setBrush(Qt.NoBrush)
    p.drawText(QRectF(rx, ry, tw+1, th+1), Qt.AlignLeft | Qt.AlignTop, text)


# ---------------------------------------------------------------------------
# Decision branch exclusion
# ---------------------------------------------------------------------------

def _build_excluded_set(flowchart_nodes: dict, connections: list) -> set:
    """
    Return the set of node IDs belonging to inactive Decision branches.
    BFS from every inactive-branch output port, transitively.
    """
    adj: dict[str, list[tuple[str, str]]] = {nid: [] for nid in flowchart_nodes}
    for conn in connections:
        fid = conn.get('from')
        tid = conn.get('to')
        fp  = conn.get('from_port', '')
        if fid in adj:
            adj[fid].append((tid, fp))

    excluded: set = set()
    for node in flowchart_nodes.values():
        if not isinstance(node, DecisionNode):
            continue
        active_port   = 'yes' if node.condition_is_true else 'no'
        inactive_port = 'no'  if active_port == 'yes'   else 'yes'

        queue = deque()
        for to_id, fp in adj.get(node.id, []):
            if fp == inactive_port and to_id not in excluded:
                excluded.add(to_id)
                queue.append(to_id)
        while queue:
            cur = queue.popleft()
            for to_id, _ in adj.get(cur, []):
                if to_id not in excluded:
                    excluded.add(to_id)
                    queue.append(to_id)

    return excluded


# ---------------------------------------------------------------------------
# Main view
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
        factor    = zoom_factor if event.angleDelta().y() > 0 else 1.0/zoom_factor
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
        pass

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def _origin_vp(self):
        p = self.mapFromScene(QPointF(0.0, 0.0))
        return float(p.x()), float(p.y())

    def _sy_to_vpy(self, scene_y):
        return float(self.mapFromScene(QPointF(0.0, scene_y)).y())

    def _sx_to_vpx(self, scene_x):
        return float(self.mapFromScene(QPointF(scene_x, 0.0)).x())

    # ------------------------------------------------------------------
    # Foreground overlay
    # ------------------------------------------------------------------

    def drawForeground(self, painter, rect):
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
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawLine(0, int(oy), vp_w, int(oy))
        p.drawLine(int(ox), 0, int(ox), vp_h)

    def _draw_surface_fg(self, p, value, name, selected, vp_w, vp_h):
        vy = self._sy_to_vpy(-value * self.scale_factor)
        if vy < -2 or vy > vp_h + 2:
            return
        color = _SURFACE_COLOR.lighter(130) if selected else _SURFACE_COLOR
        pen   = QPen(color, 2.0); pen.setStyle(Qt.DashLine)
        pen.setDashPattern(_SURFACE_DASH); pen.setCosmetic(True)
        p.setPen(pen)
        p.drawLine(0, int(vy), vp_w, int(vy))
        p.setFont(QFont("", 8, QFont.Bold))
        _draw_label(p, f"Surface: {name}  [{value:+.3f}]",
                    x=_EDGE_MARGIN+4, y=vy-4, color=color, align_bottom=True)

    def _draw_elevation_fg(self, p, value, name, selected, vp_w, vp_h):
        vy    = self._sy_to_vpy(-value * self.scale_factor)
        off_sc = vy < 0 or vy > vp_h
        vy_c  = max(float(_EDGE_MARGIN+_ARROW_HEAD+_ARROW_SHAFT+4),
                    min(vy, float(vp_h-_EDGE_MARGIN-_ARROW_HEAD-_ARROW_SHAFT-4)))
        color = _ELEV_COLOR.lighter(150) if selected else _ELEV_COLOR
        tip_x = float(vp_w) - _EDGE_MARGIN
        p.setFont(QFont("", 8))
        _draw_arrow_left(p, tip_x, vy_c, color, selected)
        _draw_label(p, f"{'↕ ' if off_sc else ''}Elev: {name}  [{value:+.3f}]",
                    x=tip_x-_ARROW_SHAFT-_ARROW_HEAD-_LABEL_PAD, y=vy_c-7,
                    color=color, align_right=True)

    def _draw_offset_fg(self, p, value, name, selected, vp_w, vp_h):
        vx    = self._sx_to_vpx(value * self.scale_factor)
        off_sc = vx < 0 or vx > vp_w
        vx_c  = max(float(_EDGE_MARGIN+_ARROW_HEAD+_ARROW_SHAFT+4),
                    min(vx, float(vp_w-_EDGE_MARGIN-_ARROW_HEAD-_ARROW_SHAFT-4)))
        color = _OFFSET_COLOR.lighter(150) if selected else _OFFSET_COLOR
        tip_y = float(_EDGE_MARGIN+_ARROW_SHAFT+_ARROW_HEAD)
        p.setFont(QFont("", 8))
        _draw_arrow_down(p, vx_c, tip_y, color, selected)
        _draw_label(p, f"{'↔ ' if off_sc else ''}Offset: {name}  [{value:+.3f}]",
                    x=vx_c-4, y=tip_y+_LABEL_PAD, color=color)

    # ------------------------------------------------------------------
    # Topological sort  (render order only — data already resolved)
    # ------------------------------------------------------------------

    def _topological_sort(self, flowchart_nodes, connections):
        """
        Sort nodes so that every node's inputs are rendered before its outputs.
        Uses the wire connection list for ordering.
        """
        in_degree = {nid: 0 for nid in flowchart_nodes}
        adj       = {nid: [] for nid in flowchart_nodes}

        for conn in connections:
            f, t = conn.get('from'), conn.get('to')
            if f in adj and t in in_degree:
                adj[f].append(t)
                in_degree[t] += 1

        queue = deque(nid for nid in flowchart_nodes if in_degree[nid] == 0)
        order = []
        while queue:
            nid = queue.popleft()
            order.append(flowchart_nodes[nid])
            for dep in adj[nid]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        if len(order) != len(flowchart_nodes):
            print("Warning: Circular dependency in flowchart")
            return list(flowchart_nodes.values())
        return order

    # ------------------------------------------------------------------
    # Stamp wire IDs onto nodes so create_preview_items can look them up
    # ------------------------------------------------------------------

    def _stamp_wire_ids(self, connections: list):
        """
        For each connection, store the upstream node ID on the downstream
        node so that create_preview_items() can locate the correct upstream
        position in point_positions without needing legacy ID fields.
        """
        for conn in connections:
            from_id   = conn.get('from')
            to_id     = conn.get('to')
            from_port = conn.get('from_port', '')
            to_port   = conn.get('to_port',   '')

            # PointNode receiving a position on its 'reference' port
            if to_port == 'reference':
                node = self._nodes_ref.get(to_id)
                if node:
                    node._wire_ref_id = from_id

            # LinkNode receiving positions on 'start' / 'end' ports
            if to_port == 'start':
                node = self._nodes_ref.get(to_id)
                if node:
                    node._wire_start_id = from_id
            if to_port == 'end':
                node = self._nodes_ref.get(to_id)
                if node:
                    node._wire_end_id = from_id

    # ------------------------------------------------------------------
    # Main update entry point
    # ------------------------------------------------------------------

    def update_preview(self, flowchart_nodes: dict, connections: list = None):
        """
        Rebuild all preview items.

        Parameters
        ----------
        flowchart_nodes : dict[str, FlowchartNode]
            All nodes in the scene.
        connections : list[dict]
            All wire connections (from scene.connections).
        """
        from .models.targets import (SurfaceTargetNode,
                                     ElevationTargetNode,
                                     OffsetTargetNode)

        conn_list = connections or []

        # Store reference for _stamp_wire_ids
        self._nodes_ref = flowchart_nodes

        # Remove old preview items
        for item in list(self._pscene.items()):
            if _is_preview_node_item(item):
                self._pscene.removeItem(item)

        self.points.clear()
        self.links.clear()
        self._target_overlays.clear()

        # Stamp wire source IDs onto nodes so create_preview_items can use them
        self._stamp_wire_ids(conn_list)

        # Determine inactive Decision branches
        excluded = _build_excluded_set(flowchart_nodes, conn_list)

        selected_node   = getattr(self, 'selected_node', None)
        point_positions = {}   # node_id → (x, y) world coords, filled as we go

        sorted_nodes = self._topological_sort(flowchart_nodes, conn_list)

        for node in sorted_nodes:
            if node.id in excluded:
                continue

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

            if isinstance(node, DecisionNode):
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
