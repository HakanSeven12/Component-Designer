"""
Node Widgets for Flowchart

Architecture
------------
- Every port — geometry flow, numeric value, combo selector — is a PortRow.
- Input ports  -> left side  (orange dot)
- Output ports -> right side (green dot)
- No separate "properties" form area; all parameters are ports.
- All sizes are layout-driven; no hardcoded pixel dimensions.

Connection interaction
----------------------
- Clicking anywhere on the port row (label, editor area, dot) triggers a
  connection. The PortDot is now a visual indicator only; the entire PortRow
  intercepts mouse press events and emits port_clicked.
"""

from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QComboBox, QCheckBox,
    QGraphicsProxyWidget, QGraphicsRectItem, QStyle, QSizePolicy,
)
from PySide2.QtCore import Qt, Signal, QPointF, QSize
from PySide2.QtGui import QPainter, QBrush, QColor, QPen, QFont


# ---------------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------------

INPUT_COLOR        = QColor(255, 150,  50)
OUTPUT_COLOR       = QColor(100, 200, 100)
HEADER_BG          = QColor( 70, 130, 180)
HEADER_BG_SELECTED = QColor(255, 140,   0)
BODY_BG            = QColor(248, 248, 252)
BORDER_NORMAL      = QColor( 60,  60,  60)
BORDER_SELECTED    = QColor(255, 120,   0)
SHADOW_COLOR       = QColor(  0,   0,   0, 30)
GLOW_COLOR         = QColor(255, 120,   0, 80)
DOT_RADIUS = 5

ROW_HOVER_INPUT  = QColor(255, 220, 180, 60)
ROW_HOVER_OUTPUT = QColor(180, 240, 180, 60)


# ---------------------------------------------------------------------------
# PortDot
# ---------------------------------------------------------------------------

class PortDot(QWidget):
    """Purely visual connection dot — click handling delegated to PortRow."""

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


# ---------------------------------------------------------------------------
# Shared editor style sheets
# ---------------------------------------------------------------------------

EDITOR_STYLE = """
    QDoubleSpinBox, QLineEdit, QComboBox {
        background: white; border: 1px solid #c0c0c0;
        border-radius: 3px; padding: 1px 4px; font-size: 8pt;
    }
    QDoubleSpinBox:focus, QLineEdit:focus, QComboBox:focus {
        border: 2px solid #4682B4;
    }
    QComboBox::drop-down { border: none; width: 18px; }
    QComboBox::down-arrow {
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid #555; margin-right: 4px;
    }
"""

EDITOR_STYLE_DISABLED = EDITOR_STYLE.replace(
    "background: white", "background: #e0e0e0"
)

COMBO_STYLE = """
    QComboBox {
        background: white; border: 1px solid #c0c0c0;
        border-radius: 3px; padding: 2px 4px; font-size: 8pt;
    }
    QComboBox:focus { border: 2px solid #4682B4; }
    QComboBox::drop-down { border: none; width: 18px; }
    QComboBox::down-arrow {
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid #555; margin-right: 4px;
    }
"""

LABEL_STYLE = "QLabel { font-size: 8pt; color: #444; background: transparent; }"


# ---------------------------------------------------------------------------
# ComboField  — label + combobox, no connection dot, stacked vertically
# ---------------------------------------------------------------------------

class ComboField(QWidget):
    """A standalone combo selector — no connection dot."""

    value_changed = Signal(str, object)  # (field_name, new_value)

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


# ---------------------------------------------------------------------------
# PortRow
# ---------------------------------------------------------------------------

class PortRow(QWidget):
    """
    One connectable port row.  Clicking ANYWHERE on the row triggers the
    port connection logic.

    editor_type:
      None     -> pure flow port (dot + label, no editor)
      'float'  -> QDoubleSpinBox
      'string' -> QLineEdit
      'bool'   -> QCheckBox
    """

    port_clicked  = Signal(object, str)
    value_changed = Signal(str,   object)

    def __init__(self, port_name, port_label, direction,
                 editor_type=None, editor_value=None,
                 node_item_ref=None, parent=None):
        super().__init__(parent)
        self.port_name     = port_name
        self.direction     = direction
        self.node_item_ref = node_item_ref
        self._connected    = False
        self._hovered      = False

        self._dot_color   = INPUT_COLOR if direction == 'input' else OUTPUT_COLOR
        self._hover_color = ROW_HOVER_INPUT if direction == 'input' else ROW_HOVER_OUTPUT

        self._dot = PortDot(self._dot_color, self)

        self._label = QLabel(port_label)
        self._label.setStyleSheet(
            "QLabel { font-size: 8pt; color: #1a1a1a; background: transparent; }"
        )
        self._label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._editor = self._make_editor(editor_type, editor_value)

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
            w.setStyleSheet(
                "QCheckBox { spacing: 4px; font-size: 8pt; background: transparent; }"
                "QCheckBox::indicator { width: 14px; height: 14px; }"
                "QCheckBox::indicator:unchecked { border: 1px solid #aaa;"
                " border-radius: 2px; background: white; }"
                "QCheckBox::indicator:checked { border: 1px solid #4682B4;"
                " border-radius: 2px; background: #4682B4; }"
            )
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
        if isinstance(self._editor, (QDoubleSpinBox, QLineEdit)):
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

    def enterEvent(self, event):
        self._hovered = True
        self._dot.set_hovered(True)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._dot.set_hovered(False)
        self.update()
        super().leaveEvent(event)

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


