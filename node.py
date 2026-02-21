"""
Node Widgets for Flowchart
"""

from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox,
    QGraphicsProxyWidget, QGraphicsRectItem, QGraphicsPolygonItem,
    QStyle, QSizePolicy, QToolTip,
)
from PySide2.QtCore import Qt, Signal, QPointF, QSize, QTimer, QRectF
from PySide2.QtGui import (
    QPainter, QBrush, QColor, QPen, QPolygonF, QFont,
)

from .theme_dark import theme
from .models.base import unpack_port, SCALAR_TYPES

INPUT_COLOR        = theme.INPUT_PORT_COLOR
OUTPUT_COLOR       = theme.OUTPUT_PORT_COLOR
HEADER_BG          = theme.HEADER_BG
HEADER_BG_SELECTED = theme.HEADER_BG_SELECTED
BODY_BG            = theme.NODE_BODY_BG
BORDER_NORMAL      = theme.NODE_BORDER_NORMAL
BORDER_SELECTED    = theme.NODE_BORDER_SEL
SHADOW_COLOR       = theme.NODE_SHADOW
GLOW_COLOR         = theme.NODE_GLOW
DOT_RADIUS = 5

ROW_HOVER_INPUT  = theme.ROW_HOVER_INPUT
ROW_HOVER_OUTPUT = theme.ROW_HOVER_OUTPUT

EDITOR_STYLE          = theme.EDITOR_STYLE
EDITOR_STYLE_DISABLED = theme.EDITOR_STYLE_DISABLED
COMBO_STYLE           = theme.COMBO_STYLE
LABEL_STYLE           = theme.LABEL_STYLE

# Decision node branch colors
_YES_COLOR = QColor(60, 200, 100)    # green — true branch
_NO_COLOR  = QColor(220, 80,  60)    # red   — false branch
_IF_HEADER = QColor(70,  55, 120)    # purple-ish header for Decision

_TOOLTIP_STYLE = """
QToolTip {
    background-color: #1a1d28;
    color: #dce3f0;
    border: 1px solid #5294e2;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 8pt;
}
"""


def _format_port_value(value) -> str:
    """
    Return a compact, human-readable string for any port value.
    Floats are shown with up to 6 significant digits (trailing zeros stripped).
    """
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, list):
        if not value:
            return "[ ]"
        return "[" + ", ".join(str(v) for v in value) + "]"
    return str(value)


class PortDot(QWidget):

    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self._color   = color
        self._hovered = False
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def sizeHint(self):
        d = DOT_RADIUS * 2 + 6
        return QSize(d, d)

    def minimumSizeHint(self):
        return self.sizeHint()

    def set_hovered(self, hovered: bool):
        self._hovered = hovered
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = self._color.lighter(130) if self._hovered else self._color
        p.setPen(QPen(c.darker(140), 1))
        p.setBrush(QBrush(c))
        r  = DOT_RADIUS
        cx = self.width()  // 2
        cy = self.height() // 2
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)


class ComboField(QWidget):

    value_changed = Signal(str, object)

    def __init__(self, field_name, field_label, options, current_value=None, parent=None):
        super().__init__(parent)
        self.field_name = field_name

        lay = QVBoxLayout()
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(2)

        lbl = QLabel(field_label)
        lbl.setStyleSheet(LABEL_STYLE)
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._combo = QComboBox()
        for opt in (options or []):
            self._combo.addItem(opt['label'], opt['value'])
        if current_value is not None:
            idx = self._combo.findData(current_value)
            if idx >= 0:
                self._combo.setCurrentIndex(idx)
        self._combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._combo.setStyleSheet(COMBO_STYLE)
        self._combo.currentIndexChanged.connect(
            lambda _: self.value_changed.emit(self.field_name, self._combo.currentData())
        )

        lay.addWidget(lbl)
        lay.addWidget(self._combo)
        self.setLayout(lay)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)


