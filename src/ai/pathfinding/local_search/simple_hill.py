from __future__ import annotations

import random
from dataclasses import dataclass
from time import perf_counter
from typing import Callable


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
        if current == goal:
            break

        current_h = heuristic(current)
        best_h = current_h
        best_neighbors = []

        for neighbor in get_neighbors(current):
            generated += 1
            neighbor_h = heuristic(neighbor)

            if neighbor_h < best_h:
                best_h = neighbor_h
                best_neighbors = [neighbor]
            elif neighbor_h == best_h and neighbor_h <= current_h:
                best_neighbors.append(neighbor)

        if not best_neighbors:
            break

        current = random.choice(best_neighbors)
        path.append(current)

    return LocalPathResult(
        algorithm="SIMPLE_HILL",
        path=path,
        found=path[-1] == goal,
        expanded_nodes=expanded,
        generated_nodes=generated,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )
