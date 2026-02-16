"""
UI Panels for Component Designer
Contains Parameters and Toolbox panels
"""
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QComboBox, QTextEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QTabWidget,
                               QTreeWidget, QTreeWidgetItem, QApplication)
from PySide2.QtCore import Qt, Signal, QMimeData
from PySide2.QtGui import QDrag, QPainter, QPixmap, QPen, QColor

from models import ParameterType, TargetType


class DraggableTreeWidget(QTreeWidget):
    """Custom tree widget with drag support"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.drag_start_position = None
        
    def mousePressEvent(self, event):
        """Handle mouse press to start drag"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move to perform drag"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if self.drag_start_position is None:
            return
            
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
            
        item = self.itemAt(self.drag_start_position)
        if item and item.parent():  # Only drag child items
            element_type = item.text(0)
            
            # Create mime data
            mime_data = QMimeData()
            mime_data.setText(element_type)
            
            # Create drag with pixmap
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # Create a simple pixmap for drag feedback
            pixmap = QPixmap(100, 40)
            pixmap.fill(QColor(200, 220, 255, 200))
            painter = QPainter(pixmap)
            painter.setPen(QPen(Qt.black))
            painter.drawRect(0, 0, 99, 39)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, element_type)
            painter.end()
            
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())
            
            # Execute drag
            drag.exec_(Qt.CopyAction)


class ToolboxPanel(QWidget):
    """Toolbox panel with geometry elements"""
    
    element_selected = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Category tree - use custom draggable tree
        self.tree = DraggableTreeWidget()
        self.tree.setHeaderLabel("Toolbox")
        
        # Parameters category
        parameters = QTreeWidgetItem(["Parameters"])
        parameters.addChild(QTreeWidgetItem(["Input Parameter"]))
        parameters.addChild(QTreeWidgetItem(["Output Parameter"]))
        parameters.addChild(QTreeWidgetItem(["Target Parameter"]))
        self.tree.addTopLevelItem(parameters)
        
        # Geometry category
        geometry = QTreeWidgetItem(["Geometry"])
        geometry.addChild(QTreeWidgetItem(["Point"]))
        geometry.addChild(QTreeWidgetItem(["Link"]))
        geometry.addChild(QTreeWidgetItem(["Shape"]))
        self.tree.addTopLevelItem(geometry)
        
        # Auxiliary
        auxiliary = QTreeWidgetItem(["Auxiliary"])
        auxiliary.addChild(QTreeWidgetItem(["Auxiliary Point"]))
        auxiliary.addChild(QTreeWidgetItem(["Auxiliary Line"]))
        auxiliary.addChild(QTreeWidgetItem(["Auxiliary Curve"]))
        self.tree.addTopLevelItem(auxiliary)
        
        # Workflow
        workflow = QTreeWidgetItem(["Workflow"])
        workflow.addChild(QTreeWidgetItem(["Decision"]))
        workflow.addChild(QTreeWidgetItem(["Switch"]))
        workflow.addChild(QTreeWidgetItem(["Variable"]))
        self.tree.addTopLevelItem(workflow)
        
        self.tree.expandAll()
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        layout.addWidget(self.tree)
        self.setLayout(layout)
        
    def on_item_double_clicked(self, item, column):
        """Handle element double-click"""
        if item.parent():  # Is a child item
            element_type = item.text(0)
            self.element_selected.emit(element_type)