class PortRow(QWidget):
    """
    One row in the node body representing a single input or output port.

    Parameters
    ----------
    editor_type : str or None
        Scalar type string ('float', 'int', 'string', 'bool', 'percent').
        When None, no editor is built regardless of the *editor* flag.
    editor_value : any
        Initial value passed to the editor widget.
    editor : bool
        When False the inline editor widget is suppressed even when
        *editor_type* is set.  The row still renders dot + label so
        the port remains connectable via wires.
    dot_color : QColor or None
        Override the default dot colour (used by Decision node for yes/no).
    """

    port_clicked  = Signal(object, str)
    value_changed = Signal(str,   object)

    def __init__(self, port_name, port_label, direction,
                 editor_type=None, editor_value=None,
                 editor=True,
                 node_item_ref=None,
                 dot_color=None,
                 parent=None):
        super().__init__(parent)
        self.port_name     = port_name
        self.direction     = direction
        self.node_item_ref = node_item_ref
        self._connected    = False
        self._hovered      = False

        if dot_color is not None:
            self._dot_color = dot_color
        else:
            self._dot_color = INPUT_COLOR if direction == 'input' else OUTPUT_COLOR
        self._hover_color = ROW_HOVER_INPUT if direction == 'input' else ROW_HOVER_OUTPUT

        self._dot = PortDot(self._dot_color, self)

        self._label = QLabel(port_label)
        self._label.setStyleSheet(
            "QLabel { font-size: 8pt; color: #a0a8b9; background: transparent; }"
        )
        self._label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Build the editor only when both type and flag allow it.
        self._editor = self._make_editor(editor_type, editor_value) if editor else None

        row = QHBoxLayout()
        row.setContentsMargins(0, 1, 0, 1)
        row.setSpacing(4)

        if direction == 'input':
            row.addWidget(self._dot,   0, Qt.AlignVCenter)
            row.addWidget(self._label, 0, Qt.AlignVCenter)
            if self._editor:
                row.addWidget(self._editor, 1)
            else:
                row.addStretch(1)
        else:
            if self._editor:
                row.addWidget(self._editor, 1)
            else:
                row.addStretch(1)
            row.addWidget(self._label, 0, Qt.AlignVCenter)
            row.addWidget(self._dot,   0, Qt.AlignVCenter)

        self.setLayout(row)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setCursor(Qt.PointingHandCursor)

        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_AlwaysShowToolTips)

    # ------------------------------------------------------------------
    # Tooltip
    # ------------------------------------------------------------------

    def _get_current_value(self):
        if self.node_item_ref is None:
            return None
        node = self.node_item_ref.node
        if hasattr(node, 'get_port_value'):
            return node.get_port_value(self.port_name)
        return getattr(node, self.port_name, None)

    def _build_tooltip(self) -> str:
        value   = self._get_current_value()
        label   = self._label.text()
        dir_str = "Output" if self.direction == 'output' else "Input"
        lines   = [
            f"<b>{label}</b>",
            f"<span style='color:#8a98b0;'>{dir_str} port</span>",
            f"Value: <b>{_format_port_value(value)}</b>",
        ]
        return "<br>".join(lines)

    # ------------------------------------------------------------------
    # Editor factory
    # ------------------------------------------------------------------

    def _make_editor(self, etype, value):
        if etype == 'float':
            w = QDoubleSpinBox()
            w.setRange(-1e6, 1e6)
            w.setDecimals(4)
            w.setValue(float(value) if value is not None else 0.0)
            w.setMinimumWidth(75)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            w.setStyleSheet(EDITOR_STYLE)
            w.valueChanged.connect(lambda v: self.value_changed.emit(self.port_name, v))
            return w

        if etype == 'int':
            w = QSpinBox()
            w.setRange(-1_000_000, 1_000_000)
            w.setValue(int(value) if value is not None else 0)
            w.setMinimumWidth(75)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            w.setStyleSheet(EDITOR_STYLE)
            w.valueChanged.connect(lambda v: self.value_changed.emit(self.port_name, v))
            return w

        if etype == 'percent':
            w = QDoubleSpinBox()
            w.setRange(-1e6, 1e6)
            w.setDecimals(4)
            w.setSuffix(" %")
            w.setValue(float(value) if value is not None else 0.0)
            w.setMinimumWidth(85)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            w.setStyleSheet(EDITOR_STYLE)
            w.valueChanged.connect(lambda v: self.value_changed.emit(self.port_name, v))
            return w

        if etype == 'string':
            w = QLineEdit(str(value) if value is not None else "")
            w.setMinimumWidth(75)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            w.setStyleSheet(EDITOR_STYLE)
            w.textChanged.connect(lambda v: self.value_changed.emit(self.port_name, v))
            return w

        if etype == 'bool':
            w = QCheckBox()
            w.setChecked(bool(value) if value is not None else False)
            w.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            w.setStyleSheet(theme.CHECKBOX_STYLE)
            w.toggled.connect(lambda v: self.value_changed.emit(self.port_name, v))
            return w

        return None

    def set_node_item(self, node_item):
        self.node_item_ref = node_item

    def set_connected(self, connected: bool):
        self._connected = connected
        if self._editor is None:
            return
        style = EDITOR_STYLE_DISABLED if connected else EDITOR_STYLE
        self._editor.setStyleSheet(style)
        if isinstance(self._editor, (QDoubleSpinBox, QSpinBox, QLineEdit)):
            self._editor.setReadOnly(connected)
        if isinstance(self._editor, QCheckBox):
            self._editor.setEnabled(not connected)

    def dot_scene_pos(self) -> QPointF:
        if self.node_item_ref is None:
            return QPointF(0, 0)
        local = self.mapTo(
            self.node_item_ref.container_widget,
            (QPointF(self._dot.x(), self._dot.y()) +
             QPointF(self._dot.width() / 2, self._dot.height() / 2)).toPoint(),
        )
        return self.node_item_ref.proxy.mapToScene(local)

    # ------------------------------------------------------------------
    # Mouse events
    # ------------------------------------------------------------------

    def enterEvent(self, event):
        self._hovered = True
        self._dot.set_hovered(True)
        self.update()
        self.setToolTip("")
        QToolTip.showText(self._resolve_global_cursor_pos(), self._build_tooltip())
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._dot.set_hovered(False)
        self.update()
        QToolTip.hideText()
        super().leaveEvent(event)

    def _resolve_global_cursor_pos(self):
        from PySide2.QtGui import QCursor
        return QCursor.pos()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.node_item_ref:
                self.port_clicked.emit(self.node_item_ref, self.port_name)
            event.accept()
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event):
        if self._hovered:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(self._hover_color))
            p.drawRoundedRect(self.rect(), 3, 3)
        super().paintEvent(event)


