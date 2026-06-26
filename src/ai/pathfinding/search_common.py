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
        return bool(self.path)


def reconstruct_path(
    came_from: dict[GridPos, GridPos | None],
    goal: GridPos,
) -> list[GridPos]:
    path: list[GridPos] = []
    current: GridPos | None = goal

    while current is not None:
        path.append(current)
        current = came_from[current]

    path.reverse()
    return path


def calculate_path_cost(
    path: list[GridPos],
    get_neighbors: NeighborFn,
) -> float:
    if len(path) <= 1:
        return 0.0

    total_cost = 0.0

    for current, next_pos in zip(path, path[1:]):
        found_edge = False

        for neighbor, step_cost in get_neighbors(current):
            if neighbor == next_pos:
                total_cost += step_cost
                found_edge = True
                break

        if not found_edge:
            return float("inf")

    return total_cost