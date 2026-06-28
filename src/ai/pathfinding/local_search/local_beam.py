from __future__ import annotations

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


def local_beam_search(
    start: GridPos,
    goal: GridPos,
    get_neighbors: NeighborFn,
    heuristic: HeuristicFn,
    beam_width: int = 5,
    max_steps: int = 1000,
) -> LocalPathResult:
    started_at = perf_counter()
    beam = [[start]]
    expanded = 0
    generated = 0

    for _ in range(max_steps):
        candidates: list[list[GridPos]] = []

        for path in beam:
            current = path[-1]
            expanded += 1
            if current == goal:
                return LocalPathResult("LOCAL_BEAM", path, True, expanded, generated, (perf_counter() - started_at) * 1000)

            for neighbor in get_neighbors(current):
                generated += 1
                candidates.append(path + [neighbor])

        if not candidates:
            break

        candidates.sort(key=lambda item: heuristic(item[-1]))
        beam = candidates[:beam_width]

    best_path = min(beam, key=lambda item: heuristic(item[-1])) if beam else [start]
    return LocalPathResult(
        algorithm="LOCAL_BEAM",
        path=best_path,
        found=best_path[-1] == goal,
        expanded_nodes=expanded,
        generated_nodes=generated,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )
