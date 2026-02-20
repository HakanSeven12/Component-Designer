"""
Geometry nodes: PointNode, LinkNode, ShapeNode.
"""

import math

from PySide2.QtCore import QPointF
from PySide2.QtGui import QColor

from .base import FlowchartNode, PointGeometryType, LinkType, _enum_options


class PointNode(FlowchartNode):
    """Represents a geometric point computed from a reference point."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Point", name)
        self.geometry_type = PointGeometryType.DELTA_XY
        self.angle         = 0.0
        self.delta_x       = 0.0
        self.delta_y       = 0.0
        self.distance      = 0.0
        self.slope         = 0.0
        self.from_point    = None
        self.point_codes   = []
        self.add_link      = False
        self.computed_x    = 0.0
        self.computed_y    = 0.0

    def get_input_ports(self) -> dict:
        ports = {
            'reference':     None,
            'geometry_type': _enum_options(PointGeometryType),
            'add_link':      'bool',
        }
        gt = self.geometry_type
        if gt == PointGeometryType.ANGLE_DELTA_X:
            ports['angle']   = 'float'
            ports['delta_x'] = 'float'
        elif gt == PointGeometryType.ANGLE_DELTA_Y:
            ports['angle']   = 'float'
            ports['delta_y'] = 'float'
        elif gt == PointGeometryType.ANGLE_DISTANCE:
            ports['angle']    = 'float'
            ports['distance'] = 'float'
        elif gt == PointGeometryType.DELTA_XY:
            ports['delta_x'] = 'float'
            ports['delta_y'] = 'float'
        elif gt == PointGeometryType.DELTA_X_SURFACE:
            ports['delta_x'] = 'float'
        elif gt == PointGeometryType.SLOPE_DELTA_X:
            ports['slope']   = 'float'
            ports['delta_x'] = 'float'
        elif gt == PointGeometryType.SLOPE_DELTA_Y:
            ports['slope']   = 'float'
            ports['delta_y'] = 'float'
        elif gt == PointGeometryType.SLOPE_TO_SURFACE:
            ports['slope'] = 'float'
        ports['point_codes'] = 'string'
        return ports

    def get_output_ports(self) -> dict:
        return {'vector': None, 'x': None, 'y': None}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    def compute_position(self, from_point_pos=None):
        """Compute the (x, y) position relative to from_point_pos."""
        gt   = self.geometry_type
        base = from_point_pos or (0.0, 0.0)

        if gt == PointGeometryType.ANGLE_DELTA_X:
            rad = math.radians(self.angle)
            self.computed_x = base[0] + self.delta_x * math.cos(rad)
            self.computed_y = base[1] + self.delta_x * math.sin(rad)
        elif gt == PointGeometryType.ANGLE_DELTA_Y:
            rad = math.radians(self.angle)
            self.computed_x = base[0] - self.delta_y * math.sin(rad)
            self.computed_y = base[1] + self.delta_y * math.cos(rad)
        elif gt == PointGeometryType.ANGLE_DISTANCE:
            rad = math.radians(self.angle)
            self.computed_x = base[0] + self.distance * math.cos(rad)
            self.computed_y = base[1] + self.distance * math.sin(rad)
        elif gt == PointGeometryType.DELTA_XY:
            self.computed_x = base[0] + self.delta_x
            self.computed_y = base[1] + self.delta_y
        elif gt == PointGeometryType.DELTA_X_SURFACE:
            self.computed_x = base[0] + self.delta_x
            self.computed_y = base[1]
        elif gt == PointGeometryType.INTERPOLATE:
            self.computed_x = base[0]
            self.computed_y = base[1]
        elif gt == PointGeometryType.SLOPE_DELTA_X:
            slope_ratio = self.slope / 100.0
            self.computed_x = base[0] + self.delta_x
            self.computed_y = base[1] + self.delta_x * slope_ratio
        elif gt == PointGeometryType.SLOPE_DELTA_Y:
            slope_ratio = self.slope / 100.0
            dx = self.delta_y / slope_ratio if slope_ratio != 0 else 0.0
            self.computed_x = base[0] + dx
            self.computed_y = base[1] + self.delta_y
        elif gt == PointGeometryType.SLOPE_TO_SURFACE:
            self.computed_x = base[0]
            self.computed_y = base[1]
        return (self.computed_x, self.computed_y)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        from ..preview import (PreviewPointItem, PreviewTextItem,
                               BASE_FONT_NODE_LABEL, BASE_FONT_CODE_LABEL)

        from_pos = point_positions.get(self.from_point) if self.from_point else None
        pos = self.compute_position(from_pos)
        point_positions[self.id] = pos

        x =  pos[0] * scale_factor
        y = -pos[1] * scale_factor
        anchor = QPointF(x, y)

        items = [PreviewPointItem(x, y, self)]

        if self.add_link and self.from_point and from_pos is not None:
            from ..preview import PreviewLinkLine
            fx =  from_pos[0] * scale_factor
            fy = -from_pos[1] * scale_factor
            items.append(PreviewLinkLine(fx, fy, x, y, self))

        lbl = PreviewTextItem(self.name, self,
                              anchor_scene=anchor,
                              offset_screen=QPointF(8, -25),
                              base_font_size=BASE_FONT_NODE_LABEL)
        f = lbl.font(); f.setBold(True); lbl.setFont(f)
        lbl.setDefaultTextColor(QColor(0, 0, 180))
        items.append(lbl)

        if show_codes and self.point_codes:
            ct = PreviewTextItem(f"[{','.join(self.point_codes)}]", self,
                                 anchor_scene=anchor,
                                 offset_screen=QPointF(8, -10),
                                 base_font_size=BASE_FONT_CODE_LABEL)
            ct.setDefaultTextColor(QColor(0, 0, 255))
            items.append(ct)

        return items

    def get_preview_display_color(self):
        return QColor(0, 120, 255)

    def to_dict(self):
        d = super().to_dict()
        d.update({
            'geometry_type': self.geometry_type.value,
            'angle':         self.angle,
            'delta_x':       self.delta_x,
            'delta_y':       self.delta_y,
            'distance':      self.distance,
            'slope':         self.slope,
            'from_point':    self.from_point,
            'point_codes':   self.point_codes,
            'add_link':      self.add_link,
        })
        return d

    @classmethod
    def from_dict(cls, data):
        node = cls(data['id'], data['name'])
        node.x = data.get('x', 0)
        node.y = data.get('y', 0)
        gt_str = data.get('geometry_type', 'Delta X and Delta Y')
        node.geometry_type = next(
            (gt for gt in PointGeometryType if gt.value == gt_str),
            PointGeometryType.DELTA_XY)
        node.angle       = data.get('angle',    0.0)
        node.delta_x     = data.get('delta_x',  0.0)
        node.delta_y     = data.get('delta_y',  0.0)
        node.distance    = data.get('distance', 0.0)
        node.slope       = data.get('slope',    0.0)
        node.from_point  = data.get('from_point')
        node.point_codes = data.get('point_codes', [])
        node.add_link    = data.get('add_link', True)
        return node


class LinkNode(FlowchartNode):
    """Represents a geometric link (line/arc) between two points."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Link", name)
        self.link_type       = LinkType.LINE
        self.start_point     = None
        self.end_point       = None
        self.link_codes      = []
        self.computed_length = 0.0
        self.computed_slope  = 0.0

    def get_input_ports(self) -> dict:
        return {'start': None, 'end': None, 'link_codes': 'string'}

    def get_output_ports(self) -> dict:
        return {'length': None, 'slope': None}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

    def compute_geometry(self, start_pos=None, end_pos=None):
        """Compute length and slope from start/end positions."""
        if start_pos and end_pos:
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            self.computed_length = (dx**2 + dy**2) ** 0.5
            self.computed_slope  = (dy / dx * 100.0) if dx != 0 else 0.0
        else:
            self.computed_length = 0.0
            self.computed_slope  = 0.0

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        from ..preview import (PreviewLineItem, PreviewTextItem,
                               BASE_FONT_NODE_LABEL, BASE_FONT_CODE_LABEL)
        items = []
        if self.start_point and self.end_point:
            sp = point_positions.get(self.start_point)
            ep = point_positions.get(self.end_point)
            if sp and ep:
                self.compute_geometry(sp, ep)
                x1, y1 = sp[0] * scale_factor, -sp[1] * scale_factor
                x2, y2 = ep[0] * scale_factor, -ep[1] * scale_factor
                items.append(PreviewLineItem(x1, y1, x2, y2, self))
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                anchor = QPointF(mx, my)
                t = PreviewTextItem(self.name, self,
                                    anchor_scene=anchor,
                                    offset_screen=QPointF(0, -30),
                                    base_font_size=BASE_FONT_NODE_LABEL)
                f = t.font(); f.setBold(True); t.setFont(f)
                t.setDefaultTextColor(QColor(0, 100, 0))
                items.append(t)
                if show_codes and self.link_codes:
                    ct = PreviewTextItem(f"[{','.join(self.link_codes)}]", self,
                                        anchor_scene=anchor,
                                        offset_screen=QPointF(0, -15),
                                        base_font_size=BASE_FONT_CODE_LABEL)
                    ct.setDefaultTextColor(QColor(0, 150, 0))
                    items.append(ct)
        return items

    def get_preview_display_color(self):
        return QColor(0, 150, 0)

    def to_dict(self):
        d = super().to_dict()
        d.update({'start_point': self.start_point,
                  'end_point':   self.end_point,
                  'link_codes':  self.link_codes})
        return d

    @classmethod
    def from_dict(cls, data):
        node = cls(data['id'], data['name'])
        node.x           = data.get('x', 0)
        node.y           = data.get('y', 0)
        node.start_point = data.get('start_point')
        node.end_point   = data.get('end_point')
        node.link_codes  = data.get('link_codes', [])
        return node


class ShapeNode(FlowchartNode):
    """Represents a filled shape defined by a set of links."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Shape", name)
        self.shape_codes = []
        self.links       = []
        self.material    = "Asphalt"

    def get_input_ports(self) -> dict:
        return {'material': 'string'}

    def get_output_ports(self) -> dict:
        return {}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        return []

    def get_preview_display_color(self):
        return QColor(200, 200, 150)

    def to_dict(self):
        d = super().to_dict()
        d.update({'shape_codes': self.shape_codes,
                  'links':       self.links,
                  'material':    self.material})
        return d

    @classmethod
    def from_dict(cls, data):
        node = cls(data['id'], data['name'])
        node.x           = data.get('x', 0)
        node.y           = data.get('y', 0)
        node.shape_codes = data.get('shape_codes', [])
        node.links       = data.get('links', [])
        node.material    = data.get('material', 'Asphalt')
        return node
