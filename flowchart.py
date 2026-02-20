"""
Flowchart Module for Component Designer
"""

from PySide2.QtWidgets import QGraphicsScene, QGraphicsPathItem, QGraphicsView
from PySide2.QtCore import Qt, Signal, QPointF
from PySide2.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath
from .models import *
from .models.targets import SurfaceTargetNode, ElevationTargetNode, OffsetTargetNode
from .base_graphics_view import BaseGraphicsView
from .node import FlowchartNodeItem
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
        self.connections = []
        self.port_wires  = []
        self.selected_node = None

        self.connection_in_progress = False
        self.connection_start_item  = None
        self.connection_start_port  = None
        self.temp_wire              = None

        self.undo_stack = UndoStack(max_depth=100)

    # ------------------------------------------------------------------
    # Port helpers
    # ------------------------------------------------------------------

    def _is_output(self, node_item, port_name):
        ports = node_item.node.get_output_ports()
        return port_name in ports and not isinstance(ports[port_name], list)

    def _is_input(self, node_item, port_name):
        ports = node_item.node.get_input_ports()
        return port_name in ports and not isinstance(ports[port_name], list)

    def _is_port_connected(self, node_item, port_name):
        return any(
            w for w in self.port_wires
            if w['to_item'] is node_item and w['to_port'] == port_name
        )

    def can_connect(self, from_item, from_port, to_item, to_port):
        if from_item is to_item:
            return False
        return self._is_output(from_item, from_port) and self._is_input(to_item, to_port)

    # ------------------------------------------------------------------
    # Port-click entry point
    # ------------------------------------------------------------------

    def handle_port_click(self, node_item, port_name):
        is_out = self._is_output(node_item, port_name)
        is_in  = self._is_input(node_item, port_name)

        if not self.connection_in_progress:
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
                else:
                    self._disconnect_input_port(node_item, port_name)
                return
            if is_out:
                self._start_connection(node_item, port_name)
        else:
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
                    saved_start_item = self.connection_start_item
                    saved_start_port = self.connection_start_port
                    self.connection_start_item = None
                    self.connection_start_port = None
                    self.undo_stack.push(cmd)
                else:
                    self._cancel_connection()
            else:
                self._cancel_connection()

    # ------------------------------------------------------------------
    # Disconnect
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
                if not (c['to'] == node_item.node.id and c['to_port'] == port_name)
            ]
            self._clear_node_ref(node_item.node, port_name)
            if port_name in node_item.ports:
                node_item.ports[port_name].set_connected(False)
        self.request_preview_update()

    # ------------------------------------------------------------------
    # Connect
    # ------------------------------------------------------------------

    def _start_connection(self, node_item, port_name):
        self.connection_in_progress = True
        self.connection_start_item  = node_item
        self.connection_start_port  = port_name
        start_pos      = node_item.get_port_scene_pos(port_name)
        self.temp_wire = ConnectionWire(start_pos, start_pos)
        self.addItem(self.temp_wire)

    def _finish_connection(self, node_item, port_name):
        """Direct finish (legacy path, kept for compatibility)."""
        if not self.connection_in_progress:
            return

        stale = [w for w in self.port_wires
                 if w['to_item'] is node_item and w['to_port'] == port_name]
        for w in stale:
            self.removeItem(w['wire'])
            self.port_wires.remove(w)
            self.connections = [c for c in self.connections
                                 if not (c['to'] == node_item.node.id
                                         and c['to_port'] == port_name)]
            self._clear_node_ref(node_item.node, port_name)
            if port_name in node_item.ports:
                node_item.ports[port_name].set_connected(False)

        sp = self.connection_start_item.get_port_scene_pos(self.connection_start_port)
        ep = node_item.get_port_scene_pos(port_name)

        wire           = ConnectionWire(sp, ep)
        wire.from_node = self.connection_start_item.node
        wire.to_node   = node_item.node
        wire.from_port = self.connection_start_port
        wire.to_port   = port_name
        self.addItem(wire)
        self.port_wires.append({
            'wire':      wire,
            'from_item': self.connection_start_item,
            'to_item':   node_item,
            'from_port': self.connection_start_port,
            'to_port':   port_name,
        })

        self._set_node_ref(self.connection_start_item.node,
                           self.connection_start_port,
                           node_item.node, port_name)
        self.connections.append({
            'from':      self.connection_start_item.node.id,
            'to':        node_item.node.id,
            'from_port': self.connection_start_port,
            'to_port':   port_name,
        })

        if port_name in node_item.ports:
            node_item.ports[port_name].set_connected(True)

        if self.temp_wire:
            self.removeItem(self.temp_wire)
            self.temp_wire = None
        self.connection_in_progress = False
        self.connection_start_item  = None
        self.connection_start_port  = None
        self.request_preview_update()

    def _cancel_connection(self):
        if self.temp_wire:
            self.removeItem(self.temp_wire)
            self.temp_wire = None
        self.connection_in_progress = False
        self.connection_start_item  = None
        self.connection_start_port  = None

    # ------------------------------------------------------------------
    # Node-ref helpers
    # ------------------------------------------------------------------

    def _set_node_ref(self, from_node, from_port, to_node, to_port):
        if isinstance(to_node, PointNode) and to_port == 'reference':
            to_node.from_point = from_node.id
        elif isinstance(to_node, LinkNode):
            if to_port == 'start':
                to_node.start_point = from_node.id
            elif to_port == 'end':
                to_node.end_point = from_node.id

    def _clear_node_ref(self, node, port):
        if isinstance(node, PointNode) and port == 'reference':
            node.from_point = None
        elif isinstance(node, LinkNode):
            if port == 'start':
                node.start_point = None
            elif port == 'end':
                node.end_point = None

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

        for w in [d for d in self.port_wires
                  if d['from_item'] is item or d['to_item'] is item]:
            self.removeItem(w['wire'])
            peer  = w['to_item']   if w['from_item'] is item else w['from_item']
            pport = w['to_port']   if w['from_item'] is item else w['from_port']
            if pport in peer.ports:
                peer.ports[pport].set_connected(False)

        self.port_wires  = [w for w in self.port_wires
                            if w['from_item'] is not item and w['to_item'] is not item]
        self.connections = [c for c in self.connections
                            if c['from'] != node.id and c['to'] != node.id]
        if node.id in self.nodes:
            del self.nodes[node.id]
        self.removeItem(item)
        self.request_preview_update()
        return True

    def delete_selected_node(self):
        selected = [i for i in self.selectedItems() if isinstance(i, FlowchartNodeItem)]
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

    def connect_nodes_with_wire(self, from_node, to_node,
                                from_port='vector', to_port='reference'):
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

        stale = [w for w in self.port_wires
                 if w['to_item'] is to_item and w['to_port'] == to_port]
        for w in stale:
            self.removeItem(w['wire'])
            self.port_wires.remove(w)
            self.connections = [c for c in self.connections
                                 if not (c['to'] == to_node.id
                                         and c['to_port'] == to_port)]
            self._clear_node_ref(to_node, to_port)
            if to_port in to_item.ports:
                to_item.ports[to_port].set_connected(False)

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
        self._set_node_ref(from_node, from_port, to_node, to_port)

        if to_port in to_item.ports:
            to_item.ports[to_port].set_connected(True)

        self.connections.append({
            'from':      from_node.id,
            'to':        to_node.id,
            'from_port': from_port,
            'to_port':   to_port,
        })


