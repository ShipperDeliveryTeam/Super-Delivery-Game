from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


GridPos = tuple[int, int]
NeighborFn = Callable[[GridPos], list[tuple[GridPos, float]]]
HeuristicFn = Callable[[GridPos, GridPos], float]


@dataclass
class SearchResult:
    algorithm: str
    path: list[GridPos]
    cost: float
    expanded_nodes: int
    generated_nodes: int
    runtime_ms: float

    @property
    def found(self) -> bool:
        return len(self.path) > 0

    @property
    def success(self) -> bool:
        return self.found


def reconstruct_path(parent, goal):
    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()
    return path


def calculate_path_cost(path, get_neighbors):
    if len(path) <= 1:
        return 0

    total = 0

    for i in range(len(path) - 1):
        current = path[i]
        next_pos = path[i + 1]

        for neighbor, step_cost in get_neighbors(current):
            if neighbor == next_pos:
                total += step_cost
                break

    return total
