"""
Node Widgets for Flowchart
Contains port widgets and node item classes
"""

from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLabel, QLineEdit, QDoubleSpinBox, QComboBox,
                               QGraphicsProxyWidget, QGraphicsRectItem, QStyle)
from PySide2.QtCore import Qt, Signal, QPointF
from PySide2.QtGui import QPainter, QBrush, QColor, QPen, QFont


class PortWidget(QWidget):
    """Connection port widget for nodes"""
    
    port_clicked = Signal(object, str)  # (node, port_type)
    
    PORT_COLORS = {
        'from': QColor(100, 200, 100),    # Green for output
        'to': QColor(255, 150, 50),       # Orange for input
        'start': QColor(255, 150, 50),    # Orange for input (link start)
        'end': QColor(255, 150, 50),      # Orange for input (link end)
    }
    
    PORT_LABELS = {
        'from': 'OUT',
        'to': 'IN',
        'start': 'START',
        'end': 'END'
    }
    
    def __init__(self, node, port_type, port_direction, parent=None):
        super().__init__(parent)
        self.node = node
        self.port_type = port_type  # 'from', 'to', 'start', 'end'
        self.port_direction = port_direction  # 'input' or 'output'
        self.is_hovered = False
        self.setFixedHeight(24)
        self.setMinimumWidth(50)
        self.setCursor(Qt.PointingHandCursor)
        
    def paintEvent(self, event):
        """Draw the port as a button with label"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Port color based on type
        color = self.PORT_COLORS.get(self.port_type, QColor(150, 150, 150))
        
        # Lighten color on hover
        if self.is_hovered:
            color = color.lighter(120)
        
        # Draw button background
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 4, 4)
        
        # Draw label
        painter.setPen(QPen(Qt.white))
        font = QFont()
        font.setBold(True)
        font.setPointSize(7)
        painter.setFont(font)
        
        label = self.PORT_LABELS.get(self.port_type, self.port_type.upper())
        painter.drawText(self.rect(), Qt.AlignCenter, label)
    
    def enterEvent(self, event):
        """Handle mouse enter"""
        self.is_hovered = True
        self.update()
        
    def leaveEvent(self, event):
        """Handle mouse leave"""
        self.is_hovered = False
        self.update()
    
    def mousePressEvent(self, event):
        """Handle port click"""
        if event.button() == Qt.LeftButton:
            self.port_clicked.emit(self.node, self.port_type)
            event.accept()


class FlowchartNodeItem(QGraphicsRectItem):
    """Draggable flowchart node item with inline editing - Dynamo style"""

    def __init__(self, node, x, y, parent=None):
        # Start with a default size, will be updated
        super().__init__(0, 0, 200, 100, parent)
        self.node = node
        self.setPos(x, y)
        self.setFlags(QGraphicsRectItem.ItemIsMovable | 
                     QGraphicsRectItem.ItemIsSelectable |
                     QGraphicsRectItem.ItemSendsGeometryChanges)
        
        # Visual styling
        self.normal_pen = QPen(QColor(60, 60, 60), 2)
        self.selected_pen = QPen(QColor(255, 120, 0), 3)
        self.header_brush = QBrush(QColor(70, 130, 180))
        self.body_brush = QBrush(QColor(245, 245, 250))
        self.selected_header_brush = QBrush(QColor(255, 140, 0))

        self.header_height = 35
        
        # Port widgets - dynamic based on node type
        self.ports = {}  # Dictionary: port_type -> PortWidget
        
        # Create container widget with layout
        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header
        self.create_header(main_layout)
        
        # Create body
        self.create_body(main_layout)
        
        self.container_widget.setLayout(main_layout)
        
        # Create proxy widget to embed in graphics scene
        self.proxy = QGraphicsProxyWidget(self)
        self.proxy.setWidget(self.container_widget)
        self.proxy.setPos(0, 0)
        
        # Update node size based on container
        self.update_size()
        
        # Store node reference
        self.setData(0, node)
    
    def create_header(self, main_layout):
        """Create header widget"""
        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(self.header_height)
        self.header_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(10, 8, 10, 8)
        
        # Create header with editable name
        self.header_label = QLabel(f"{self.node.type}: {self.node.name}")
        self.header_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 9pt;
                background-color: transparent;
            }
        """)
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.mouseDoubleClickEvent = self.edit_name
        self.header_label.setCursor(Qt.PointingHandCursor)
        
        # Line edit for name (hidden by default)
        self.name_edit = QLineEdit(self.node.name)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                color: white;
                font-weight: bold;
                font-size: 9pt;
                background-color: rgba(255, 255, 255, 30);
                border: 1px solid white;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        self.name_edit.setAlignment(Qt.AlignCenter)
        self.name_edit.hide()
        self.name_edit.returnPressed.connect(self.finish_name_edit)
        self.name_edit.editingFinished.connect(self.finish_name_edit)
        
        header_layout.addWidget(self.header_label)
        header_layout.addWidget(self.name_edit)
        self.header_widget.setLayout(header_layout)
        
        main_layout.addWidget(self.header_widget)
    
    def create_body(self, main_layout):
        """Create body widget with ports and properties"""
        self.body_widget = QWidget()
        self.body_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            QLabel {
                color: #282828;
                font-size: 8pt;
                background-color: transparent;
            }
        """)
        
        body_layout = QVBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        
        # Add ports if node has any
        input_ports = self.node.get_input_ports()
        output_ports = self.node.get_output_ports()
        
        if input_ports or output_ports:
            self.create_ports(body_layout)
        
        # Form layout for properties
        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(10, 8, 10, 8)
        self.form_layout.setSpacing(6)
        self.form_layout.setHorizontalSpacing(8)
        
        # Add properties to form
        self.property_widgets = []
        self.create_property_widgets()
        
        form_container = QWidget()
        form_container.setLayout(self.form_layout)
        body_layout.addWidget(form_container)
        
        self.body_widget.setLayout(body_layout)
        main_layout.addWidget(self.body_widget)
    
    def create_ports(self, body_layout):
        """Create port widgets based on node's input and output ports"""
        ports_widget = QWidget()
        ports_layout = QHBoxLayout()
        ports_layout.setContentsMargins(10, 8, 10, 8)
        ports_layout.setSpacing(8)
        
        # Get input and output ports separately
        input_ports = self.node.get_input_ports()
        output_ports = self.node.get_output_ports()
        
        # Add input ports on the left
        if input_ports:
            input_container = QWidget()
            input_layout = QVBoxLayout()
            input_layout.setContentsMargins(0, 0, 0, 0)
            input_layout.setSpacing(4)
            
            for port_type in input_ports:
                port = PortWidget(self.node, port_type, 'input')
                port.port_clicked.connect(self.on_port_clicked)
                self.ports[port_type] = port
                input_layout.addWidget(port)
            
            input_container.setLayout(input_layout)
            ports_layout.addWidget(input_container)
        
        # Add spacer in the middle
        ports_layout.addStretch()
        
        # Add output ports on the right
        if output_ports:
            output_container = QWidget()
            output_layout = QVBoxLayout()
            output_layout.setContentsMargins(0, 0, 0, 0)
            output_layout.setSpacing(4)
            
            for port_type in output_ports:
                port = PortWidget(self.node, port_type, 'output')
                port.port_clicked.connect(self.on_port_clicked)
                self.ports[port_type] = port
                output_layout.addWidget(port)
            
            output_container.setLayout(output_layout)
            ports_layout.addWidget(output_container)
        
        ports_widget.setLayout(ports_layout)
        body_layout.addWidget(ports_widget)
    
    def on_port_clicked(self, node, port_type):
        """Handle port click - start or finish connection"""
        if self.scene():
            self.scene().handle_port_click(self, port_type)
    
    def get_port_scene_pos(self, port_type):
        """Get port position in scene coordinates (center of port button)"""
        if port_type in self.ports:
            port = self.ports[port_type]
            # Get center point of the port widget
            port_rect = port.rect()
            port_center = QPointF(port_rect.center())
            # Map to container widget
            widget_pos = port.mapTo(self.container_widget, port_center.toPoint())
            # Map to scene
            proxy_pos = self.proxy.mapToScene(widget_pos)
            return proxy_pos
        return self.scenePos()
    
    def edit_name(self, event):
        """Start editing node name"""
        self.header_label.hide()
        self.name_edit.setText(self.node.name)
        self.name_edit.show()
        self.name_edit.setFocus()
        self.name_edit.selectAll()
    
    def finish_name_edit(self):
        """Finish editing node name"""
        new_name = self.name_edit.text().strip()
        if new_name:
            self.node.name = new_name
            self.header_label.setText(f"{self.node.type}: {self.node.name}")
            self.update_size()
            
            # Trigger preview update
            if self.scene():
                self.scene().request_preview_update()
        
        self.name_edit.hide()
        self.header_label.show()
    
    def rebuild_properties(self):
        """Rebuild property widgets (used when geometry type changes)"""
        # Clear existing widgets
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.property_widgets.clear()
        
        # Recreate widgets
        self.create_property_widgets()
        
        # Update size
        self.update_size()
    
    def create_property_widgets(self):
        """Create property widgets using form layout"""
        properties = self.node.get_inline_properties()
        
        for prop_info in properties:
            prop_name = prop_info['name']
            prop_label = prop_info['label']
            prop_type = prop_info['type']
            prop_value = prop_info['value']
            
            # Skip name property (it's in header)
            if prop_name == 'name':
                continue
            
            # Create label
            label = QLabel(prop_label + ":")
            
            # Create widget based on type
            widget = None
            
            if prop_type == 'float':
                widget = self.create_float_widget(prop_name, prop_value)
            elif prop_type == 'string':
                widget = self.create_string_widget(prop_name, prop_value)
            elif prop_type == 'combo':
                widget = self.create_combo_widget(prop_name, prop_value, prop_info)
            
            if widget:
                self.form_layout.addRow(label, widget)
                self.property_widgets.append({
                    'name': prop_name,
                    'widget': widget,
                    'label': label
                })
    
    def create_float_widget(self, prop_name, prop_value):
        """Create float spinbox widget"""
        widget = QDoubleSpinBox()
        widget.setRange(-10000, 10000)
        widget.setDecimals(3)
        widget.setValue(prop_value)
        widget.setMinimumWidth(80)
        widget.setStyleSheet("""
            QDoubleSpinBox {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 3px;
                font-size: 8pt;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #4682B4;
            }
        """)
        widget.valueChanged.connect(lambda v, p=prop_name: self.on_property_changed(p, v))
        return widget
    
    def create_string_widget(self, prop_name, prop_value):
        """Create string line edit widget"""
        widget = QLineEdit()
        widget.setText(str(prop_value))
        widget.setMinimumWidth(80)
        widget.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 3px;
                font-size: 8pt;
            }
            QLineEdit:focus {
                border: 2px solid #4682B4;
            }
        """)
        widget.textChanged.connect(lambda v, p=prop_name: self.on_property_changed(p, v))
        return widget
    
    def create_combo_widget(self, prop_name, prop_value, prop_info):
        """Create combobox widget"""
        widget = QComboBox()
        for option in prop_info['options']:
            widget.addItem(option['label'], option['value'])
        # Set current value
        index = widget.findData(prop_value)
        if index >= 0:
            widget.setCurrentIndex(index)
        widget.setMinimumWidth(80)
        widget.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 3px;
                font-size: 8pt;
            }
            QComboBox:focus {
                border: 2px solid #4682B4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #666;
                margin-right: 5px;
            }
        """)
        # Special handling for geometry_type combo
        if prop_name == 'geometry_type':
            widget.currentIndexChanged.connect(lambda idx, p=prop_name, w=widget: self.on_geometry_type_changed(p, w.currentData()))
        else:
            widget.currentIndexChanged.connect(lambda idx, p=prop_name, w=widget: self.on_property_changed(p, w.currentData()))
        return widget
    
    def on_geometry_type_changed(self, prop_name, value):
        """Handle geometry type change - rebuild properties"""
        # Update node property
        if hasattr(self.node, prop_name):
            setattr(self.node, prop_name, value)
        
        # Rebuild properties to show relevant fields
        self.rebuild_properties()
        
        # Trigger preview update
        if self.scene():
            self.scene().request_preview_update()
    
    def update_size(self):
        """Update node size based on container widget"""
        # Let the container calculate its size
        self.container_widget.adjustSize()
        
        # Get the size hint from container
        size = self.container_widget.sizeHint()
        width = max(200, size.width() + 20)  # Add some padding
        height = size.height()
        
        # Update rectangle
        self.setRect(0, 0, width, height)
        
        # Update proxy size
        self.proxy.setMaximumSize(width, height)
    
    def on_property_changed(self, prop_name, value):
        """Handle property value change"""
        # Update node property
        if hasattr(self.node, prop_name):
            setattr(self.node, prop_name, value)
        
        # Trigger preview update
        if self.scene():
            self.scene().request_preview_update()
        
    def itemChange(self, change, value):
        """Handle item changes - update node position and arrows"""
        if change == QGraphicsRectItem.ItemPositionChange:
            # Update node position
            new_pos = value
            self.node.x = new_pos.x()
            self.node.y = new_pos.y()
            
            # Update connected wires
            if self.scene():
                self.scene().update_port_wires(self)
                # Trigger preview update
                self.scene().request_preview_update()
        
        elif change == QGraphicsRectItem.ItemPositionHasChanged:
            # Force scene update to clear artifacts
            if self.scene():
                self.scene().update()
                
        elif change == QGraphicsRectItem.ItemSelectedChange:
            # Update visual style based on selection
            self.update()
                
        return super().itemChange(change, value)
    
    def paint(self, painter, option, widget=None):
        """Custom paint to show Dynamo-style node"""
        # Remove the selection rectangle that Qt draws by default
        option.state &= ~QStyle.State_Selected
        
        # Enable antialiasing
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw shadow for depth
        if not self.isSelected():
            shadow_rect = self.rect().adjusted(3, 3, 3, 3)
            painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(shadow_rect, 5, 5)
        
        # Draw header with rounded top corners
        if self.isSelected():
            painter.setBrush(self.selected_header_brush)
            painter.setPen(self.selected_pen)
        else:
            painter.setBrush(self.header_brush)
            painter.setPen(self.normal_pen)
        
        # Header rectangle
        from PySide2.QtCore import QRectF
        header_rect = QRectF(0, 0, self.rect().width(), self.header_height)
        painter.drawRoundedRect(header_rect, 5, 5)
        
        # Draw body with rounded bottom corners
        painter.setBrush(self.body_brush)
        if self.isSelected():
            painter.setPen(self.selected_pen)
        else:
            painter.setPen(self.normal_pen)
        
        body_rect = QRectF(0, self.header_height, 
                          self.rect().width(), 
                          self.rect().height() - self.header_height)
        painter.drawRoundedRect(body_rect, 5, 5)
        
        # Cover the top corners of body to connect with header
        painter.setPen(Qt.NoPen)
        cover_rect = QRectF(0, self.header_height - 5, 
                           self.rect().width(), 10)
        painter.drawRect(cover_rect)
        
        # Redraw edges for clean connection
        if self.isSelected():
            painter.setPen(self.selected_pen)
        else:
            painter.setPen(self.normal_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(int(self.rect().left()), self.header_height,
                        int(self.rect().right()), self.header_height)
        
        # Draw selection highlight if selected
        if self.isSelected():
            # Draw a glow effect
            glow_pen = QPen(QColor(255, 120, 0, 80), 8)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(-4, -4, 4, 4), 8, 8)

    def mousePressEvent(self, event):
        """Handle mouse press - select node"""
        super().mousePressEvent(event)
        if self.scene():
            self.scene().node_selected.emit(self.node)
            
    def mouseDoubleClickEvent(self, event):
        """Handle double click - edit name"""
        self.edit_name(event)

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            # Delete this node
            if self.scene():
                if self.scene().delete_selected_node():
                    event.accept()
                    return
        
        super().keyPressEvent(event)