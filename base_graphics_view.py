"""
Base Graphics View with common pan and zoom functionality
"""
from PySide2.QtWidgets import QGraphicsView
from PySide2.QtCore import Qt
from PySide2.QtGui import QMouseEvent


class BaseGraphicsView(QGraphicsView):
    """Base graphics view with pan and zoom capabilities"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Pan mode variables
        self.is_panning = False
        self.pan_start_pos = None
        
        # Selection tracking
        self.selected_node = None
        
    def select_node_visually(self, node):
        """Select a node visually in this view - to be overridden by subclass"""
        self.selected_node = node
        
    def mousePressEvent(self, event):
        """Handle mouse press for panning"""
        if event.button() == Qt.MiddleButton:
            # Start panning - switch to ScrollHandDrag mode
            self.is_panning = True
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.ClosedHandCursor)
            # Create a fake left button event to start the drag
            fake_event = QMouseEvent(
                event.type(),
                event.localPos(),
                Qt.LeftButton,
                Qt.LeftButton,
                event.modifiers()
            )
            super().mousePressEvent(fake_event)
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for panning"""
        if self.is_panning:
            # Pass through as left button for ScrollHandDrag
            fake_event = QMouseEvent(
                event.type(),
                event.localPos(),
                Qt.LeftButton,
                Qt.LeftButton,
                event.modifiers()
            )
            super().mouseMoveEvent(fake_event)
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release to end panning"""
        if event.button() == Qt.MiddleButton and self.is_panning:
            # End panning
            self.is_panning = False
            # Create fake left button release
            fake_event = QMouseEvent(
                event.type(),
                event.localPos(),
                Qt.LeftButton,
                Qt.LeftButton,
                event.modifiers()
            )
            super().mouseReleaseEvent(fake_event)
            # Restore original drag mode (to be set by subclass)
            self.restore_drag_mode()
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
    def wheelEvent(self, event):
        """Handle zoom with mouse wheel"""
        # Check if Shift is pressed for horizontal pan
        if event.modifiers() & Qt.ShiftModifier:
            # Horizontal pan with Shift+wheel
            delta = event.angleDelta().y()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta
            )
        # Check if Ctrl is pressed for zoom
        elif event.modifiers() & Qt.ControlModifier:
            # Zoom with Ctrl+wheel
            zoom_factor = 1.15
            if event.angleDelta().y() > 0:
                self.scale(zoom_factor, zoom_factor)
            else:
                self.scale(1/zoom_factor, 1/zoom_factor)
        else:
            # Default: vertical pan with wheel
            delta = event.angleDelta().y()
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta
            )
            
    def restore_drag_mode(self):
        """Restore drag mode after panning - to be overridden by subclass"""
        self.setDragMode(QGraphicsView.NoDrag)