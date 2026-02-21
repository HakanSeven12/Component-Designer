"""
Flowchart Module for Component Designer.

Wire-based data transport
-------------------------
Every wire carries data from one node's output port to another node's input
port.  There are no special-case node-ID references (from_point, start_point,
etc.) anywhere in this file.  The general flow is:

    wire connects  from_node.output_port  →  to_node.input_port
    on every update:
        value = from_node.get_port_value(output_port)
        to_node.set_port_value(input_port, value)

This means ANY output port value (float, tuple, bool, …) can be delivered to
ANY compatible input port purely through wires, with no special handling.
"""

from PySide2.QtWidgets import QGraphicsScene, QGraphicsPathItem, QGraphicsView
from PySide2.QtCore import Qt, Signal, QPointF
from PySide2.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath

from .models import *
from .models.geometry import PointNode, LinkNode
from .models.workflow import DecisionNode
from .base_graphics_view import BaseGraphicsView
from .node import FlowchartNodeItem, DecisionNodeItem
from .theme_dark import theme
from .undo_stack import (
    UndoStack,
    AddNodeCommand,
    DeleteNodeCommand,
    MoveNodeCommand,
    AddConnectionCommand,
    RemoveConnectionCommand,
)


class ConnectionWire(QGraphicsPathItem):

    def __init__(self, start_pos, end_pos, parent=None):
        super().__init__(parent)
        self.start_pos = start_pos
        self.end_pos   = end_pos
        self.from_node = None
        self.to_node   = None
        self.from_port = None
        self.to_port   = None

        pen = QPen(theme.WIRE_COLOR, 2)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)
        self.update_path()
        self.setZValue(-1)

    def update_path(self):
        path = QPainterPath()
        path.moveTo(self.start_pos)
        dx    = abs(self.end_pos.x() - self.start_pos.x())
        ctrl1 = QPointF(self.start_pos.x() + dx * 0.5, self.start_pos.y())
        ctrl2 = QPointF(self.end_pos.x()   - dx * 0.5, self.end_pos.y())
        path.cubicTo(ctrl1, ctrl2, self.end_pos)
        self.setPath(path)

    def set_end_pos(self, pos):
        self.end_pos = pos
        self.update_path()


class FlowchartScene(QGraphicsScene):

    node_selected            = Signal(object)
    preview_update_requested = Signal()

    def __init__(self):
        super().__init__()
        self.nodes       = {}
        self.connections = []   # list of {from, from_port, to, to_port}
        self.port_wires  = []   # list of wire-data dicts
        self.selected_node = None

        self.connection_in_progress = False
        self.connection_start_item  = None
        self.connection_start_port  = None
        self.temp_wire              = None

        self.undo_stack = UndoStack(max_depth=100)

    # ------------------------------------------------------------------
    # Port classification helpers
    # ------------------------------------------------------------------

    def _is_output(self, node_item, port_name):
        return port_name in node_item.node.get_output_ports()

    def _is_input(self, node_item, port_name):
        return port_name in node_item.node.get_input_ports()

    def _is_port_connected(self, node_item, port_name):
        return any(
            w for w in self.port_wires
            if w['to_item'] is node_item and w['to_port'] == port_name
        )

    def can_connect(self, from_item, from_port, to_item, to_port):
        """Any output port can connect to any input port (duck-typed values)."""
        if from_item is to_item:
            return False
        return (self._is_output(from_item, from_port) and
                self._is_input(to_item,   to_port))

    # ------------------------------------------------------------------
    # Port-click entry point
    # ------------------------------------------------------------------

    def handle_port_click(self, node_item, port_name):
        is_out = self._is_output(node_item, port_name)
        is_in  = self._is_input(node_item,  port_name)

        if not self.connection_in_progress:
            # Click on an already-connected input → remove the wire
            if is_in and self._is_port_connected(node_item, port_name):
                wire_data = next(
                    (w for w in self.port_wires
                     if w['to_item'] is node_item and w['to_port'] == port_name),
                    None,
                )
                if wire_data:
                    cmd = RemoveConnectionCommand(
                        self,
                        wire_data['from_item'], wire_data['from_port'],
                        node_item, port_name,
                    )
                    self.undo_stack.push(cmd)
                return
            # Click on an output → start a new wire
            if is_out:
                self._start_connection(node_item, port_name)
        else:
            # Second click on an input → finish the wire
            if is_in and node_item is not self.connection_start_item:
                if self.can_connect(self.connection_start_item,
                                    self.connection_start_port,
                                    node_item, port_name):
                    if self.temp_wire:
                        self.removeItem(self.temp_wire)
                        self.temp_wire = None
                    self.connection_in_progress = False

                    cmd = AddConnectionCommand(
                        self,
                        self.connection_start_item, self.connection_start_port,
                        node_item, port_name,
                    )
                    self.connection_start_item = None
                    self.connection_start_port = None
                    self.undo_stack.push(cmd)
                else:
                    self._cancel_connection()
            else:
                self._cancel_connection()

    # ------------------------------------------------------------------
    # Wire lifecycle — connect
    # ------------------------------------------------------------------

    def _start_connection(self, node_item, port_name):
        self.connection_in_progress = True
        self.connection_start_item  = node_item
        self.connection_start_port  = port_name
        start_pos      = node_item.get_port_scene_pos(port_name)
        self.temp_wire = ConnectionWire(start_pos, start_pos)
        self.addItem(self.temp_wire)

    def _cancel_connection(self):
        if self.temp_wire:
            self.removeItem(self.temp_wire)
            self.temp_wire = None
        self.connection_in_progress = False
        self.connection_start_item  = None
        self.connection_start_port  = None

    def connect_nodes_with_wire(self, from_node, to_node,
                                from_port: str, to_port: str):
        """
        Draw a wire between two nodes and register the connection.

        Called by AddConnectionCommand.redo() and load_file().
        Replaces any existing wire on the destination input port first.
        """
        from_item = to_item = None
        for i in self.items():
            if isinstance(i, FlowchartNodeItem):
                if i.node is from_node:
                    from_item = i
                elif i.node is to_node:
                    to_item = i

        if not (from_item and to_item):
            return
        if from_port not in from_item.ports or to_port not in to_item.ports:
            return

        # Remove any existing wire on to_port (inputs accept only one wire)
        self._disconnect_input_port(to_item, to_port, record_undo=False)

        sp = from_item.get_port_scene_pos(from_port)
        ep = to_item.get_port_scene_pos(to_port)

        wire           = ConnectionWire(sp, ep)
        wire.from_node = from_node
        wire.to_node   = to_node
        wire.from_port = from_port
        wire.to_port   = to_port
        self.addItem(wire)

        self.port_wires.append({
            'wire':      wire,
            'from_item': from_item,
            'to_item':   to_item,
            'from_port': from_port,
            'to_port':   to_port,
        })
        self.connections.append({
            'from':      from_node.id,
            'to':        to_node.id,
            'from_port': from_port,
            'to_port':   to_port,
        })

        if to_port in to_item.ports:
            to_item.ports[to_port].set_connected(True)

        # Immediately push the current value through the new wire
        self._push_wire_value(from_node, from_port, to_node, to_port)
        self.request_preview_update()

    # ------------------------------------------------------------------
    # Wire lifecycle — disconnect
    # ------------------------------------------------------------------

    def _disconnect_input_port(self, node_item, port_name, record_undo=True):
        if record_undo:
            wire_data = next(
                (w for w in self.port_wires
                 if w['to_item'] is node_item and w['to_port'] == port_name),
                None,
            )
            if wire_data:
                cmd = RemoveConnectionCommand(
                    self,
                    wire_data['from_item'], wire_data['from_port'],
                    node_item, port_name,
                )
                self.undo_stack.push(cmd)
                return

        stale = [w for w in self.port_wires
                 if w['to_item'] is node_item and w['to_port'] == port_name]
        for w in stale:
            self.removeItem(w['wire'])
            self.port_wires.remove(w)
            self.connections = [
                c for c in self.connections
                if not (c['to'] == node_item.node.id and
                        c['to_port'] == port_name)
            ]
            if port_name in node_item.ports:
                node_item.ports[port_name].set_connected(False)

        self.request_preview_update()

    # ------------------------------------------------------------------
    # Unified value push  (the core of the wire-based data transport)
    # ------------------------------------------------------------------

    def _push_wire_value(self, from_node, from_port, to_node, to_port):
        """
        Read from_node.get_port_value(from_port) and deliver it to
        to_node.set_port_value(to_port, value).

        This is the ONLY place where data crosses a wire.  No special
        cases for point references, link endpoints, etc.
        """
        value = from_node.get_port_value(from_port)
        if value is not None:
            to_node.set_port_value(to_port, value)

    def resolve_all_wires(self):
        """
        Propagate all wire values in topological order.

        Called before every preview update so that every node has
        up-to-date inputs before its output is read.
        """
        # Build adjacency for topological sort over the connection graph
        ids       = list(self.nodes.keys())
        in_degree = {nid: 0 for nid in ids}
        adj       = {nid: [] for nid in ids}

        for conn in self.connections:
            f, t = conn['from'], conn['to']
            if f in adj and t in in_degree:
                adj[f].append(conn)
                in_degree[t] += 1

        from collections import deque
        queue  = deque(nid for nid in ids if in_degree[nid] == 0)
        order  = []
        while queue:
            nid = queue.popleft()
            order.append(nid)
            for conn in adj[nid]:
                t = conn['to']
                in_degree[t] -= 1
                if in_degree[t] == 0:
                    queue.append(t)

        # Walk in topological order and push each wire's value
        for nid in order:
            for conn in self.connections:
                if conn['from'] != nid:
                    continue
                from_node = self.nodes.get(conn['from'])
                to_node   = self.nodes.get(conn['to'])
                if from_node and to_node:
                    self._push_wire_value(
                        from_node, conn['from_port'],
                        to_node,   conn['to_port'],
                    )

    # ------------------------------------------------------------------
    # Mouse move (temp wire)
    # ------------------------------------------------------------------

    def mouseMoveEvent(self, event):
        if self.connection_in_progress and self.temp_wire:
            self.temp_wire.set_end_pos(event.scenePos())
        super().mouseMoveEvent(event)

    # ------------------------------------------------------------------
    # Add / remove nodes
    # ------------------------------------------------------------------

    def add_flowchart_node(self, node, x, y):
        self.nodes[node.id] = node
        node.x = x
        node.y = y

        if isinstance(node, DecisionNode):
            item = DecisionNodeItem(node, x, y)
        else:
            item = FlowchartNodeItem(node, x, y)

        self.addItem(item)
        return item

    def _remove_node_item(self, item, record_undo=True):
        node = item.node
        if isinstance(node, StartNode):
            return False

        if record_undo:
            cmd = DeleteNodeCommand(self, item)
            self.undo_stack.push(cmd)
            return True

        # Disconnect all wires touching this node
        for w in [d for d in self.port_wires
                  if d['from_item'] is item or d['to_item'] is item]:
            self.removeItem(w['wire'])
            peer  = w['to_item']   if w['from_item'] is item else w['from_item']
            pport = w['to_port']   if w['from_item'] is item else w['from_port']
            if pport in peer.ports:
                peer.ports[pport].set_connected(False)

        self.port_wires  = [w for w in self.port_wires
                            if w['from_item'] is not item and
                               w['to_item']   is not item]
        self.connections = [c for c in self.connections
                            if c['from'] != node.id and c['to'] != node.id]
        if node.id in self.nodes:
            del self.nodes[node.id]
        self.removeItem(item)
        self.request_preview_update()
        return True

    def delete_selected_node(self):
        selected = [i for i in self.selectedItems()
                    if isinstance(i, FlowchartNodeItem)]
        if not selected:
            return False
        return self._remove_node_item(selected[0], record_undo=True)

    def update_port_wires(self, moved_item):
        for w in self.port_wires:
            if w['from_item'] is moved_item:
                w['wire'].start_pos = moved_item.get_port_scene_pos(w['from_port'])
                w['wire'].update_path()
            if w['to_item'] is moved_item:
                w['wire'].end_pos = moved_item.get_port_scene_pos(w['to_port'])
                w['wire'].update_path()

    def request_preview_update(self):
        self.preview_update_requested.emit()


