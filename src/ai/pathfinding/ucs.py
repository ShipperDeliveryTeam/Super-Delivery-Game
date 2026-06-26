from __future__ import annotations

from heapq import heappop, heappush
from itertools import count
from time import perf_counter

from src.ai.pathfinding.search_common import GridPos, NeighborFn, SearchResult, reconstruct_path


def ucs(
    start: GridPos,
    goal: GridPos,
    get_neighbors: NeighborFn,
) -> SearchResult:
    started_at = perf_counter()

    tie_breaker = count()
    frontier: list[tuple[float, int, GridPos]] = []
    heappush(frontier, (0.0, next(tie_breaker), start))

    came_from: dict[GridPos, GridPos | None] = {start: None}
    cost_so_far: dict[GridPos, float] = {start: 0.0}

    expanded_nodes = 0
    generated_nodes = 1

    while frontier:
        current_cost, _, current = heappop(frontier)

        if current_cost > cost_so_far.get(current, float("inf")):
            continue

        expanded_nodes += 1

        if current == goal:
            path = reconstruct_path(came_from, goal)
            return SearchResult(
                algorithm="UCS",
                path=path,
                cost=cost_so_far[goal],
                expanded_nodes=expanded_nodes,
                generated_nodes=generated_nodes,
                runtime_ms=(perf_counter() - started_at) * 1000,
            )

        for next_pos, step_cost in get_neighbors(current):
            new_cost = current_cost + step_cost

            if new_cost >= cost_so_far.get(next_pos, float("inf")):
                continue

            cost_so_far[next_pos] = new_cost
            came_from[next_pos] = current
            heappush(frontier, (new_cost, next(tie_breaker), next_pos))
            generated_nodes += 1

    return SearchResult(
        algorithm="UCS",
        path=[],
        cost=float("inf"),
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )