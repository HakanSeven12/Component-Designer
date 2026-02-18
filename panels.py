"""
Toolbox Panel for Component Designer
"""
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QApplication,
                               QTreeWidget, QTreeWidgetItem)
from PySide2.QtCore import Qt, Signal, QMimeData
from PySide2.QtGui import QDrag, QPainter, QPixmap, QPen, QColor


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
        pixmap.fill(QColor(200, 220, 255, 220))
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(80, 80, 160), 1))
        painter.drawRect(0, 0, 139, 35)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, element_type)
        painter.end()

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        drag.exec_(Qt.CopyAction)


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

        params = QTreeWidgetItem(["Parameters"])
        params.setFlags(params.flags() & ~Qt.ItemIsDragEnabled)
        for label in ("Output", "Target"):
            child = QTreeWidgetItem([label])
            child.setFlags(child.flags() | Qt.ItemIsDragEnabled)
            params.addChild(child)
        self.tree.addTopLevelItem(params)

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

        geometry = QTreeWidgetItem(["Geometry"])
        geometry.setFlags(geometry.flags() & ~Qt.ItemIsDragEnabled)
        for label in ("Point", "Link", "Shape"):
            child = QTreeWidgetItem([label])
            child.setFlags(child.flags() | Qt.ItemIsDragEnabled)
            geometry.addChild(child)
        self.tree.addTopLevelItem(geometry)

        auxiliary = QTreeWidgetItem(["Auxiliary"])
        auxiliary.setFlags(auxiliary.flags() & ~Qt.ItemIsDragEnabled)
        for label in ("Auxiliary Point", "Auxiliary Line", "Auxiliary Curve"):
            child = QTreeWidgetItem([label])
            child.setFlags(child.flags() | Qt.ItemIsDragEnabled)
            auxiliary.addChild(child)
        self.tree.addTopLevelItem(auxiliary)

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