# ---------------------------------------------------------------------------
# Per-type abbreviation map  (unchanged)
# ---------------------------------------------------------------------------

_TYPED_INPUT_TYPES = (
    "Integer Input", "Double Input", "String Input",
    "Grade Input", "Slope Input", "Yes\\No Input",
    "Side Input", "Superelevation Input",
)

_TYPE_PREFIX: dict[str, str] = {
    "Point": "P", "Link": "L", "Shape": "SH",
    "Start": "ST", "Decision": "D", "Variable": "VAR",
    "Input": "IN", "Output": "OUT",
    "Surface Target": "SURF", "Elevation Target": "ELEV", "Offset Target": "OFF",
    "Integer Input": "INT", "Double Input": "DBL", "String Input": "STR",
    "Grade Input": "GRD", "Slope Input": "SLP",
    "Yes\\No Input": "YN", "Superelevation Input": "SE",
    "Add": "ADD", "Subtract": "SUB", "Multiply": "MUL",
    "Divide": "DIV", "Modulo": "MOD", "Power": "POW",
    "Abs": "ABS", "Negate": "NEG", "Sqrt": "SQRT",
    "Ceil": "CEIL", "Floor": "FLR", "Round": "RND",
    "Sin": "SIN", "Cos": "COS", "Tan": "TAN",
    "Asin": "ASIN", "Acos": "ACOS", "Atan": "ATAN", "Atan2": "AT2",
    "Ln": "LN", "Log10": "LOG", "Exp": "EXP",
    "Min": "MIN", "Max": "MAX", "Clamp": "CLM",
    "Interpolate": "LERP", "Map Range": "MAP",
}


