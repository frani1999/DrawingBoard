"""Geometry for cutting pencil segments along a continuous rubber drag."""

from math import hypot, sqrt


def remaining_segments(line, start, end, radius):
    """Return pieces of a line outside the capsule swept by a round rubber.

    Intersect with the two endpoint circles and the rectangle between them.
    This handles fast drags without leaving gaps between mouse events.
    """
    x, y, x2, y2 = line
    dx, dy = x2 - x, y2 - y
    intervals = []
    length_squared = dx * dx + dy * dy
    for cx, cy in (start, end):
        ox, oy = x - cx, y - cy
        if length_squared == 0:
            if ox * ox + oy * oy <= radius * radius:
                intervals.append((0, 1))
            continue
        b = 2 * (ox * dx + oy * dy)
        c = ox * ox + oy * oy - radius * radius
        discriminant = b * b - 4 * length_squared * c
        if discriminant >= 0:
            root = sqrt(discriminant)
            intervals.append(((-b - root) / (2 * length_squared),
                              (-b + root) / (2 * length_squared)))

    vx, vy = end[0] - start[0], end[1] - start[1]
    length = hypot(vx, vy)
    if length:
        ux, uy = vx / length, vy / length
        ox, oy = x - start[0], y - start[1]
        low, high = 0, 1
        for position, delta, minimum, maximum in (
                (ox * ux + oy * uy, dx * ux + dy * uy, 0, length),
                (-ox * uy + oy * ux, -dx * uy + dy * ux, -radius, radius)):
            if abs(delta) < 1e-12:
                if not minimum <= position <= maximum:
                    high = -1
                    break
            else:
                a, b = sorted(((minimum - position) / delta,
                               (maximum - position) / delta))
                low, high = max(low, a), min(high, b)
        if low <= high:
            intervals.append((low, high))

    clipped = sorted((max(0, a), min(1, b)) for a, b in intervals
                     if max(0, a) < min(1, b))
    if not clipped:
        return [tuple(line)]
    pieces = []
    current = 0
    for a, b in clipped:
        if a > current:
            pieces.append((x + current * dx, y + current * dy,
                           x + a * dx, y + a * dy))
        current = max(current, b)
    if current < 1:
        pieces.append((x + current * dx, y + current * dy, x2, y2))
    return pieces
