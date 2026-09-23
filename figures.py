"""Immutable figure geometry, independent of Tkinter."""

from dataclasses import dataclass, replace
from math import atan2, ceil, cos, degrees, hypot, pi, radians, sin


KINDS = ('Rectangle', 'Ellipse', 'Triangle')
CORNERS = ((-1, -1), (1, -1), (1, 1), (-1, 1))


@dataclass(frozen=True)
class Figure:
    kind: str
    cx: float
    cy: float
    width: float
    height: float
    border: float = 1
    color: str = 'black'
    custom_color: bool = False
    angle: float = 0

    @classmethod
    def from_drag(cls, kind, start, end, border, color, custom_color):
        width, height = abs(end[0] - start[0]), abs(end[1] - start[1])
        if not width or not height:
            return None
        return cls(kind, (start[0] + end[0]) / 2,
                   (start[1] + end[1]) / 2, width, height,
                   border, color, custom_color)

    def world(self, x, y):
        c, s = cos(radians(self.angle)), sin(radians(self.angle))
        return self.cx + c * x - s * y, self.cy + s * x + c * y

    def local(self, x, y):
        c, s = cos(radians(self.angle)), sin(radians(self.angle))
        x, y = x - self.cx, y - self.cy
        return c * x + s * y, -s * x + c * y

    def corners(self):
        return [self.world(sx * self.width / 2, sy * self.height / 2)
                for sx, sy in CORNERS]

    def rotation_handle(self):
        return self.world(0, -self.height / 2 - self.border / 2 - 28)

    def points(self):
        if self.kind == 'Rectangle':
            points = self.corners()
        elif self.kind == 'Triangle':
            points = [self.world(0, -self.height / 2),
                      self.world(self.width / 2, self.height / 2),
                      self.world(-self.width / 2, self.height / 2)]
        elif self.kind == 'Ellipse':
            # Keep chord error small even for larger ellipses.
            count = max(48, ceil(pi * (max(self.width, self.height)) ** .5 * 2))
            points = [self.world(self.width / 2 * cos(2 * pi * i / count),
                                 self.height / 2 * sin(2 * pi * i / count))
                      for i in range(count)]
        else:
            raise ValueError(f'Unknown figure: {self.kind}')
        return points + points[:1]

    def hit(self, x, y):
        points = self.points()
        return any(segment_distance((x, y), a, b) <= self.border / 2 + 4
                   for a, b in zip(points, points[1:]))

    def resized(self, corner, point):
        x, y = self.local(*point)
        sx, sy = CORNERS[corner]
        width, height = max(1, 2 * x * sx), max(1, 2 * y * sy)
        if abs(width - self.width) < 1e-9 and abs(height - self.height) < 1e-9:
            return self
        return replace(self, width=width, height=height)

    def rotated(self, start, point):
        if hypot(point[0] - self.cx, point[1] - self.cy) < 1e-9:
            return self
        if hypot(start[0] - self.cx, start[1] - self.cy) < 1e-9:
            return self
        delta = atan2(point[1] - self.cy, point[0] - self.cx) - atan2(
            start[1] - self.cy, start[0] - self.cx)
        angle = (self.angle + degrees(delta)) % 360
        if min(abs(angle - self.angle), 360 - abs(angle - self.angle)) < 1e-9:
            return self
        return replace(self, angle=angle)


def segment_distance(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = dx * dx + dy * dy
    t = max(0, min(1, ((point[0] - a[0]) * dx +
                      (point[1] - a[1]) * dy) / length)) if length else 0
    return hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dy)
