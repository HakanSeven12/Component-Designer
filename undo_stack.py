"""
Undo/Redo command stack for Component Designer.

Implements the Command Pattern.  Every mutating action in the flowchart
creates a Command object and pushes it onto UndoStack.  Ctrl+Z pops the
last command and calls its undo(); Ctrl+Y / Ctrl+Shift+Z redoes it.

Supported commands
------------------
AddNodeCommand       – node dropped / double-clicked from toolbox
DeleteNodeCommand    – Delete / Backspace key
MoveNodeCommand      – node dragged to a new position
AddConnectionCommand – wire drawn between two ports
RemoveConnectionCommand – wire removed by clicking a connected input port
ChangeValueCommand   – any port-editor value change (spinbox, lineedit, …)
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .flowchart import FlowchartScene


# ---------------------------------------------------------------------------
# Base command
# ---------------------------------------------------------------------------

class Command:
    """Abstract base for all undoable commands."""

    def redo(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError

    # Human-readable description shown in the status bar
    description: str = "action"


# ---------------------------------------------------------------------------
# Concrete commands
# ---------------------------------------------------------------------------

class AddNodeCommand(Command):
    """Records the addition of a single node to the scene."""

    description = "Add node"

    def __init__(self, scene: "FlowchartScene", node, x: float, y: float):
        self._scene = scene
        self._node  = node
        self._x     = x
        self._y     = y
        self._item  = None          # FlowchartNodeItem, filled on first redo

    def redo(self):
        self._item = self._scene.add_flowchart_node(self._node, self._x, self._y)

    def undo(self):
        if self._item is not None:
            self._scene._remove_node_item(self._item, record_undo=False)


class DeleteNodeCommand(Command):
    """Records the deletion of a node together with all its wires."""

    description = "Delete node"

    def __init__(self, scene: "FlowchartScene", item):
        from .node import FlowchartNodeItem   # local import to avoid cycles
        self._scene = scene
        self._item  = item
        self._node  = item.node

        # Snapshot position
        self._x = item.node.x
        self._y = item.node.y

        # Snapshot every wire that touches this node so we can restore them
        self._affected_wires = [
            dict(w) for w in scene.port_wires
            if w['from_item'] is item or w['to_item'] is item
        ]
        self._affected_connections = [
            dict(c) for c in scene.connections
            if c['from'] == self._node.id or c['to'] == self._node.id
        ]

    def redo(self):
        self._scene._remove_node_item(self._item, record_undo=False)

    def undo(self):
        # Re-add the node
        self._item = self._scene.add_flowchart_node(
            self._node, self._x, self._y
        )
        # Restore wires
        for conn in self._affected_connections:
            from_node = self._scene.nodes.get(conn['from'])
            to_node   = self._scene.nodes.get(conn['to'])
            if from_node and to_node:
                self._scene.connect_nodes_with_wire(
                    from_node, to_node,
                    conn.get('from_port', 'vector'),
                    conn.get('to_port',   'reference'),
                )
        self._scene.request_preview_update()


class MoveNodeCommand(Command):
    """Records a node being dragged from one position to another."""

    description = "Move node"

    def __init__(self, scene: "FlowchartScene", item,
                 old_pos, new_pos):
        self._scene   = scene
        self._item    = item
        self._old_pos = old_pos   # QPointF
        self._new_pos = new_pos   # QPointF

    def redo(self):
        self._item.setPos(self._new_pos)
        self._item.node.x = self._new_pos.x()
        self._item.node.y = self._new_pos.y()
        self._scene.update_port_wires(self._item)

    def undo(self):
        self._item.setPos(self._old_pos)
        self._item.node.x = self._old_pos.x()
        self._item.node.y = self._old_pos.y()
        self._scene.update_port_wires(self._item)


class AddConnectionCommand(Command):
    """Records a wire being drawn between two ports."""

    description = "Connect ports"

    def __init__(self, scene: "FlowchartScene",
                 from_item, from_port: str,
                 to_item,   to_port: str):
        self._scene     = scene
        self._from_item = from_item
        self._from_port = from_port
        self._to_item   = to_item
        self._to_port   = to_port

    def redo(self):
        self._scene.connect_nodes_with_wire(
            self._from_item.node, self._to_item.node,
            self._from_port, self._to_port,
        )

    def undo(self):
        self._scene._disconnect_input_port(
            self._to_item, self._to_port, record_undo=False
        )


class RemoveConnectionCommand(Command):
    """Records a wire being removed by clicking a connected input port."""

    description = "Disconnect ports"

    def __init__(self, scene: "FlowchartScene",
                 from_item, from_port: str,
                 to_item,   to_port: str):
        self._scene     = scene
        self._from_item = from_item
        self._from_port = from_port
        self._to_item   = to_item
        self._to_port   = to_port

    def redo(self):
        self._scene._disconnect_input_port(
            self._to_item, self._to_port, record_undo=False
        )

    def undo(self):
        self._scene.connect_nodes_with_wire(
            self._from_item.node, self._to_item.node,
            self._from_port, self._to_port,
        )


class ChangeValueCommand(Command):
    """Records a port-editor value change on a node."""

    description = "Change value"

    def __init__(self, scene: "FlowchartScene", item,
                 port_name: str, old_value, new_value):
        self._scene     = scene
        self._item      = item
        self._port_name = port_name
        self._old_value = old_value
        self._new_value = new_value

    def redo(self):
        self._apply(self._new_value)

    def undo(self):
        self._apply(self._old_value)

    def _apply(self, value):
        node = self._item.node
        port = self._port_name

        # Mirror the logic in FlowchartNodeItem._on_value_changed
        if port in ('point_codes', 'link_codes') and isinstance(value, str):
            codes = [c.strip() for c in value.split(',') if c.strip()]
            setattr(node, port, codes)
        elif port in ('point_codes', 'link_codes') and isinstance(value, list):
            setattr(node, port, value)
        else:
            if hasattr(node, port):
                setattr(node, port, value)

        structural = ('geometry_type', 'link_type', 'target_type', 'data_type')
        if port in structural:
            self._item.rebuild_ports()

        # Refresh the widget editor to reflect the applied value
        pr = self._item.ports.get(port)
        if pr and pr._editor is not None:
            self._sync_editor(pr._editor, value)

        self._scene.request_preview_update()

    @staticmethod
    def _sync_editor(editor, value):
        from PySide2.QtWidgets import (QDoubleSpinBox, QSpinBox,
                                       QLineEdit, QCheckBox)
        editor.blockSignals(True)
        try:
            if isinstance(editor, (QDoubleSpinBox, QSpinBox)):
                editor.setValue(value if value is not None else 0)
            elif isinstance(editor, QLineEdit):
                if isinstance(value, list):
                    editor.setText(', '.join(str(v) for v in value))
                else:
                    editor.setText(str(value) if value is not None else '')
            elif isinstance(editor, QCheckBox):
                editor.setChecked(bool(value))
        finally:
            editor.blockSignals(False)


class RenameNodeCommand(Command):
    """Records a node name change."""

    description = "Rename node"

    def __init__(self, scene: "FlowchartScene", item,
                 old_name: str, new_name: str):
        self._scene    = scene
        self._item     = item
        self._old_name = old_name
        self._new_name = new_name

    def redo(self):
        self._set(self._new_name)

    def undo(self):
        self._set(self._old_name)

    def _set(self, name: str):
        self._item.node.name = name
        self._item._header_label.setText(
            f"{self._item.node.type}  ·  {name}"
        )
        self._scene.request_preview_update()


# ---------------------------------------------------------------------------
# Undo stack
# ---------------------------------------------------------------------------

class UndoStack:
    """
    Manages undo/redo history.

    Usage::

        stack = UndoStack(max_depth=100)
        stack.push(SomeCommand(...))   # executes redo() and records
        stack.undo()
        stack.redo()
    """

    def __init__(self, max_depth: int = 100):
        self._stack: list[Command] = []
        self._index: int           = -1    # points to the last executed command
        self._max_depth            = max_depth

    # ------------------------------------------------------------------
    def push(self, command: Command):
        """Execute *command* and add it to the history."""
        # Discard any undone future
        self._stack = self._stack[: self._index + 1]

        command.redo()
        self._stack.append(command)
        self._index = len(self._stack) - 1

        # Trim oldest entries when over the limit
        if len(self._stack) > self._max_depth:
            trim = len(self._stack) - self._max_depth
            self._stack = self._stack[trim:]
            self._index = len(self._stack) - 1

    def undo(self) -> str | None:
        """Undo the last command.  Returns its description or None."""
        if not self.can_undo():
            return None
        cmd = self._stack[self._index]
        cmd.undo()
        self._index -= 1
        return cmd.description

    def redo(self) -> str | None:
        """Redo the next undone command.  Returns its description or None."""
        if not self.can_redo():
            return None
        self._index += 1
        cmd = self._stack[self._index]
        cmd.redo()
        return cmd.description

    def can_undo(self) -> bool:
        return self._index >= 0

    def can_redo(self) -> bool:
        return self._index < len(self._stack) - 1

    def clear(self):
        self._stack.clear()
        self._index = -1

    @property
    def undo_description(self) -> str | None:
        if self.can_undo():
            return self._stack[self._index].description
        return None

    @property
    def redo_description(self) -> str | None:
        if self.can_redo():
            return self._stack[self._index + 1].description
        return None