def _prefix_for_type(node_type: str) -> str:
    if node_type in _TYPE_PREFIX:
        return _TYPE_PREFIX[node_type]
    return "".join(w[0].upper() for w in node_type.split()) or "X"


# ---------------------------------------------------------------------------
# FlowchartView
# ---------------------------------------------------------------------------

class FlowchartView(BaseGraphicsView):

    def __init__(self):
        super().__init__()
        self.scene = FlowchartScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setAcceptDrops(True)

        self.node_counter = 0
        self._type_counters: dict[str, int] = {}

        self._clipboard_node = None
        self._drag_start_positions: dict = {}

        self.scene.node_selected.connect(self.on_node_selected)
        self.setBackgroundBrush(QBrush(theme.CANVAS_BG))
        self.setStyleSheet(theme.SCROLLBAR_STYLE)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.create_start_node()

    @property
    def undo_stack(self):
        return self.scene.undo_stack

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.scene.connection_in_progress:
            self.scene._cancel_connection()
            event.accept()
            return

        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            if self.scene.delete_selected_node():
                event.accept()
                return

        if event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            if not (event.modifiers() & Qt.ShiftModifier):
                desc = self.scene.undo_stack.undo()
                if desc:
                    self._emit_status(f"Undo: {desc}")
                event.accept()
                return

        if (event.key() == Qt.Key_Y and event.modifiers() & Qt.ControlModifier) or \
           (event.key() == Qt.Key_Z and
            event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier)):
            desc = self.scene.undo_stack.redo()
            if desc:
                self._emit_status(f"Redo: {desc}")
            event.accept()
            return

        if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            selected = [i for i in self.scene.selectedItems()
                        if isinstance(i, FlowchartNodeItem)]
            if selected:
                self._clipboard_node = selected[0].node
            event.accept()
            return

        if event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            if self._clipboard_node is not None:
                self._paste_node()
            event.accept()
            return

        super().keyPressEvent(event)

    def _emit_status(self, msg: str):
        widget = self.parentWidget()
        while widget:
            if hasattr(widget, 'statusBar'):
                widget.statusBar().showMessage(msg, 3000)
                return
            widget = widget.parentWidget()

    # ------------------------------------------------------------------
    # Drag tracking
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            item_under = self.itemAt(event.pos())
            if isinstance(item_under, FlowchartNodeItem) or (
                item_under is not None and
                isinstance(item_under.parentItem(), FlowchartNodeItem)
            ):
                self.setDragMode(QGraphicsView.NoDrag)
                self._drag_start_positions = {
                    item: item.pos()
                    for item in self.scene.selectedItems()
                    if isinstance(item, FlowchartNodeItem)
                }
                if isinstance(item_under, FlowchartNodeItem):
                    self._drag_start_positions.setdefault(item_under, item_under.pos())
                elif isinstance(item_under.parentItem(), FlowchartNodeItem):
                    ni = item_under.parentItem()
                    self._drag_start_positions.setdefault(ni, ni.pos())
            else:
                self.setDragMode(QGraphicsView.RubberBandDrag)
                self._drag_start_positions = {}
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            if self._drag_start_positions:
                for item, old_pos in self._drag_start_positions.items():
                    new_pos = item.pos()
                    if (new_pos - old_pos).manhattanLength() > 1:
                        cmd = MoveNodeCommand(self.scene, item, old_pos, new_pos)
                        self.scene.undo_stack._stack = \
                            self.scene.undo_stack._stack[
                                :self.scene.undo_stack._index + 1]
                        self.scene.undo_stack._stack.append(cmd)
                        self.scene.undo_stack._index = \
                            len(self.scene.undo_stack._stack) - 1
                self._drag_start_positions = {}
            self.setDragMode(QGraphicsView.RubberBandDrag)

    # ------------------------------------------------------------------
    # Paste
    # ------------------------------------------------------------------

    def _paste_node(self):
        src  = self._clipboard_node
        data = src.to_dict()
        data['id']   = self._next_id()
        data['x']    = src.x + 30
        data['y']    = src.y + 30
        data['name'] = self._next_type_name(src.type)

        from .models import create_node_from_dict
        new_node = create_node_from_dict(data)

        cmd = AddNodeCommand(self.scene, new_node, new_node.x, new_node.y)
        self.scene.undo_stack.push(cmd)

        for i in self.scene.selectedItems():
            i.setSelected(False)
        if cmd._item:
            cmd._item.setSelected(True)

        self._clipboard_node = new_node

    # ------------------------------------------------------------------
    # Visual selection sync
    # ------------------------------------------------------------------

    def select_node_visually(self, node):
        self.selected_node = node
        for item in self.scene.items():
            if isinstance(item, FlowchartNodeItem):
                item.setSelected(item.node is node)
                if item.node is node:
                    self.centerOn(item)

    def restore_drag_mode(self):
        self.setDragMode(QGraphicsView.RubberBandDrag)

    def create_start_node(self):
        self.scene.add_flowchart_node(StartNode("START", "START"), 50, 50)

    def on_node_selected(self, node):
        self.scene.selected_node = node

    # ------------------------------------------------------------------
    # Drag-and-drop from toolbox
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not event.mimeData().hasText():
            event.ignore()
            return
        pos = self.mapToScene(event.pos())
        if self.add_node_by_type(event.mimeData().text(), pos.x(), pos.y()):
            event.acceptProposedAction()
            self.scene.request_preview_update()
        else:
            event.ignore()

    # ------------------------------------------------------------------
    # ID / name helpers
    # ------------------------------------------------------------------

    def _next_id(self) -> str:
        self.node_counter += 1
        return f"N{self.node_counter:04d}"

    def _next_type_name(self, node_type: str) -> str:
        self._type_counters[node_type] = self._type_counters.get(node_type, 0) + 1
        return f"{_prefix_for_type(node_type)}{self._type_counters[node_type]}"

    def _auto_pos(self):
        x = 50 + (self.node_counter * 160) % 640
        y = 50 + ((self.node_counter * 160) // 640) * 130
        return x, y

    # ------------------------------------------------------------------
    # Node creators
    # ------------------------------------------------------------------

    def _add_node(self, node, x, y):
        cmd = AddNodeCommand(self.scene, node, x, y)
        self.scene.undo_stack.push(cmd)
        return node

    def add_node_by_type(self, node_type: str, x=None, y=None):
        if x is None or y is None:
            x, y = self._auto_pos()
        node_id   = self._next_id()
        node_name = self._next_type_name(node_type)
        node = create_node_from_type(node_type, node_id, node_name)
        return self._add_node(node, x, y)

    def get_next_node_id(self):
        return self._next_id()