# ---------------------------------------------------------------------------
# FlowchartNodeItem
# ---------------------------------------------------------------------------

class FlowchartNodeItem(QGraphicsRectItem):
    """Draggable flowchart node."""

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
        self.container_widget.setStyleSheet("background: transparent;")

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

    # ==================================================================
    # Header
    # ==================================================================

    def _build_header(self):
        w = QWidget()
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.setStyleSheet("background: transparent;")
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        lay = QHBoxLayout()
        lay.setContentsMargins(8, 5, 8, 5)

        self._header_label = QLabel(f"{self.node.type}  ·  {self.node.name}")
        self._header_label.setStyleSheet(
            "QLabel { color: white; font-weight: bold; font-size: 9pt;"
            " background: transparent; }"
        )
        self._header_label.setAlignment(Qt.AlignCenter)
        self._header_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._header_label.mouseDoubleClickEvent = lambda e: self.edit_name()

        self._name_edit = QLineEdit(self.node.name)
        self._name_edit.setAlignment(Qt.AlignCenter)
        self._name_edit.setStyleSheet(
            "QLineEdit { color: white; font-weight: bold; font-size: 9pt;"
            " background: rgba(255,255,255,40); border: 1px solid white;"
            " border-radius: 3px; padding: 2px; }"
        )
        self._name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._name_edit.hide()
        self._name_edit.returnPressed.connect(self._finish_rename)
        self._name_edit.editingFinished.connect(self._finish_rename)

        lay.addWidget(self._header_label)
        lay.addWidget(self._name_edit)
        w.setLayout(lay)
        return w

    # ==================================================================
    # Body
    # ==================================================================

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
        """
        Build body content from port declarations.

        Layout structure:
          [combo fields — full width at top]
          [input column] | [divider] | [output column]
        """
        self.ports.clear()

        inputs  = self.node.get_input_ports()
        outputs = self.node.get_output_ports()

        combo_inputs = {n: t for n, t in inputs.items()  if isinstance(t, list)}
        port_inputs  = {n: t for n, t in inputs.items()  if not isinstance(t, list)}
        port_outputs = {n: t for n, t in outputs.items() if not isinstance(t, list)}

        # ── 1. Combo fields (full-width) ──────────────────────────────
        if combo_inputs:
            combo_section = QWidget()
            combo_section.setAttribute(Qt.WA_TranslucentBackground)
            combo_section.setStyleSheet("background: transparent;")
            cslay = QVBoxLayout()
            cslay.setContentsMargins(4, 2, 4, 4)
            cslay.setSpacing(4)
            for name, options in combo_inputs.items():
                lbl = name.replace('_', ' ').title()
                val = getattr(self.node, name, None)
                cf  = ComboField(name, lbl, options, val)
                cf.value_changed.connect(self._on_value_changed)
                cslay.addWidget(cf)
            combo_section.setLayout(cslay)
            layout.addWidget(combo_section)

            sep = QWidget()
            sep.setFixedHeight(1)
            sep.setStyleSheet("background: #d0d0d0;")
            sep.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(sep)

        # ── 2. Port columns ───────────────────────────────────────────
        def make_port_row(port_name, port_type, direction):
            etype = port_type if port_type in ('float', 'string', 'bool') else None
            eval_ = getattr(self.node, port_name, None) if etype else None

            if port_name in ('point_codes', 'link_codes') and isinstance(eval_, list):
                eval_ = ', '.join(eval_)

            if port_name == 'slope':
                lbl = 'Slope (%)'
            else:
                lbl = port_name.replace('_', ' ').title()

            pr = PortRow(
                port_name     = port_name,
                port_label    = lbl,
                direction     = direction,
                editor_type   = etype,
                editor_value  = eval_,
                node_item_ref = None,
            )
            pr.value_changed.connect(self._on_value_changed)
            pr.port_clicked.connect(self._on_port_clicked)
            self.ports[port_name] = pr
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
            for name, ptype in port_inputs.items():
                pr = make_port_row(name, ptype, 'input')
                pr.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                in_lay.addWidget(pr)
            in_lay.addStretch(1)
            in_col.setLayout(in_lay)
            col_lay.addWidget(in_col, 1)

        if has_inputs and has_outputs:
            vdiv = QWidget()
            vdiv.setFixedWidth(1)
            vdiv.setStyleSheet("background: #c8c8c8;")
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
            for name, ptype in port_outputs.items():
                pr = make_port_row(name, ptype, 'output')
                pr.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                out_lay.addWidget(pr)
            out_lay.addStretch(1)
            out_col.setLayout(out_lay)
            col_lay.addWidget(out_col, 0)

        columns.setLayout(col_lay)
        layout.addWidget(columns)

    # ==================================================================
    # Rebuild after structural combo change
    # ==================================================================

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

    # ==================================================================
    # Port scene position
    # ==================================================================

    def get_port_scene_pos(self, port_name):
        pr = self.ports.get(port_name)
        if pr:
            return pr.dot_scene_pos()
        return self.scenePos()

    # ==================================================================
    # Slots
    # ==================================================================

    def _on_port_clicked(self, node_item, port_name):
        if self.scene():
            self.scene().handle_port_click(self, port_name)

    def _on_value_changed(self, port_name, value):
        if hasattr(self.node, port_name):
            if port_name in ('point_codes', 'link_codes') and isinstance(value, str):
                codes_list = [code.strip() for code in value.split(',') if code.strip()]
                setattr(self.node, port_name, codes_list)
            else:
                setattr(self.node, port_name, value)

        # Structural combos that require a full port rebuild
        structural_ports = (
            'geometry_type',
            'link_type',
            'target_type',
            'parameter_type',  # legacy
            'data_type',       # InputParameterNode / OutputParameterNode
        )
        if port_name in structural_ports:
            from PySide2.QtCore import QTimer
            QTimer.singleShot(0, self.rebuild_ports)
            return

        if self.scene():
            self.scene().request_preview_update()

    # ==================================================================
    # Rename
    # ==================================================================

    def edit_name(self):
        self._header_label.hide()
        self._name_edit.setText(self.node.name)
        self._name_edit.show()
        self._name_edit.setFocus()
        self._name_edit.selectAll()

    def _finish_rename(self):
        name = self._name_edit.text().strip()
        if name:
            self.node.name = name
            self._header_label.setText(f"{self.node.type}  ·  {name}")
        self._name_edit.hide()
        self._header_label.show()
        self.update_size()
        if self.scene():
            self.scene().request_preview_update()

    # ==================================================================
    # Size management
    # ==================================================================

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

    # ==================================================================
    # Qt overrides
    # ==================================================================

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

        from PySide2.QtCore import QRectF
        rect = self.rect()
        sel  = self.isSelected()

        hh = self._header_widget.sizeHint().height()
        if hh <= 0:
            hh = 32

        # Shadow
        if not sel:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(SHADOW_COLOR))
            painter.drawRoundedRect(rect.adjusted(3, 3, 3, 3), 6, 6)

        # Header
        painter.setPen(QPen(BORDER_SELECTED if sel else BORDER_NORMAL, 2))
        painter.setBrush(QBrush(HEADER_BG_SELECTED if sel else HEADER_BG))
        painter.drawRoundedRect(QRectF(0, 0, rect.width(), hh), 6, 6)

        # Body
        painter.setPen(QPen(BORDER_SELECTED if sel else BORDER_NORMAL, 2))
        painter.setBrush(QBrush(BODY_BG))
        painter.drawRoundedRect(
            QRectF(0, hh, rect.width(), rect.height() - hh), 6, 6
        )

        # Seam cover
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(BODY_BG))
        painter.drawRect(QRectF(1, hh - 6, rect.width() - 2, 8))

        # Divider
        painter.setPen(QPen(BORDER_SELECTED if sel else BORDER_NORMAL, 1))
        painter.drawLine(int(rect.left() + 1), hh, int(rect.right() - 1), hh)

        # Selection glow
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

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            if self.scene() and self.scene().delete_selected_node():
                event.accept()
                return
        super().keyPressEvent(event)