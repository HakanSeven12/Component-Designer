"""
Geometry nodes: PointNode, LinkNode, ShapeNode.

All data flows via wires — there are no hard-coded node-ID references.

PointNode
---------
  Inputs:
    reference   : None  — carries a (x, y) world-coord tuple from another
                          PointNode's 'position' output port.
    geometry_type, angle, delta_x, delta_y, distance, slope, point_codes,
    add_link  — as before.
  Outputs:
    position : None  — (x, y) world-coord tuple, consumed by other nodes.
    x, y     : float — individual components (read-only display).

LinkNode
--------
  Inputs:
    start : None — (x, y) tuple from a PointNode 'position' output.
    end   : None — (x, y) tuple from a PointNode 'position' output.
    link_codes : string
  Outputs:
    length : float
    slope  : float

The 'None' port type means "carries any Python object"; the wire still
renders and connects normally.
"""

import math

from PySide2.QtCore import QPointF
from PySide2.QtGui import QColor

from .base import FlowchartNode, PointGeometryType, LinkType, _enum_options, port


class PointNode(FlowchartNode):
    """
    Geometric point whose world position is derived from an optional
    upstream reference position plus geometry parameters.
    """

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Point", name)
        self.geometry_type = PointGeometryType.DELTA_XY

        # Geometry parameters (editable via inline editors or wires)
        self.angle    = 0.0
        self.delta_x  = 0.0
        self.delta_y  = 0.0
        self.distance = 0.0
        self.slope    = 0.0

        # Received from upstream wire (reference port)
        self._ref_pos: tuple = (0.0, 0.0)

        self.point_codes = []
        self.add_link    = False

        # Computed outputs — updated by _compute()
        self._pos_x = 0.0
        self._pos_y = 0.0

    # ------------------------------------------------------------------
    # Port declarations
    # ------------------------------------------------------------------

    def get_input_ports(self) -> dict:
        ports = {
            'reference':     None,                         # receives (x,y) tuple
            'geometry_type': _enum_options(PointGeometryType),
            'add_link':      port('bool', editor=False),
        }
        gt = self.geometry_type
        if gt == PointGeometryType.ANGLE_DELTA_X:
            ports['angle']   = port('float', editor=False)
            ports['delta_x'] = port('float', editor=False)
        elif gt == PointGeometryType.ANGLE_DELTA_Y:
            ports['angle']   = port('float', editor=False)
            ports['delta_y'] = port('float', editor=False)
        elif gt == PointGeometryType.ANGLE_DISTANCE:
            ports['angle']    = port('float', editor=False)
            ports['distance'] = port('float', editor=False)
        elif gt == PointGeometryType.DELTA_XY:
            ports['delta_x'] = port('float', editor=False)
            ports['delta_y'] = port('float', editor=False)
        elif gt == PointGeometryType.DELTA_X_SURFACE:
            ports['delta_x'] = port('float', editor=False)
        elif gt == PointGeometryType.SLOPE_DELTA_X:
            ports['slope']   = port('float', editor=False)
            ports['delta_x'] = port('float', editor=False)
        elif gt == PointGeometryType.SLOPE_DELTA_Y:
            ports['slope']   = port('float', editor=False)
            ports['delta_y'] = port('float', editor=False)
        elif gt == PointGeometryType.SLOPE_TO_SURFACE:
            ports['slope'] = port('float', editor=False)
        ports['point_codes'] = port('string', editor=False)
        return ports

    def get_output_ports(self) -> dict:
        return {
            'position': None,                    # (x, y) tuple — wire carries it
            'x':        port('float', editor=False),
            'y':        port('float', editor=False),
        }

    # ------------------------------------------------------------------
    # Value accessors
    # ------------------------------------------------------------------

    def set_port_value(self, port_name, value):
        if port_name == 'reference':
            # Upstream PointNode pushes its (x, y) position here
            if isinstance(value, (tuple, list)) and len(value) >= 2:
                self._ref_pos = (float(value[0]), float(value[1]))
            else:
                self._ref_pos = (0.0, 0.0)
            self._compute()
        elif port_name == 'geometry_type':
            self.geometry_type = value
            self._compute()
        elif port_name in ('angle', 'delta_x', 'delta_y',
                           'distance', 'slope'):
            try:
                setattr(self, port_name, float(value) if value is not None else 0.0)
            except (TypeError, ValueError):
                pass
            self._compute()
        elif port_name == 'point_codes':
            if isinstance(value, str):
                self.point_codes = [c.strip() for c in value.split(',') if c.strip()]
            elif isinstance(value, list):
                self.point_codes = value
        elif port_name == 'add_link':
            self.add_link = bool(value)
        elif hasattr(self, port_name):
            setattr(self, port_name, value)

    def get_port_value(self, port_name):
        if port_name == 'position':
            self._compute()
            return (self._pos_x, self._pos_y)
        if port_name == 'x':
            self._compute()
            return self._pos_x
        if port_name == 'y':
            self._compute()
            return self._pos_y
        return getattr(self, port_name, None)

    # ------------------------------------------------------------------
    # Geometry computation
    # ------------------------------------------------------------------

    def _compute(self):
        """Recompute (x, y) from the current reference position and params."""
        bx, by = self._ref_pos
        gt = self.geometry_type

        if gt == PointGeometryType.ANGLE_DELTA_X:
            rad = math.radians(self.angle)
            self._pos_x = bx + self.delta_x * math.cos(rad)
            self._pos_y = by + self.delta_x * math.sin(rad)
        elif gt == PointGeometryType.ANGLE_DELTA_Y:
            rad = math.radians(self.angle)
            self._pos_x = bx - self.delta_y * math.sin(rad)
            self._pos_y = by + self.delta_y * math.cos(rad)
        elif gt == PointGeometryType.ANGLE_DISTANCE:
            rad = math.radians(self.angle)
            self._pos_x = bx + self.distance * math.cos(rad)
            self._pos_y = by + self.distance * math.sin(rad)
        elif gt == PointGeometryType.DELTA_XY:
            self._pos_x = bx + self.delta_x
            self._pos_y = by + self.delta_y
        elif gt == PointGeometryType.DELTA_X_SURFACE:
            self._pos_x = bx + self.delta_x
            self._pos_y = by
        elif gt == PointGeometryType.INTERPOLATE:
            self._pos_x = bx
            self._pos_y = by
        elif gt == PointGeometryType.SLOPE_DELTA_X:
            slope_ratio = self.slope / 100.0
            self._pos_x = bx + self.delta_x
            self._pos_y = by + self.delta_x * slope_ratio
        elif gt == PointGeometryType.SLOPE_DELTA_Y:
            slope_ratio = self.slope / 100.0
            dx = self.delta_y / slope_ratio if slope_ratio != 0 else 0.0
            self._pos_x = bx + dx
            self._pos_y = by + self.delta_y
        elif gt == PointGeometryType.SLOPE_TO_SURFACE:
            self._pos_x = bx
            self._pos_y = by
        else:
            self._pos_x = bx
            self._pos_y = by

    # Convenience for preview renderer (backwards compat)
    @property
    def computed_x(self):
        self._compute()
        return self._pos_x

    @property
    def computed_y(self):
        self._compute()
        return self._pos_y

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        from ..preview import (PreviewPointItem, PreviewTextItem,
                               PreviewLinkLine,
                               BASE_FONT_NODE_LABEL, BASE_FONT_CODE_LABEL)

        # Resolve reference position from the shared registry
        # (populated by the topological render pass in preview.py)
        ref_id = getattr(self, '_wire_ref_id', None)
        if ref_id and ref_id in point_positions:
            self._ref_pos = point_positions[ref_id]
        self._compute()

        pos = (self._pos_x, self._pos_y)
        point_positions[self.id] = pos

        x =  pos[0] * scale_factor
        y = -pos[1] * scale_factor
        anchor = QPointF(x, y)

        items = [PreviewPointItem(x, y, self)]

        if self.add_link and ref_id and ref_id in point_positions:
            ref = point_positions[ref_id]
            fx =  ref[0] * scale_factor
            fy = -ref[1] * scale_factor
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

    # ------------------------------------------------------------------
    # Serialisation  (store params only, not computed state)
    # ------------------------------------------------------------------

    def to_dict(self):
        d = super().to_dict()
        d.update({
            'geometry_type': self.geometry_type.value,
            'angle':         self.angle,
            'delta_x':       self.delta_x,
            'delta_y':       self.delta_y,
            'distance':      self.distance,
            'slope':         self.slope,
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
        node.point_codes = data.get('point_codes', [])
        node.add_link    = data.get('add_link', False)
        # Legacy support: old files stored from_point as a node-id reference.
        # We keep it only for the preview renderer's topology sort.
        node._legacy_from_point = data.get('from_point')
        return node


class LinkNode(FlowchartNode):
    """
    Geometric link (line/arc) between two points.

    Inputs:
        start : None — receives (x, y) tuple from a PointNode 'position' output
        end   : None — receives (x, y) tuple from a PointNode 'position' output
        link_codes : string

    Outputs:
        length : float — Euclidean distance between start and end
        slope  : float — rise/run as a percentage (Δy/Δx × 100)
    """

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Link", name)
        self.link_type  = LinkType.LINE
        self.link_codes = []

        # Positions received from upstream wires
        self._start_pos: tuple = (0.0, 0.0)
        self._end_pos:   tuple = (0.0, 0.0)
        self._has_start  = False
        self._has_end    = False

        # Computed outputs
        self._length = 0.0
        self._slope  = 0.0

    # ------------------------------------------------------------------
    # Port declarations
    # ------------------------------------------------------------------

    def get_input_ports(self) -> dict:
        return {
            'start':      None,                    # (x, y) from PointNode
            'end':        None,                    # (x, y) from PointNode
            'link_codes': port('string', editor=False),
        }

    def get_output_ports(self) -> dict:
        return {
            'length': port('float', editor=False),
            'slope':  port('float', editor=False),
        }

    # ------------------------------------------------------------------
    # Value accessors
    # ------------------------------------------------------------------

    def set_port_value(self, port_name, value):
        if port_name == 'start':
            if isinstance(value, (tuple, list)) and len(value) >= 2:
                self._start_pos = (float(value[0]), float(value[1]))
                self._has_start = True
            self._compute()
        elif port_name == 'end':
            if isinstance(value, (tuple, list)) and len(value) >= 2:
                self._end_pos = (float(value[0]), float(value[1]))
                self._has_end = True
            self._compute()
        elif port_name == 'link_codes':
            if isinstance(value, str):
                self.link_codes = [c.strip() for c in value.split(',') if c.strip()]
            elif isinstance(value, list):
                self.link_codes = value
        elif hasattr(self, port_name):
            setattr(self, port_name, value)

    def get_port_value(self, port_name):
        if port_name == 'length':
            self._compute()
            return self._length
        if port_name == 'slope':
            self._compute()
            return self._slope
        return getattr(self, port_name, None)

    # ------------------------------------------------------------------
    # Geometry computation
    # ------------------------------------------------------------------

    def _compute(self):
        if self._has_start and self._has_end:
            dx = self._end_pos[0] - self._start_pos[0]
            dy = self._end_pos[1] - self._start_pos[1]
            self._length = math.hypot(dx, dy)
            self._slope  = (dy / dx * 100.0) if dx != 0 else 0.0
        else:
            self._length = 0.0
            self._slope  = 0.0

    # Backwards-compat properties used by old preview/resolve code
    @property
    def computed_length(self):
        self._compute()
        return self._length

    @property
    def computed_slope(self):
        self._compute()
        return self._slope

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def create_preview_items(self, scene, scale_factor, show_codes, point_positions):
        from ..preview import (PreviewLineItem, PreviewTextItem,
                               BASE_FONT_NODE_LABEL, BASE_FONT_CODE_LABEL)

        # Resolve start/end from the shared point_positions registry
        # populated by the topological render pass in preview.py.
        start_id = getattr(self, '_wire_start_id', None)
        end_id   = getattr(self, '_wire_end_id',   None)

        sp = point_positions.get(start_id) if start_id else None
        ep = point_positions.get(end_id)   if end_id   else None

        # Also accept positions delivered by wire resolver
        if sp is None and self._has_start:
            sp = self._start_pos
        if ep is None and self._has_end:
            ep = self._end_pos

        if sp:
            self._start_pos = sp
            self._has_start = True
        if ep:
            self._end_pos = ep
            self._has_end = True

        self._compute()

        items = []
        if sp and ep:
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

            info = PreviewTextItem(
                f"L={self._length:.3f}  S={self._slope:.2f}%",
                self,
                anchor_scene=anchor,
                offset_screen=QPointF(0, -16),
                base_font_size=BASE_FONT_CODE_LABEL,
            )
            info.setDefaultTextColor(QColor(60, 140, 60))
            items.append(info)

            if show_codes and self.link_codes:
                ct = PreviewTextItem(f"[{','.join(self.link_codes)}]", self,
                                     anchor_scene=anchor,
                                     offset_screen=QPointF(0, -4),
                                     base_font_size=BASE_FONT_CODE_LABEL)
                ct.setDefaultTextColor(QColor(0, 150, 0))
                items.append(ct)
        return items

    def get_preview_display_color(self):
        return QColor(0, 150, 0)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self):
        d = super().to_dict()
        d.update({'link_codes': self.link_codes})
        return d

    @classmethod
    def from_dict(cls, data):
        node = cls(data['id'], data['name'])
        node.x          = data.get('x', 0)
        node.y          = data.get('y', 0)
        node.link_codes = data.get('link_codes', [])
        # Legacy: old files stored start_point/end_point as node IDs.
        node._legacy_start_point = data.get('start_point')
        node._legacy_end_point   = data.get('end_point')
        return node


class ShapeNode(FlowchartNode):
    """Represents a filled shape defined by a set of links."""

    def __init__(self, node_id, name=""):
        super().__init__(node_id, "Shape", name)
        self.shape_codes = []
        self.links       = []
        self.material    = "Asphalt"

    def get_input_ports(self) -> dict:
        return {'material': port('string', editor=True)}

    def get_output_ports(self) -> dict:
        return {}

    def get_port_value(self, port_name):
        return getattr(self, port_name, None)

    def set_port_value(self, port_name, value):
        if hasattr(self, port_name):
            setattr(self, port_name, value)

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
