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


class ParametersPanel(QWidget):
    """Panel for managing Input/Output and Target parameters"""
    
    def __init__(self):
        super().__init__()
        self.input_output_params = []
        self.target_params = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Tab widget for different parameter types
        tabs = QTabWidget()
        
        # Component Settings tab
        component_tab = QWidget()
        component_layout = QFormLayout()
        self.component_name = QLineEdit()
        self.component_desc = QTextEdit()
        self.component_desc.setMaximumHeight(80)
        component_layout.addRow("Component Name:", self.component_name)
        component_layout.addRow("Description:", self.component_desc)
        component_tab.setLayout(component_layout)
        
        # Input/Output Parameters tab
        io_tab = QWidget()
        io_layout = QVBoxLayout()
        
        self.io_table = QTableWidget(0, 5)
        self.io_table.setHorizontalHeaderLabels(["Name", "Type", "Direction", "Default", "Display Name"])
        self.io_table.horizontalHeader().setStretchLastSection(True)
        
        io_buttons = QHBoxLayout()
        add_io_btn = QPushButton("Add Parameter")
        add_io_btn.clicked.connect(self.add_io_parameter)
        remove_io_btn = QPushButton("Remove Parameter")
        remove_io_btn.clicked.connect(self.remove_io_parameter)
        io_buttons.addWidget(add_io_btn)
        io_buttons.addWidget(remove_io_btn)
        io_buttons.addStretch()
        
        io_layout.addWidget(self.io_table)
        io_layout.addLayout(io_buttons)
        io_tab.setLayout(io_layout)
        
        # Target Parameters tab
        target_tab = QWidget()
        target_layout = QVBoxLayout()
        
        self.target_table = QTableWidget(0, 3)
        self.target_table.setHorizontalHeaderLabels(["Name", "Type", "Preview Value"])
        self.target_table.horizontalHeader().setStretchLastSection(True)
        
        target_buttons = QHBoxLayout()
        add_target_btn = QPushButton("Add Target")
        add_target_btn.clicked.connect(self.add_target_parameter)
        remove_target_btn = QPushButton("Remove Target")
        remove_target_btn.clicked.connect(self.remove_target_parameter)
        target_buttons.addWidget(add_target_btn)
        target_buttons.addWidget(remove_target_btn)
        target_buttons.addStretch()
        
        target_layout.addWidget(self.target_table)
        target_layout.addLayout(target_buttons)
        target_tab.setLayout(target_layout)
        
        tabs.addTab(component_tab, "Component Settings")
        tabs.addTab(io_tab, "I/O Parameters")
        tabs.addTab(target_tab, "Target Parameters")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
        
    def add_io_parameter(self):
        """Add new Input/Output parameter"""
        row = self.io_table.rowCount()
        self.io_table.insertRow(row)
        
        # Name
        name_item = QTableWidgetItem(f"Parameter{row+1}")
        self.io_table.setItem(row, 0, name_item)
        
        # Type
        type_combo = QComboBox()
        for pt in ParameterType:
            type_combo.addItem(pt.value, pt)
        self.io_table.setCellWidget(row, 1, type_combo)
        
        # Direction
        dir_combo = QComboBox()
        dir_combo.addItems(["Input", "Output", "InputOutput"])
        self.io_table.setCellWidget(row, 2, dir_combo)
        
        # Default value
        default_item = QTableWidgetItem("0.0")
        self.io_table.setItem(row, 3, default_item)
        
        # Display name
        display_item = QTableWidgetItem(f"Parameter {row+1}")
        self.io_table.setItem(row, 4, display_item)
        
    def remove_io_parameter(self):
        """Remove selected I/O parameter"""
        current_row = self.io_table.currentRow()
        if current_row >= 0:
            self.io_table.removeRow(current_row)
            
    def add_target_parameter(self):
        """Add new Target parameter"""
        row = self.target_table.rowCount()
        self.target_table.insertRow(row)
        
        # Name
        name_item = QTableWidgetItem(f"TargetParameter{row+1}")
        self.target_table.setItem(row, 0, name_item)
        
        # Type
        type_combo = QComboBox()
        for tt in TargetType:
            type_combo.addItem(tt.value, tt)
        self.target_table.setCellWidget(row, 1, type_combo)
        
        # Preview value
        preview_item = QTableWidgetItem("-1.0")
        self.target_table.setItem(row, 2, preview_item)
        
    def remove_target_parameter(self):
        """Remove selected target parameter"""
        current_row = self.target_table.currentRow()
        if current_row >= 0:
            self.target_table.removeRow(current_row)


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
        
        # Geometry category
        geometry = QTreeWidgetItem(["Geometry"])
        geometry.addChild(QTreeWidgetItem(["Point"]))
        geometry.addChild(QTreeWidgetItem(["Link"]))
        geometry.addChild(QTreeWidgetItem(["Shape"]))
        self.tree.addTopLevelItem(geometry)
        
        # Advanced Geometry
        advanced = QTreeWidgetItem(["Advanced Geometry"])
        advanced.addChild(QTreeWidgetItem(["Arc Point"]))
        advanced.addChild(QTreeWidgetItem(["Parabola Point"]))
        self.tree.addTopLevelItem(advanced)
        
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
        
        # Miscellaneous
        misc = QTreeWidgetItem(["Miscellaneous"])
        misc.addChild(QTreeWidgetItem(["Mark Point"]))
        misc.addChild(QTreeWidgetItem(["Comment"]))
        self.tree.addTopLevelItem(misc)
        
        self.tree.expandAll()
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        layout.addWidget(self.tree)
        self.setLayout(layout)
        
    def on_item_double_clicked(self, item, column):
        """Handle element double-click"""
        if item.parent():  # Is a child item
            element_type = item.text(0)
            self.element_selected.emit(element_type)