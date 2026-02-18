"""
Base Graphics View with pan and zoom functionality
"""
from PySide2.QtWidgets import QGraphicsView
from PySide2.QtCore import Qt
from PySide2.QtGui import QMouseEvent


class BaseGraphicsView(QGraphicsView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_panning    = False
        self.pan_start_pos = None
        self.selected_node = None

    def select_node_visually(self, node):
        self.selected_node = node

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.is_panning = True
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.ClosedHandCursor)
            fake_event = QMouseEvent(
                event.type(), event.localPos(),
                Qt.LeftButton, Qt.LeftButton, event.modifiers()
            )
            super().mousePressEvent(fake_event)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_panning:
            fake_event = QMouseEvent(
                event.type(), event.localPos(),
                Qt.LeftButton, Qt.LeftButton, event.modifiers()
            )
            super().mouseMoveEvent(fake_event)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self.is_panning:
            self.is_panning = False
            fake_event = QMouseEvent(
                event.type(), event.localPos(),
                Qt.LeftButton, Qt.LeftButton, event.modifiers()
            )
            super().mouseReleaseEvent(fake_event)
            self.restore_drag_mode()
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta)
        elif event.modifiers() & Qt.ShiftModifier:
            delta = event.angleDelta().y()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta)
        else:
            zoom_factor = 1.15
            scene_pos   = self.mapToScene(event.pos())

            if event.angleDelta().y() > 0:
                self.scale(zoom_factor, zoom_factor)
            else:
                self.scale(1.0 / zoom_factor, 1.0 / zoom_factor)

            new_view_pos = self.mapFromScene(scene_pos)
            delta = new_view_pos - event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta.y())
            event.accept()

    def restore_drag_mode(self):
        self.setDragMode(QGraphicsView.NoDrag)