# ===========================================================================
# Standard node item
# ===========================================================================

class FlowchartNodeItem(QGraphicsRectItem):

    def __init__(self, node, x, y, parent=None):
        super().__init__(0, 0, 10, 10, parent)
        self.node = node
        self.setPos(x, y)
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemSendsGeometryChanges,
        )

        self.ports: dict = {}

        self.container_widget = QWidget()
        self.container_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.container_widget.setStyleSheet(
            "background: transparent;" + _TOOLTIP_STYLE
        )

        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header_widget = self._build_header()
        root.addWidget(self._header_widget)

        self._body_widget, self._body_layout = self._build_body()
        root.addWidget(self._body_widget)

        self.container_widget.setLayout(root)

        self.proxy = QGraphicsProxyWidget(self)
        self.proxy.setWidget(self.container_widget)
        self.proxy.setPos(0, 0)

        for pr in self.ports.values():
            pr.set_node_item(self)

        self.update_size()
        self.setData(0, node)

    # ------------------------------------------------------------------
    # Build header
    # ------------------------------------------------------------------

    def _build_header(self):
        w = QWidget()
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.setStyleSheet("background: transparent;")
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        lay = QHBoxLayout()
        lay.setContentsMargins(8, 5, 8, 5)

        self._header_label = QLabel(f"{self.node.type}  ·  {self.node.name}")
        self._header_label.setStyleSheet(theme.HEADER_LABEL_STYLE)
        self._header_label.setAlignment(Qt.AlignCenter)
        self._header_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._header_label.mouseDoubleClickEvent = lambda e: self.edit_name()

        self._name_edit = QLineEdit(self.node.name)
        self._name_edit.setAlignment(Qt.AlignCenter)
        self._name_edit.setStyleSheet(theme.NAME_EDIT_STYLE)
        self._name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._name_edit.hide()
        self._name_edit.returnPressed.connect(self._finish_rename)
        self._name_edit.editingFinished.connect(self._finish_rename)

        lay.addWidget(self._header_label)
        lay.addWidget(self._name_edit)
        w.setLayout(lay)
        return w

    # ------------------------------------------------------------------
    # Build body
    # ------------------------------------------------------------------

    def _build_body(self):
        w = QWidget()
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.setStyleSheet("background: transparent;")
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        lay = QVBoxLayout()
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(2)

        self._populate_port_rows(lay)
        lay.addStretch(0)

        w.setLayout(lay)
        return w, lay

    def _populate_port_rows(self, layout):
        self.ports.clear()

        inputs  = self.node.get_input_ports()
        outputs = self.node.get_output_ports()

        # Separate combo (list) ports from scalar/ref ports.
        def _is_combo(port_def):
            if isinstance(port_def, list):
                return True
            if isinstance(port_def, dict) and isinstance(port_def.get('type'), list):
                return True
            return False

        combo_inputs  = {n: d for n, d in inputs.items()  if _is_combo(d)}
        combo_outputs = {n: d for n, d in outputs.items() if _is_combo(d)}
        port_inputs   = {n: d for n, d in inputs.items()  if not _is_combo(d)}
        port_outputs  = {n: d for n, d in outputs.items() if not _is_combo(d)}

        # ── Combo section ────────────────────────────────────────────────
        all_combos = list(combo_inputs.items()) + list(combo_outputs.items())
        if all_combos:
            combo_section = QWidget()
            combo_section.setAttribute(Qt.WA_TranslucentBackground)
            combo_section.setStyleSheet("background: transparent;")
            cslay = QVBoxLayout()
            cslay.setContentsMargins(4, 2, 4, 4)
            cslay.setSpacing(4)
            for name, port_def in all_combos:
                opts = (port_def.get('type') if isinstance(port_def, dict)
                        else port_def)
                lbl  = name.replace('_', ' ').title()
                val  = getattr(self.node, name, None)
                cf   = ComboField(name, lbl, opts, val)
                cf.value_changed.connect(self._on_value_changed)
                cslay.addWidget(cf)
            combo_section.setLayout(cslay)
            layout.addWidget(combo_section)

            sep = QWidget()
            sep.setFixedHeight(1)
            sep.setStyleSheet(theme.SEPARATOR_STYLE)
            sep.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(sep)

        # ── Port row factory ─────────────────────────────────────────────
        def make_port_row(port_name, port_def, direction, dot_color=None):
            ptype, show_editor = unpack_port(port_def)

            if ptype in SCALAR_TYPES:
                if hasattr(self.node, 'get_port_value'):
                    eval_ = self.node.get_port_value(port_name)
                else:
                    eval_ = getattr(self.node, port_name, None)
            else:
                eval_ = None

            if port_name in ('point_codes', 'link_codes') and isinstance(eval_, list):
                eval_ = ', '.join(eval_)

            lbl = ('Slope (%)' if port_name == 'slope'
                   else port_name.replace('_', ' ').title())

            pr = PortRow(
                port_name    = port_name,
                port_label   = lbl,
                direction    = direction,
                editor_type  = ptype if ptype in SCALAR_TYPES else None,
                editor_value = eval_,
                editor       = show_editor,
                node_item_ref= None,
                dot_color    = dot_color,
            )
            pr.value_changed.connect(self._on_value_changed)
            pr.port_clicked.connect(self._on_port_clicked)
            self.ports[port_name] = pr

            if direction == 'output' and not hasattr(self.node, port_name):
                pr.set_connected(True)

            return pr

        has_inputs  = bool(port_inputs)
        has_outputs = bool(port_outputs)

        if not has_inputs and not has_outputs:
            return

        columns = QWidget()
        columns.setAttribute(Qt.WA_TranslucentBackground)
        columns.setStyleSheet("background: transparent;")
        col_lay = QHBoxLayout()
        col_lay.setContentsMargins(0, 2, 0, 2)
        col_lay.setSpacing(0)

        if has_inputs:
            in_col = QWidget()
            in_col.setAttribute(Qt.WA_TranslucentBackground)
            in_col.setStyleSheet("background: transparent;")
            in_lay = QVBoxLayout()
            in_lay.setContentsMargins(0, 0, 0, 0)
            in_lay.setSpacing(1)
            for name, pdef in port_inputs.items():
                pr = make_port_row(name, pdef, 'input')
                pr.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                in_lay.addWidget(pr)
            in_lay.addStretch(1)
            in_col.setLayout(in_lay)
            col_lay.addWidget(in_col, 1)

        if has_inputs and has_outputs:
            vdiv = QWidget()
            vdiv.setFixedWidth(1)
            vdiv.setStyleSheet(theme.VDIVIDER_STYLE)
            vdiv.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            col_lay.addWidget(vdiv)
            col_lay.addSpacing(4)

        if has_outputs:
            out_col = QWidget()
            out_col.setAttribute(Qt.WA_TranslucentBackground)
            out_col.setStyleSheet("background: transparent;")
            out_lay = QVBoxLayout()
            out_lay.setContentsMargins(0, 0, 0, 0)
            out_lay.setSpacing(1)
            for name, pdef in port_outputs.items():
                pr = make_port_row(name, pdef, 'output')
                pr.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                out_lay.addWidget(pr)
            out_lay.addStretch(1)
            out_col.setLayout(out_lay)
            col_lay.addWidget(out_col, 0)

        columns.setLayout(col_lay)
        layout.addWidget(columns)

    # ------------------------------------------------------------------
    # Rebuild ports after structural change
    # ------------------------------------------------------------------

    def rebuild_ports(self):
        self._body_widget.blockSignals(True)

        lay = self._body_layout
        widgets_to_remove = []
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w:
                widgets_to_remove.append(w)
        for w in widgets_to_remove:
            w.hide()
            w.setParent(None)

        self.ports.clear()
        self._populate_port_rows(lay)
        lay.addStretch(0)

        for pr in self.ports.values():
            pr.set_node_item(self)

        self._body_widget.blockSignals(False)
        self.update_size()

    def get_port_scene_pos(self, port_name):
        pr = self.ports.get(port_name)
        if pr:
            return pr.dot_scene_pos()
        return self.scenePos()

    def _on_port_clicked(self, node_item, port_name):
        if self.scene():
            self.scene().handle_port_click(self, port_name)

    # ------------------------------------------------------------------
    # Value changes
    # ------------------------------------------------------------------

    def _on_value_changed(self, port_name, value):
        node = self.node

        if port_name in ('point_codes', 'link_codes'):
            old_raw   = getattr(node, port_name, [])
            old_value = ', '.join(old_raw) if isinstance(old_raw, list) else old_raw
        else:
            old_value = getattr(node, port_name, None)

        if old_value == value:
            self._apply_value(port_name, value)
            return

        sc = self.scene()
        if sc and hasattr(sc, 'undo_stack'):
            from .undo_stack import ChangeValueCommand
            cmd = ChangeValueCommand(sc, self, port_name, old_value, value)
            sc.undo_stack._stack = sc.undo_stack._stack[:sc.undo_stack._index + 1]
            sc.undo_stack._stack.append(cmd)
            sc.undo_stack._index = len(sc.undo_stack._stack) - 1

        self._apply_value(port_name, value)

    def _apply_value(self, port_name, value):
        node = self.node

        if port_name in ('point_codes', 'link_codes') and isinstance(value, str):
            codes_list = [code.strip() for code in value.split(',') if code.strip()]
            setattr(node, port_name, codes_list)
        else:
            if hasattr(node, port_name):
                setattr(node, port_name, value)

        if port_name in ('rise', 'run') and hasattr(node, 'percent'):
            percent_row = self.ports.get('percent')
            if percent_row and percent_row._editor is not None:
                percent_row._editor.blockSignals(True)
                percent_row._editor.setValue(node.percent)
                percent_row._editor.blockSignals(False)

        structural_ports = ('geometry_type', 'link_type', 'target_type', 'data_type')
        if port_name in structural_ports:
            QTimer.singleShot(0, self.rebuild_ports)
            return

        if self.scene():
            self.scene().request_preview_update()

    # ------------------------------------------------------------------
    # Rename
    # ------------------------------------------------------------------

    def edit_name(self):
        self._pending_rename_old = self.node.name
        self._header_label.hide()
        self._name_edit.setText(self.node.name)
        self._name_edit.show()
        self._name_edit.setFocus()
        self._name_edit.selectAll()

    def _finish_rename(self):
        new_name = self._name_edit.text().strip()
        self._name_edit.hide()
        self._header_label.show()

        if not new_name:
            return

        old_name = getattr(self, '_pending_rename_old', self.node.name)
        if new_name == old_name:
            return

        sc = self.scene()
        if sc and hasattr(sc, 'undo_stack'):
            from .undo_stack import RenameNodeCommand
            cmd = RenameNodeCommand(sc, self, old_name, new_name)
            self.node.name = new_name
            self._header_label.setText(f"{self.node.type}  ·  {new_name}")
            sc.undo_stack._stack = sc.undo_stack._stack[:sc.undo_stack._index + 1]
            sc.undo_stack._stack.append(cmd)
            sc.undo_stack._index = len(sc.undo_stack._stack) - 1
            sc.request_preview_update()
        else:
            self.node.name = new_name
            self._header_label.setText(f"{self.node.type}  ·  {new_name}")

        self.update_size()
        if self.scene():
            self.scene().request_preview_update()

    # ------------------------------------------------------------------
    # Size / paint
    # ------------------------------------------------------------------

    def update_size(self):
        lay = self.container_widget.layout()
        if lay:
            lay.activate()

        msh = self.container_widget.minimumSizeHint()
        sh  = self.container_widget.sizeHint()

        w = max(msh.width(),  sh.width()  if sh.width()  > 0 else 0) + 4
        h = max(msh.height(), sh.height() if sh.height() > 0 else 0) + 4

        self.setRect(0, 0, w, h)
        self.container_widget.setFixedSize(w, h)
        self.proxy.setMinimumSize(w, h)
        self.proxy.setMaximumSize(w, h)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange:
            self.node.x = value.x()
            self.node.y = value.y()
            if self.scene():
                self.scene().update_port_wires(self)
                self.scene().request_preview_update()
        elif change == QGraphicsRectItem.ItemPositionHasChanged:
            if self.scene():
                self.scene().update()
        elif change == QGraphicsRectItem.ItemSelectedChange:
            self.update()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget=None):
        option.state &= ~QStyle.State_Selected
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        sel  = self.isSelected()

        hh = self._header_widget.sizeHint().height()
        if hh <= 0:
            hh = 32

        if not sel:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(SHADOW_COLOR))
            painter.drawRoundedRect(rect.adjusted(3, 3, 3, 3), 6, 6)

        painter.setPen(QPen(BORDER_SELECTED if sel else BORDER_NORMAL, 2))
        painter.setBrush(QBrush(HEADER_BG_SELECTED if sel else HEADER_BG))
        painter.drawRoundedRect(QRectF(0, 0, rect.width(), hh), 6, 6)

        painter.setPen(QPen(BORDER_SELECTED if sel else BORDER_NORMAL, 2))
        painter.setBrush(QBrush(BODY_BG))
        painter.drawRoundedRect(
            QRectF(0, hh, rect.width(), rect.height() - hh), 6, 6
        )

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(BODY_BG))
        painter.drawRect(QRectF(1, hh - 6, rect.width() - 2, 8))

        painter.setPen(QPen(BORDER_SELECTED if sel else BORDER_NORMAL, 1))
        painter.drawLine(int(rect.left() + 1), hh, int(rect.right() - 1), hh)

        if sel:
            painter.setPen(QPen(GLOW_COLOR, 8))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(-4, -4, 4, 4), 8, 8)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_selected.emit(self.node)

    def mouseDoubleClickEvent(self, event):
        self.edit_name()


# ===========================================================================
# Decision node item  —  IF/ELSE visual with diamond header
# ===========================================================================

class DecisionNodeItem(FlowchartNodeItem):
    """
    A specialised FlowchartNodeItem for DecisionNode.

    Visual differences from the standard node
    ------------------------------------------
    * Header is drawn as a **diamond (rhombus)** shape that protrudes above
      the rectangular body, giving the classic flowchart "decision" look.
    * Header background uses a distinct purple colour so it stands out.
    * The 'yes' output port dot is green and labelled "YES ✔".
    * The 'no'  output port dot is red   and labelled "NO ✘".
    * A small "IF" badge is rendered inside the diamond tip.
    * Active branch label ("▶ YES" / "▶ NO") is shown below the condition
      spinbox so the user can see at a glance which branch is live.
    """

    # Extra pixels the diamond tip protrudes above the widget rect
    _DIAMOND_OVERHANG = 14

    def __init__(self, node, x, y, parent=None):
        # We need the overhang space so shift the proxy widget down.
        super().__init__(node, x, y, parent)
        # Move the proxy widget down to leave room for the diamond tip
        self.proxy.setPos(0, self._DIAMOND_OVERHANG)
        self.update_size()

    # ------------------------------------------------------------------
    # Override header: no rounded rect header widget — diamond is painted
    # directly in paint().  We keep the widget for the name label only.
    # ------------------------------------------------------------------

    def _build_header(self):
        """
        Build a slim header widget that contains only the name label and
        rename edit.  The diamond shape is rendered purely via QPainter.
        """
        w = QWidget()
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.setStyleSheet("background: transparent;")
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        lay = QHBoxLayout()
        # Top margin = diamond overhang so text sits below the diamond tip
        lay.setContentsMargins(8, self._DIAMOND_OVERHANG + 2, 8, 4)

        self._header_label = QLabel(f"IF  ·  {self.node.name}")
        self._header_label.setStyleSheet(
            "QLabel { color: #e8d870; font-weight: bold; "
            "font-size: 9pt; background: transparent; }"
        )
        self._header_label.setAlignment(Qt.AlignCenter)
        self._header_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._header_label.mouseDoubleClickEvent = lambda e: self.edit_name()

        self._name_edit = QLineEdit(self.node.name)
        self._name_edit.setAlignment(Qt.AlignCenter)
        self._name_edit.setStyleSheet(theme.NAME_EDIT_STYLE)
        self._name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._name_edit.hide()
        self._name_edit.returnPressed.connect(self._finish_rename)
        self._name_edit.editingFinished.connect(self._finish_rename)

        lay.addWidget(self._header_label)
        lay.addWidget(self._name_edit)
        w.setLayout(lay)
        return w

    # ------------------------------------------------------------------
    # Override body: add coloured yes/no port rows + live branch badge
    # ------------------------------------------------------------------

    def _populate_port_rows(self, layout):
        """
        Custom port layout for Decision node:

        ┌─ INPUT ──────────────────────┐
        │  ● condition  [spinbox]       │
        ├──────────────────────────────┤
        │  Active branch badge          │
        ├─ OUTPUT ─────────────────────┤
        │             YES ✔  ●(green)  │
        │              NO ✘  ●(red)    │
        └──────────────────────────────┘
        """
        self.ports.clear()

        # ── condition input port ─────────────────────────────────────────
        cond_val = getattr(self.node, 'condition', 0.0)
        cond_row = PortRow(
            port_name    = 'condition',
            port_label   = 'Condition',
            direction    = 'input',
            editor_type  = 'float',
            editor_value = cond_val,
            editor       = True,
            node_item_ref= None,
        )
        cond_row.value_changed.connect(self._on_value_changed)
        cond_row.port_clicked.connect(self._on_port_clicked)
        self.ports['condition'] = cond_row
        layout.addWidget(cond_row)

        # ── separator ────────────────────────────────────────────────────
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(theme.SEPARATOR_STYLE)
        sep.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(sep)

        # ── active-branch badge ──────────────────────────────────────────
        self._branch_badge = QLabel(self._branch_text())
        self._branch_badge.setAlignment(Qt.AlignCenter)
        self._branch_badge.setStyleSheet(
            "QLabel { font-size: 8pt; font-weight: bold; "
            "background: transparent; padding: 2px; }"
        )
        self._update_branch_badge_color()
        layout.addWidget(self._branch_badge)

        # ── separator ────────────────────────────────────────────────────
        sep2 = QWidget()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(theme.SEPARATOR_STYLE)
        sep2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(sep2)

        # ── yes output port (green dot) ───────────────────────────────────
        yes_row = PortRow(
            port_name    = 'yes',
            port_label   = 'YES  ✔',
            direction    = 'output',
            editor_type  = None,
            editor_value = None,
            editor       = False,
            node_item_ref= None,
            dot_color    = _YES_COLOR,
        )
        yes_row.port_clicked.connect(self._on_port_clicked)
        yes_row._label.setStyleSheet(
            "QLabel { font-size: 8pt; font-weight: bold; "
            "color: #3cc870; background: transparent; }"
        )
        self.ports['yes'] = yes_row
        layout.addWidget(yes_row)

        # ── no output port (red dot) ──────────────────────────────────────
        no_row = PortRow(
            port_name    = 'no',
            port_label   = 'NO  ✘',
            direction    = 'output',
            editor_type  = None,
            editor_value = None,
            editor       = False,
            node_item_ref= None,
            dot_color    = _NO_COLOR,
        )
        no_row.port_clicked.connect(self._on_port_clicked)
        no_row._label.setStyleSheet(
            "QLabel { font-size: 8pt; font-weight: bold; "
            "color: #e05040; background: transparent; }"
        )
        self.ports['no'] = no_row
        layout.addWidget(no_row)

    # ------------------------------------------------------------------
    # Branch badge helpers
    # ------------------------------------------------------------------

    def _branch_text(self) -> str:
        is_true = bool(getattr(self.node, 'condition', 0.0))
        return "▶  YES branch active" if is_true else "▶  NO branch active"

    def _update_branch_badge_color(self):
        is_true = bool(getattr(self.node, 'condition', 0.0))
        color   = "#3cc870" if is_true else "#e05040"
        self._branch_badge.setStyleSheet(
            f"QLabel {{ font-size: 8pt; font-weight: bold; "
            f"color: {color}; background: transparent; padding: 2px; }}"
        )

    # ------------------------------------------------------------------
    # Override _apply_value to also refresh the branch badge
    # ------------------------------------------------------------------

    def _apply_value(self, port_name, value):
        super()._apply_value(port_name, value)
        if port_name == 'condition' and hasattr(self, '_branch_badge'):
            self._branch_badge.setText(self._branch_text())
            self._update_branch_badge_color()

    # ------------------------------------------------------------------
    # Override update_size: add overhang to the rect height
    # ------------------------------------------------------------------

    def update_size(self):
        lay = self.container_widget.layout()
        if lay:
            lay.activate()

        msh = self.container_widget.minimumSizeHint()
        sh  = self.container_widget.sizeHint()

        w = max(msh.width(),  sh.width()  if sh.width()  > 0 else 0) + 4
        h = max(msh.height(), sh.height() if sh.height() > 0 else 0) + 4

        # Expand the bounding rect upward to include the diamond overhang
        total_h = h + self._DIAMOND_OVERHANG

        self.setRect(0, 0, w, total_h)
        self.container_widget.setFixedSize(w, h)
        if hasattr(self, 'proxy'):
            self.proxy.setPos(0, self._DIAMOND_OVERHANG)
            self.proxy.setMinimumSize(w, h)
            self.proxy.setMaximumSize(w, h)

    # ------------------------------------------------------------------
    # Override rename helpers to use "IF · name" format
    # ------------------------------------------------------------------

    def _finish_rename(self):
        new_name = self._name_edit.text().strip()
        self._name_edit.hide()
        self._header_label.show()

        if not new_name:
            return

        old_name = getattr(self, '_pending_rename_old', self.node.name)
        if new_name == old_name:
            return

        sc = self.scene()
        if sc and hasattr(sc, 'undo_stack'):
            from .undo_stack import RenameNodeCommand
            cmd = RenameNodeCommand(sc, self, old_name, new_name)
            self.node.name = new_name
            self._header_label.setText(f"IF  ·  {new_name}")
            sc.undo_stack._stack = sc.undo_stack._stack[:sc.undo_stack._index + 1]
            sc.undo_stack._stack.append(cmd)
            sc.undo_stack._index = len(sc.undo_stack._stack) - 1
            sc.request_preview_update()
        else:
            self.node.name = new_name
            self._header_label.setText(f"IF  ·  {new_name}")

        self.update_size()
        if self.scene():
            self.scene().request_preview_update()

    # ------------------------------------------------------------------
    # Paint — diamond header + standard body
    # ------------------------------------------------------------------

    def paint(self, painter, option, widget=None):
        option.state &= ~QStyle.State_Selected
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        sel  = self.isSelected()
        w    = rect.width()
        oh   = self._DIAMOND_OVERHANG   # diamond overhang above the body

        # Body top starts at oh; header height is the label widget height
        hh = self._header_widget.sizeHint().height()
        if hh <= 0:
            hh = 36
        body_top = oh

        # ── Drop shadow ────────────────────────────────────────────────
        if not sel:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(SHADOW_COLOR))
            painter.drawRoundedRect(
                QRectF(3, oh + 3, w, rect.height() - oh),
                6, 6
            )

        # ── Body (rounded rect below the diamond) ──────────────────────
        border_pen = QPen(BORDER_SELECTED if sel else _IF_HEADER.lighter(160), 2)
        painter.setPen(border_pen)
        painter.setBrush(QBrush(BODY_BG))
        painter.drawRoundedRect(
            QRectF(0, body_top, w, rect.height() - body_top),
            6, 6
        )

        # ── Header band inside the body (where the label sits) ─────────
        header_color = _IF_HEADER.lighter(130) if sel else _IF_HEADER
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(header_color))
        painter.drawRoundedRect(
            QRectF(1, body_top + 1, w - 2, hh - 2),
            5, 5
        )
        # Fill bottom corners of header so it blends with body
        painter.drawRect(QRectF(1, body_top + hh - 8, w - 2, 9))

        # Separator line between header and body ports
        painter.setPen(QPen(border_pen.color().darker(110), 1))
        painter.drawLine(int(1), body_top + hh, int(w - 1), body_top + hh)

        # ── Diamond tip (protruding above the body) ────────────────────
        cx = w / 2.0
        diamond = QPolygonF([
            QPointF(cx,       0),           # top tip
            QPointF(cx + 18,  oh),          # right
            QPointF(cx - 18,  oh),          # left
        ])
        diamond_body = QPolygonF([
            QPointF(cx - 18,  oh),
            QPointF(cx + 18,  oh),
            QPointF(cx + 24,  oh + 14),
            QPointF(cx - 24,  oh + 14),
        ])

        # Draw diamond fill
        painter.setPen(QPen(border_pen.color(), 1.5))
        painter.setBrush(QBrush(header_color))
        painter.drawPolygon(diamond)
        painter.drawPolygon(diamond_body)

        # "IF" text inside the diamond tip
        painter.setPen(QColor(240, 230, 130))
        f = QFont()
        f.setPointSizeF(7.5)
        f.setBold(True)
        painter.setFont(f)
        painter.drawText(
            QRectF(cx - 12, 1, 24, oh - 1),
            Qt.AlignHCenter | Qt.AlignVCenter,
            "IF",
        )

        # ── Selection glow ─────────────────────────────────────────────
        if sel:
            painter.setPen(QPen(GLOW_COLOR, 8))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                QRectF(-4, oh - 4, w + 8, rect.height() - oh + 8),
                8, 8
            )