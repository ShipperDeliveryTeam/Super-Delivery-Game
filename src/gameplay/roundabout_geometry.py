from __future__ import annotations

import math
from typing import Iterable, Sequence, Tuple


GridPoint = Tuple[float, float]
GridPos = Tuple[int, int]


def edge_key(a: GridPos, b: GridPos) -> tuple[GridPos, GridPos]:
    return (a, b) if a <= b else (b, a)


def build_roundabout_curve(
    start: GridPos,
    end: GridPos,
    center: GridPoint | None,
    ring: Sequence[GridPos],
    connections: Iterable[tuple[GridPos, GridPos]],
) -> dict[str, object] | None:
    if center is None or len(ring) < 2:
        return None

    ring_index = {pos: index for index, pos in enumerate(ring)}
    start_index = ring_index.get(start)
    end_index = ring_index.get(end)

    if start_index is not None and end_index is not None:
        size = len(ring)

        if (start_index - end_index) % size != 1 and (end_index - start_index) % size != 1:
            return None

        cx, cy = center
        start_angle = math.atan2(start[1] - cy, start[0] - cx)
        end_angle = math.atan2(end[1] - cy, end[0] - cx)
        angle_delta = (end_angle - start_angle + math.pi) % (2.0 * math.pi) - math.pi

        return {
            "kind": "arc",
            "center": center,
            "start_angle": start_angle,
            "angle_delta": angle_delta,
            "start_radius": math.hypot(start[0] - cx, start[1] - cy),
            "end_radius": math.hypot(end[0] - cx, end[1] - cy),
        }

    connection_edges = {edge_key(a, b) for a, b in connections}

    if edge_key(start, end) not in connection_edges:
        return None

    ring_pos = start if start_index is not None else end
    ring_pos_index = ring_index.get(ring_pos)

    if ring_pos_index is None:
        return None

    # Cardinal gates must stay centered in their lane until they reach the
    # ring. Applying the ring tangent inside a one-cell gate makes horizontal
    # gates dip vertically and vertical gates sway sideways.
    if start[1] == end[1] or start[0] == end[0]:
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        p0 = (float(start[0]), float(start[1]))
        p3 = (float(end[0]), float(end[1]))
        return {
            "kind": "bezier",
            "p0": p0,
            "p1": (p0[0] + dx / 3.0, p0[1] + dy / 3.0),
            "p2": (p0[0] + 2.0 * dx / 3.0, p0[1] + 2.0 * dy / 3.0),
            "p3": p3,
        }

    # The ring tuple is clockwise on screen. Traffic uses the previous node,
    # which gives the natural counter-clockwise roundabout direction.
    successor = ring[(ring_pos_index - 1) % len(ring)]
    ring_tangent = _normalized(
        successor[0] - ring_pos[0],
        successor[1] - ring_pos[1],
    )
    road_tangent = _normalized(end[0] - start[0], end[1] - start[1])
    distance = max(0.01, math.hypot(end[0] - start[0], end[1] - start[1]))
    handle = min(0.72, distance * 0.62)
    p0 = (float(start[0]), float(start[1]))
    p3 = (float(end[0]), float(end[1]))

    if start_index is None:
        start_tangent = road_tangent
        end_tangent = ring_tangent
    else:
        start_tangent = ring_tangent
        end_tangent = road_tangent

    p1 = (p0[0] + start_tangent[0] * handle, p0[1] + start_tangent[1] * handle)
    p2 = (p3[0] - end_tangent[0] * handle, p3[1] - end_tangent[1] * handle)

    return {
        "kind": "bezier",
        "p0": p0,
        "p1": p1,
        "p2": p2,
        "p3": p3,
    }


def curve_point(curve: dict[str, object], t: float) -> GridPoint:
    t = max(0.0, min(1.0, float(t)))

    if curve["kind"] == "arc":
        cx, cy = curve["center"]
        angle = curve["start_angle"] + curve["angle_delta"] * t
        radius = curve["start_radius"] + (curve["end_radius"] - curve["start_radius"]) * t
        return cx + math.cos(angle) * radius, cy + math.sin(angle) * radius

    p0 = curve["p0"]
    p1 = curve["p1"]
    p2 = curve["p2"]
    p3 = curve["p3"]
    inv = 1.0 - t
    return (
        inv**3 * p0[0] + 3.0 * inv**2 * t * p1[0] + 3.0 * inv * t**2 * p2[0] + t**3 * p3[0],
        inv**3 * p0[1] + 3.0 * inv**2 * t * p1[1] + 3.0 * inv * t**2 * p2[1] + t**3 * p3[1],
    )


def curve_length(curve: dict[str, object], samples: int = 16) -> float:
    previous = curve_point(curve, 0.0)
    total = 0.0

    for index in range(1, max(2, samples) + 1):
        current = curve_point(curve, index / max(2, samples))
        total += math.hypot(current[0] - previous[0], current[1] - previous[1])
        previous = current

    return total


def _normalized(dx: float, dy: float) -> GridPoint:
    length = math.hypot(dx, dy)

    if length <= 0.0001:
        return 0.0, 0.0

    return dx / length, dy / length
