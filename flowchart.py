"""
Flowchart Module for Component Designer

Connection rules (all ports are equal — no distinction between 'flow' and 'value'):
  - Output port  ->  Input port  on a different node = valid
  - Input  port  ->  Output port = invalid (must start from output)
  - Same node connections are blocked

Disconnect rule:
  - Clicking a connected input port (when NO connection is in progress)
    removes the existing wire immediately.
"""

from PySide2.QtWidgets import QGraphicsScene, QGraphicsPathItem, QGraphicsView
from PySide2.QtCore import Qt, Signal, QPointF
from PySide2.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath
from models import PointNode, LinkNode, ShapeNode, DecisionNode, FlowchartNode
from base_graphics_view import BaseGraphicsView
from node import FlowchartNodeItem


class ConnectionWire(QGraphicsPathItem):
    """Bezier curve connecting two ports."""

    def __init__(self, start_pos, end_pos, parent=None):
        super().__init__(parent)
        self.start_pos = start_pos
        self.end_pos   = end_pos
        self.from_node = None
        self.to_node   = None
        self.from_port = None
        self.to_port   = None

        pen = QPen(QColor(100, 100, 100), 2)
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
    """Custom scene for flowchart editing."""

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

    # ------------------------------------------------------------------
    # Port direction helpers
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
    # Port click dispatch
    # ------------------------------------------------------------------

    def handle_port_click(self, node_item, port_name):
        is_out = self._is_output(node_item, port_name)
        is_in  = self._is_input(node_item, port_name)

        if not self.connection_in_progress:
            if is_in and self._is_port_connected(node_item, port_name):
                self._disconnect_input_port(node_item, port_name)
                return
            if is_out:
                self._start_connection(node_item, port_name)
        else:
            if is_in and node_item is not self.connection_start_item:
                if self.can_connect(self.connection_start_item,
                                    self.connection_start_port,
                                    node_item, port_name):
                    self._finish_connection(node_item, port_name)
                else:
                    self._cancel_connection()
            else:
                self._cancel_connection()

    # ------------------------------------------------------------------
    # Disconnect
    # ------------------------------------------------------------------

    def _disconnect_input_port(self, node_item, port_name):
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
    # Connection lifecycle
    # ------------------------------------------------------------------

    def _start_connection(self, node_item, port_name):
        self.connection_in_progress = True
        self.connection_start_item  = node_item
        self.connection_start_port  = port_name
        start_pos      = node_item.get_port_scene_pos(port_name)
        self.temp_wire = ConnectionWire(start_pos, start_pos)
        self.addItem(self.temp_wire)

    def _finish_connection(self, node_item, port_name):
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
    # Node model reference helpers
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
    # Scene events
    # ------------------------------------------------------------------

    def mouseMoveEvent(self, event):
        if self.connection_in_progress and self.temp_wire:
            self.temp_wire.set_end_pos(event.scenePos())
        super().mouseMoveEvent(event)

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def add_flowchart_node(self, node, x, y):
        self.nodes[node.id] = node
        node.x = x
        node.y = y
        item = FlowchartNodeItem(node, x, y)
        self.addItem(item)
        return item

    def delete_selected_node(self):
        from models import StartNode
        selected = [i for i in self.selectedItems() if isinstance(i, FlowchartNodeItem)]
        if not selected:
            return False

        item = selected[0]
        node = item.node
        if isinstance(node, StartNode):
            return False

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
        """Restore a saved wire connection (used when loading from file)."""
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


# ---------------------------------------------------------------------------
# FlowchartView
# ---------------------------------------------------------------------------

