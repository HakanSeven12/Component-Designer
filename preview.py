"""
Preview Module for Component Designer
Handles geometry preview with Layout and Roadway modes
"""
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem
from PySide2.QtCore import Qt, QPointF
from PySide2.QtGui import QPainter, QBrush, QColor, QPen, QPolygonF

from models import PointNode, LinkNode, ShapeNode
from base_graphics_view import BaseGraphicsView


class GeometryPreview(BaseGraphicsView):  # Changed from QGraphicsView
    """Preview panel showing the component geometry"""
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        
        self.scale_factor = 20  # pixels per meter
        self.show_codes = True
        self.show_comments = False
        self.preview_mode = "Layout"  # Layout or Roadway
        
        self.points = []
        self.links = []
        self.shapes = []
        
        self.setup_scene()
        
    def restore_drag_mode(self):
        """Restore drag mode after panning"""
        self.setDragMode(QGraphicsView.NoDrag)
        
    def setup_scene(self):
        """Initialize preview scene"""
        self.scene.setSceneRect(-300, -300, 600, 600)
        self.draw_grid()
        self.draw_axes()
        
    def draw_grid(self):
        """Draw background grid"""
        pen = QPen(QColor(220, 220, 220), 0.5)
        pen.setStyle(Qt.DotLine)
        
        for x in range(-300, 301, 20):
            self.scene.addLine(x, -300, x, 300, pen)
        for y in range(-300, 301, 20):
            self.scene.addLine(-300, y, 300, y, pen)
            
    def draw_axes(self):
        """Draw coordinate axes"""
        axis_pen = QPen(QColor(150, 150, 150), 2)
        self.scene.addLine(-300, 0, 300, 0, axis_pen)
        self.scene.addLine(0, -300, 0, 300, axis_pen)
        
        # Add labels
        origin_text = self.scene.addText("0,0")
        origin_text.setPos(5, 5)
        origin_text.setDefaultTextColor(QColor(100, 100, 100))
        
    def update_preview(self, flowchart_nodes):
        """Update preview based on flowchart"""
        # Clear existing geometry (keep grid and axes)
        for item in list(self.scene.items()):
            if isinstance(item, (QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem)):
                if item.data(0) is not None:  # Has node data
                    self.scene.removeItem(item)
            elif hasattr(item, 'toPlainText'):  # Text items with node data
                if item.data(0) is not None:
                    self.scene.removeItem(item)
        
        self.points.clear()
        self.links.clear()
        
        # Process flowchart nodes
        point_positions = {}
        
        for node_id, node in flowchart_nodes.items():
            if isinstance(node, PointNode):
                # Compute point position
                from_pos = None
                if node.from_point and node.from_point in point_positions:
                    from_pos = point_positions[node.from_point]
                    
                pos = node.compute_position(from_pos)
                point_positions[node.id] = pos
                
                # Draw point
                x = pos[0] * self.scale_factor
                y = -pos[1] * self.scale_factor  # Invert Y for screen coordinates
                
                circle = self.scene.addEllipse(x-4, y-4, 8, 8,
                                              QPen(Qt.black, 1),
                                              QBrush(QColor(0, 120, 255)))
                circle.setData(0, node)
                
                # Add point codes if enabled
                if self.show_codes and node.point_codes:
                    code_text = self.scene.addText(f"[{','.join(node.point_codes)}]")
                    code_text.setPos(x + 8, y - 20)
                    code_text.setDefaultTextColor(QColor(0, 0, 255))
                    code_text.setData(0, node)
                    
            elif isinstance(node, LinkNode):
                # Draw link between points
                if node.start_point and node.end_point:
                    if node.start_point in point_positions and node.end_point in point_positions:
                        start_pos = point_positions[node.start_point]
                        end_pos = point_positions[node.end_point]
                        
                        x1 = start_pos[0] * self.scale_factor
                        y1 = -start_pos[1] * self.scale_factor
                        x2 = end_pos[0] * self.scale_factor
                        y2 = -end_pos[1] * self.scale_factor
                        
                        line = self.scene.addLine(x1, y1, x2, y2,
                                                 QPen(QColor(0, 150, 0), 2))
                        line.setData(0, node)
                        
                        # Add link codes if enabled
                        if self.show_codes and node.link_codes:
                            mid_x = (x1 + x2) / 2
                            mid_y = (y1 + y2) / 2
                            code_text = self.scene.addText(f"[{','.join(node.link_codes)}]")
                            code_text.setPos(mid_x, mid_y - 15)
                            code_text.setDefaultTextColor(QColor(0, 150, 0))
                            code_text.setData(0, node)
                            
            elif isinstance(node, ShapeNode):
                # Draw shape (closed polygon)
                if len(node.links) >= 3:
                    polygon_points = []
                    for link_id in node.links:
                        if link_id in flowchart_nodes:
                            link = flowchart_nodes[link_id]
                            if link.start_point in point_positions:
                                pos = point_positions[link.start_point]
                                x = pos[0] * self.scale_factor
                                y = -pos[1] * self.scale_factor
                                polygon_points.append(QPointF(x, y))
                    
                    if len(polygon_points) >= 3:
                        polygon = QPolygonF(polygon_points)
                        shape_item = self.scene.addPolygon(
                            polygon,
                            QPen(QColor(100, 100, 100), 1),
                            QBrush(QColor(200, 200, 150, 128))
                        )
                        shape_item.setData(0, node)
                        
                        # Add shape codes
                        if self.show_codes and node.shape_codes:
                            center = polygon.boundingRect().center()
                            code_text = self.scene.addText(f"[{','.join(node.shape_codes)}]")
                            code_text.setPos(center.x() - 30, center.y() - 10)
                            code_text.setDefaultTextColor(QColor(100, 100, 0))
                            code_text.setData(0, node)