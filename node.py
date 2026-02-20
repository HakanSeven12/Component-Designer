"""
Node Widgets for Flowchart
"""

from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox,
    QGraphicsProxyWidget, QGraphicsRectItem, QStyle, QSizePolicy,
)
from PySide2.QtCore import Qt, Signal, QPointF, QSize, QTimer, QRectF
from PySide2.QtGui import QPainter, QBrush, QColor, QPen

from .theme_dark import theme

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
            "QLabel { font-size: 8pt; color: #a0a8b9; background: transparent; }"
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

        combo_inputs  = {n: t for n, t in inputs.items()  if isinstance(t, list)}
        combo_outputs = {n: t for n, t in outputs.items() if isinstance(t, list)}
        port_inputs   = {n: t for n, t in inputs.items()  if not isinstance(t, list)}
        port_outputs  = {n: t for n, t in outputs.items() if not isinstance(t, list)}

        all_combos = list(combo_inputs.items()) + list(combo_outputs.items())
        if all_combos:
            combo_section = QWidget()
            combo_section.setAttribute(Qt.WA_TranslucentBackground)
            combo_section.setStyleSheet("background: transparent;")
            cslay = QVBoxLayout()
            cslay.setContentsMargins(4, 2, 4, 4)
            cslay.setSpacing(4)
            for name, options in all_combos:
                lbl = name.replace('_', ' ').title()
                val = getattr(self.node, name, None)
                cf  = ComboField(name, lbl, options, val)
                cf.value_changed.connect(self._on_value_changed)
                cslay.addWidget(cf)
            combo_section.setLayout(cslay)
            layout.addWidget(combo_section)

            sep = QWidget()
            sep.setFixedHeight(1)
            sep.setStyleSheet(theme.SEPARATOR_STYLE)
            sep.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(sep)

        def make_port_row(port_name, port_type, direction):
            etype = port_type if port_type in ('float', 'int', 'string', 'bool', 'percent') else None

            if etype and hasattr(self.node, 'get_port_value'):
                eval_ = self.node.get_port_value(port_name)
            elif etype:
                eval_ = getattr(self.node, port_name, None)
            else:
                eval_ = None

            if port_name in ('point_codes', 'link_codes') and isinstance(eval_, list):
                eval_ = ', '.join(eval_)

            lbl = 'Slope (%)' if port_name == 'slope' else port_name.replace('_', ' ').title()

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
            for name, ptype in port_outputs.items():
                pr = make_port_row(name, ptype, 'output')
                pr.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                out_lay.addWidget(pr)
            out_lay.addStretch(1)
            out_col.setLayout(out_lay)
            col_lay.addWidget(out_col, 0)

        columns.setLayout(col_lay)
        layout.addWidget(columns)

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

    def _on_value_changed(self, port_name, value):
        node = self.node

        if port_name in ('point_codes', 'link_codes'):
            old_raw = getattr(node, port_name, [])
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
            sc.undo_stack._stack = sc.undo_stack._stack[
                :sc.undo_stack._index + 1
            ]
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

        structural_ports = (
            'geometry_type',
            'link_type',
            'target_type',
            'data_type',
        )
        if port_name in structural_ports:
            QTimer.singleShot(0, self.rebuild_ports)
            return

        if self.scene():
            self.scene().request_preview_update()

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
            sc.undo_stack._stack = sc.undo_stack._stack[
                :sc.undo_stack._index + 1
            ]
            sc.undo_stack._stack.append(cmd)
            sc.undo_stack._index = len(sc.undo_stack._stack) - 1
            sc.request_preview_update()
        else:
            self.node.name = new_name
            self._header_label.setText(f"{self.node.type}  ·  {new_name}")

        self.update_size()
        if self.scene():
            self.scene().request_preview_update()

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