_TYPED_INPUT_TYPES = (
    "Integer Input",
    "Double Input",
    "String Input",
    "Grade Input",
    "Slope Input",
    "Yes\\No Input",
    "Side Input",
    "Superelevation Input",
)


class FlowchartView(BaseGraphicsView):

    def __init__(self):
        super().__init__()
        self.scene = FlowchartScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setAcceptDrops(True)
        self.node_counter    = 0
        self._clipboard_node = None

        self._drag_start_positions: dict = {}

        self.scene.node_selected.connect(self.on_node_selected)
        self.setBackgroundBrush(QBrush(theme.CANVAS_BG))
        self.setStyleSheet(theme.SCROLLBAR_STYLE)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.create_start_node()

    # ------------------------------------------------------------------
    # Shortcut for external callers
    # ------------------------------------------------------------------

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
                                :self.scene.undo_stack._index + 1
                            ]
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

        data['id'] = self._next_id()
        data['x']  = src.x + 30
        data['y']  = src.y + 30

        for ref in ('from_point', 'start_point', 'end_point'):
            if ref in data:
                data[ref] = None

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
    # ID / position helpers
    # ------------------------------------------------------------------

    def _next_id(self):
        self.node_counter += 1
        return f"N{self.node_counter:04d}"

    def _auto_pos(self):
        x = 50 + (self.node_counter * 160) % 640
        y = 50 + ((self.node_counter * 160) // 640) * 130
        return x, y

    # ------------------------------------------------------------------
    # Node creators
    # ------------------------------------------------------------------

    @staticmethod
    def _name_prefix(node_type: str, counter: int) -> str:
        initials = "".join(w[0].upper() for w in node_type.split())
        return f"{initials}{counter}"

    def _add_node(self, node, x, y):
        cmd = AddNodeCommand(self.scene, node, x, y)
        self.scene.undo_stack.push(cmd)
        return node

    def add_node_by_type(self, node_type: str, x=None, y=None):
        """
        Create any node by its type string and add it to the scene.

        If *x* / *y* are omitted the node is placed at the next
        auto-layout position.  Returns the new node, or None if the
        type string is not recognised.
        """
        if x is None or y is None:
            x, y = self._auto_pos()

        node_id = self._next_id()
        prefix  = self._name_prefix(node_type, self.node_counter)

        # 1. Known registry type → instantiate directly
        node = create_node_from_type(node_type, node_id, prefix)

        # create_node_from_type falls back to GenericNode for unknown types,
        # so every string is handled — nothing extra needed.
        return self._add_node(node, x, y)

    def get_next_node_id(self):
        return self._next_id()