# Typed input node type strings — kept in sync with NODE_REGISTRY keys
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
    """Flowchart editor view."""

    def __init__(self):
        super().__init__()
        self.scene = FlowchartScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setAcceptDrops(True)
        self.node_counter = 0

        self.scene.node_selected.connect(self.on_node_selected)
        self.setBackgroundBrush(QBrush(QColor(240, 240, 245)))
        self.create_start_node()

    def restore_drag_mode(self):
        self.setDragMode(QGraphicsView.RubberBandDrag)

    def select_node_visually(self, node):
        self.selected_node = node
        for item in self.scene.items():
            if isinstance(item, FlowchartNodeItem):
                item.setSelected(item.node is node)
                if item.node is node:
                    self.centerOn(item)

    def create_start_node(self):
        from models import StartNode
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

        etype = event.mimeData().text()
        pos   = self.mapToScene(event.pos())

        # Named creators for well-known node types
        creators = {
            "Point":    self.create_point_node_at,
            "Link":     self.create_link_node_at,
            "Shape":    self.create_shape_node_at,
            "Decision": self.create_decision_node_at,
            "Input":    self.create_input_parameter_node_at,
            "Output":   self.create_output_parameter_node_at,
            "Target":   self.create_target_parameter_node_at,
        }
        fn = creators.get(etype)
        if fn:
            fn(pos.x(), pos.y())
            event.acceptProposedAction()
        elif etype in _TYPED_INPUT_TYPES:
            # Typed input nodes: instantiate via NODE_REGISTRY
            self.create_typed_input_node_at(etype, pos.x(), pos.y())
            event.acceptProposedAction()
        elif etype in ("Variable", "Switch", "Auxiliary Point",
                       "Auxiliary Line", "Auxiliary Curve",
                       "Mark Point", "Comment"):
            self.create_generic_node_at(etype, pos.x(), pos.y())
            event.acceptProposedAction()
        else:
            event.ignore()

    # ------------------------------------------------------------------
    # Node factories
    # ------------------------------------------------------------------

    def _next_id(self):
        self.node_counter += 1
        return f"N{self.node_counter:04d}"

    def _auto_pos(self):
        x = 50 + (self.node_counter * 160) % 640
        y = 50 + ((self.node_counter * 160) // 640) * 130
        return x, y

    def create_point_node_at(self, x, y):
        from models import PointNode
        n = PointNode(self._next_id(), f"P{self.node_counter}")
        self.scene.add_flowchart_node(n, x, y)
        return n

    def create_link_node_at(self, x, y):
        from models import LinkNode
        n = LinkNode(self._next_id(), f"L{self.node_counter}")
        self.scene.add_flowchart_node(n, x, y)
        return n

    def create_shape_node_at(self, x, y):
        from models import ShapeNode
        n = ShapeNode(self._next_id(), f"S{self.node_counter}")
        self.scene.add_flowchart_node(n, x, y)
        return n

    def create_decision_node_at(self, x, y):
        from models import DecisionNode
        n = DecisionNode(self._next_id(), f"D{self.node_counter}")
        self.scene.add_flowchart_node(n, x, y)
        return n

    def create_input_parameter_node_at(self, x, y):
        from models import InputParameterNode
        n = InputParameterNode(self._next_id(), f"IP{self.node_counter}")
        self.scene.add_flowchart_node(n, x, y)
        return n

    def create_output_parameter_node_at(self, x, y):
        from models import OutputParameterNode
        n = OutputParameterNode(self._next_id(), f"OP{self.node_counter}")
        self.scene.add_flowchart_node(n, x, y)
        return n

    def create_target_parameter_node_at(self, x, y):
        from models import TargetParameterNode
        n = TargetParameterNode(self._next_id(), f"TP{self.node_counter}")
        self.scene.add_flowchart_node(n, x, y)
        return n

    def create_typed_input_node_at(self, node_type, x, y):
        """
        Instantiate a typed input node (Integer Input, Double Input, …)
        using the NODE_REGISTRY and add it to the scene.
        """
        from models import create_node_from_type
        # Derive a short prefix from the type string for the default name
        prefix = ''.join(w[0] for w in node_type.split()) + str(self.node_counter)
        n = create_node_from_type(node_type, self._next_id(), prefix)
        self.scene.add_flowchart_node(n, x, y)
        return n

    def create_generic_node_at(self, ntype, x, y):
        n = FlowchartNode(self._next_id(), ntype, f"{ntype[0]}{self.node_counter}")
        self.scene.add_flowchart_node(n, x, y)
        return n

    # ------------------------------------------------------------------
    # Toolbar / programmatic helpers (double-click path)
    # ------------------------------------------------------------------

    def add_point_node(self):
        return self.create_point_node_at(*self._auto_pos())

    def add_link_node(self):
        return self.create_link_node_at(*self._auto_pos())

    def add_shape_node(self):
        return self.create_shape_node_at(*self._auto_pos())

    def add_decision_node(self):
        return self.create_decision_node_at(*self._auto_pos())

    def add_input_parameter_node(self):
        return self.create_input_parameter_node_at(*self._auto_pos())

    def add_output_parameter_node(self):
        return self.create_output_parameter_node_at(*self._auto_pos())

    def add_target_parameter_node(self):
        return self.create_target_parameter_node_at(*self._auto_pos())

    def add_typed_input_node(self, node_type):
        """Programmatically add a typed input node at the next auto position."""
        return self.create_typed_input_node_at(node_type, *self._auto_pos())

    def get_next_node_id(self):
        return self._next_id()