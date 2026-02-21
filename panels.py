"""
Toolbox Panel for Component Designer
"""
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QApplication,
                               QTreeWidget, QTreeWidgetItem)
from PySide2.QtCore import Qt, Signal, QMimeData
from PySide2.QtGui import QDrag, QPainter, QPixmap, QPen, QColor

from .theme_dark import theme


class DraggableTreeWidget(QTreeWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self._drag_start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if self._drag_start_pos is None:
            return
        if ((event.pos() - self._drag_start_pos).manhattanLength()
                < QApplication.startDragDistance()):
            return

        item = self.itemAt(self._drag_start_pos)
        if item is None or item.childCount() > 0:
            return

        element_type = item.text(0)

        mime = QMimeData()
        mime.setText(element_type)

        pixmap = QPixmap(140, 36)
        pixmap.fill(QColor(38, 45, 65, 230))
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(82, 148, 226), 1))
        painter.drawRect(0, 0, 139, 35)
        painter.setPen(QColor(200, 210, 230))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, element_type)
        painter.end()

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        drag.exec_(Qt.CopyAction)


# Node types handled by the new specialised target creators
_TARGET_TYPES = ("Surface Target", "Elevation Target", "Offset Target")

# Math node labels grouped by sub-category for toolbox display
_MATH_ARITHMETIC   = ("Add", "Subtract", "Multiply", "Divide", "Modulo", "Power")
_MATH_UNARY        = ("Abs", "Negate", "Sqrt", "Ceil", "Floor", "Round")
_MATH_TRIG         = ("Sin", "Cos", "Tan", "Asin", "Acos", "Atan", "Atan2")
_MATH_LOG          = ("Ln", "Log10", "Exp")
_MATH_COMPARISON   = ("Min", "Max", "Clamp")
_MATH_UTILITY      = ("Interpolate", "Map Range")

# Logic node labels grouped by sub-category for toolbox display
_LOGIC_BOOLEAN     = ("And", "Or", "Not", "Xor", "Nand", "Nor")
_LOGIC_COMPARISON  = ("Equal", "Not Equal", "Greater", "Greater Equal",
                      "Less", "Less Equal")
_LOGIC_UTILITY     = ("If Else", "Switch", "All", "Any")


class ToolboxPanel(QWidget):

    element_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.tree = DraggableTreeWidget()
        self.tree.setHeaderLabel("Toolbox")
        self.tree.setIndentation(16)
        self.tree.setStyleSheet(theme.TOOLBOX_STYLE)
        self.setStyleSheet("background: #161820;")

        # ── Parameters ──────────────────────────────────────────────────────
        params = QTreeWidgetItem(["Parameters"])
        params.setFlags(params.flags() & ~Qt.ItemIsDragEnabled)
        for label in ("Output",):
            child = QTreeWidgetItem([label])
            child.setFlags(child.flags() | Qt.ItemIsDragEnabled)
            params.addChild(child)
        self.tree.addTopLevelItem(params)

        # ── Targets ─────────────────────────────────────────────────────────
        targets = QTreeWidgetItem(["Targets"])
        targets.setFlags(targets.flags() & ~Qt.ItemIsDragEnabled)
        for label in _TARGET_TYPES:
            child = QTreeWidgetItem([label])
            child.setFlags(child.flags() | Qt.ItemIsDragEnabled)
            targets.addChild(child)
        self.tree.addTopLevelItem(targets)

        # ── Typed Inputs ────────────────────────────────────────────────────
        typed = QTreeWidgetItem(["Typed Inputs"])
        typed.setFlags(typed.flags() & ~Qt.ItemIsDragEnabled)
        for label in (
            "Integer Input",
            "Double Input",
            "String Input",
            "Grade Input",
            "Slope Input",
            "Yes\\No Input",
            "Superelevation Input",
        ):
            child = QTreeWidgetItem([label])
            child.setFlags(child.flags() | Qt.ItemIsDragEnabled)
            typed.addChild(child)
        self.tree.addTopLevelItem(typed)

        # ── Math ─────────────────────────────────────────────────────────────
        math_root = QTreeWidgetItem(["Math"])
        math_root.setFlags(math_root.flags() & ~Qt.ItemIsDragEnabled)

        def _add_subgroup(parent, title, labels):
            grp = QTreeWidgetItem([title])
            grp.setFlags(grp.flags() & ~Qt.ItemIsDragEnabled)
            for lbl in labels:
                ch = QTreeWidgetItem([lbl])
                ch.setFlags(ch.flags() | Qt.ItemIsDragEnabled)
                grp.addChild(ch)
            parent.addChild(grp)

        _add_subgroup(math_root, "Arithmetic",   _MATH_ARITHMETIC)
        _add_subgroup(math_root, "Unary",        _MATH_UNARY)
        _add_subgroup(math_root, "Trigonometry", _MATH_TRIG)
        _add_subgroup(math_root, "Logarithm",    _MATH_LOG)
        _add_subgroup(math_root, "Comparison",   _MATH_COMPARISON)
        _add_subgroup(math_root, "Utility",      _MATH_UTILITY)

        self.tree.addTopLevelItem(math_root)

        # ── Logic ────────────────────────────────────────────────────────────
        logic_root = QTreeWidgetItem(["Logic"])
        logic_root.setFlags(logic_root.flags() & ~Qt.ItemIsDragEnabled)

        _add_subgroup(logic_root, "Boolean",    _LOGIC_BOOLEAN)
        _add_subgroup(logic_root, "Comparison", _LOGIC_COMPARISON)
        _add_subgroup(logic_root, "Utility",    _LOGIC_UTILITY)

        self.tree.addTopLevelItem(logic_root)

        # ── Geometry ────────────────────────────────────────────────────────
        geometry = QTreeWidgetItem(["Geometry"])
        geometry.setFlags(geometry.flags() & ~Qt.ItemIsDragEnabled)
        for label in ("Point", "Link", "Shape"):
            child = QTreeWidgetItem([label])
            child.setFlags(child.flags() | Qt.ItemIsDragEnabled)
            geometry.addChild(child)
        self.tree.addTopLevelItem(geometry)

        # ── Auxiliary ───────────────────────────────────────────────────────
        auxiliary = QTreeWidgetItem(["Auxiliary"])
        auxiliary.setFlags(auxiliary.flags() & ~Qt.ItemIsDragEnabled)
        for label in ("Auxiliary Point", "Auxiliary Line", "Auxiliary Curve"):
            child = QTreeWidgetItem([label])
            child.setFlags(child.flags() | Qt.ItemIsDragEnabled)
            auxiliary.addChild(child)
        self.tree.addTopLevelItem(auxiliary)

        # ── Workflow ────────────────────────────────────────────────────────
        workflow = QTreeWidgetItem(["Workflow"])
        workflow.setFlags(workflow.flags() & ~Qt.ItemIsDragEnabled)
        for label in ("Decision", "Switch", "Variable"):
            child = QTreeWidgetItem([label])
            child.setFlags(child.flags() | Qt.ItemIsDragEnabled)
            workflow.addChild(child)
        self.tree.addTopLevelItem(workflow)

        self.tree.expandAll()
        self.tree.itemDoubleClicked.connect(self._on_double_click)

        layout.addWidget(self.tree)
        self.setLayout(layout)

    def _on_double_click(self, item, _column):
        if item.childCount() == 0:
            self.element_selected.emit(item.text(0))
