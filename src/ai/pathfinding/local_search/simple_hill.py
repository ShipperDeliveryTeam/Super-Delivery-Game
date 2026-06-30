from __future__ import annotations

"""Simple Hill Climbing.

Moi buoc chi chon ngau nhien 1 node con de thu.
Neu node con tot hon node hien tai thi di tiep.
Neu khong tot hon thi dung tai local optimum.
"""

import random
from dataclasses import dataclass
from time import perf_counter
from typing import Callable

from src.ai.pathfinding.search_common import is_goal


GridPos = tuple[int, int]
NeighborFn = Callable[[GridPos], list[GridPos]]
HeuristicFn = Callable[[GridPos], float]


@dataclass
class LocalPathResult:
    algorithm: str
    path: list[GridPos]
    found: bool
    expanded_nodes: int
    generated_nodes: int
    runtime_ms: float


def simple_hill(
    start: GridPos,
    goal: GridPos,
    get_neighbors: NeighborFn,
    heuristic: HeuristicFn,
    max_steps: int = 1000,
) -> LocalPathResult:
    started_at = perf_counter()
    current = start
    path = [start]
    expanded = 0
    generated = 0

    for _ in range(max_steps):
        expanded += 1

        if is_goal(current, goal):
            break

        neighbors = get_neighbors(current)

        if not neighbors:
            break

        current_h = heuristic(current)
        neighbor = random.choice(neighbors)
        generated += 1
        neighbor_h = heuristic(neighbor)

        # Simple hill chi thu mot node con ngau nhien.
        # Neu node do khong tot hon thi dung.
        if neighbor_h >= current_h:
            break

        current = neighbor
        path.append(current)

    return LocalPathResult(
        algorithm="SIMPLE_HILL",
        path=path,
        found=is_goal(path[-1], goal),
        expanded_nodes=expanded,
        generated_nodes=generated,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )
