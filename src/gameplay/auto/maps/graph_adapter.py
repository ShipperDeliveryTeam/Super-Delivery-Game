from __future__ import annotations

from math import sqrt

from src.gameplay.auto.maps.registry import get_auto_map_profile
from src.gameplay.auto.maps.tmx_loader import AutoMapData, GridPos


MAP3_ROUNDABOUT_RINGS = (
    ((12, 3), (13, 3), (13, 4), (13, 5), (12, 5), (11, 5), (11, 4), (11, 3)),
    ((26, 3), (27, 3), (27, 4), (27, 5), (26, 5), (25, 5), (25, 4), (25, 3)),
    ((12, 24), (13, 24), (13, 25), (13, 26), (12, 26), (11, 26), (11, 25), (11, 24)),
)


class AutoMapGraph:
    def __init__(self, map_data: AutoMapData) -> None:
        self.map_data = map_data
        self.profile = get_auto_map_profile(map_data.map_id)

    def get_neighbors(self, pos: GridPos) -> list[tuple[GridPos, float]]:
        x, y = pos

        directions: list[tuple[int, int, float]] = [
            (0, -1, 1.0),
            (0, 1, 1.0),
            (-1, 0, 1.0),
            (1, 0, 1.0),
        ]

        if self.profile.allow_diagonal:
            directions.extend(
                [
                    (-1, -1, sqrt(2)),
                    (1, -1, sqrt(2)),
                    (-1, 1, sqrt(2)),
                    (1, 1, sqrt(2)),
                ]
            )

        neighbors: list[tuple[GridPos, float]] = []

        for dx, dy, move_cost in directions:
            next_pos = x + dx, y + dy

            if not self.map_data.is_walkable(next_pos):
                continue

            if not self._can_move_roundabout(pos, next_pos):
                continue

            total_cost = self.map_data.movement_cost(next_pos) * move_cost
            neighbors.append((next_pos, total_cost))

        return neighbors

    def _can_move_roundabout(self, current: GridPos, next_pos: GridPos) -> bool:
        if self.map_data.map_id != 3:
            return True

        for ring in MAP3_ROUNDABOUT_RINGS:
            if current not in ring or next_pos not in ring:
                continue

            size = len(ring)
            current_index = ring.index(current)
            next_index = ring.index(next_pos)

            # Ring được khai báo theo chiều kim đồng hồ trên màn hình.
            # Đi ngược chiều kim đồng hồ nghĩa là đi về node trước đó.
            return (current_index - next_index) % size == 1

        return True

    def heuristic(self, start: GridPos, goal: GridPos) -> float:
        x1, y1 = start
        x2, y2 = goal

        return abs(x1 - x2) + abs(y1 - y2)

    def path_cost(self, path: list[GridPos]) -> float:
        if len(path) <= 1:
            return 0.0

        total = 0.0

        for pos in path[1:]:
            total += self.map_data.movement_cost(pos)

        return total