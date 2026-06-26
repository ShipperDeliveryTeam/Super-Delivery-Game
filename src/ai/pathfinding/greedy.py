from __future__ import annotations

from heapq import heappop, heappush
from itertools import count
from time import perf_counter

from src.ai.pathfinding.search_common import (
    GridPos,
    HeuristicFn,
    NeighborFn,
    SearchResult,
    reconstruct_path,
)


def greedy_best_first_search(
    start: GridPos,
    goal: GridPos,
    get_neighbors: NeighborFn,
    heuristic: HeuristicFn,
) -> SearchResult:
    started_at = perf_counter()

    tie_breaker = count()
    frontier: list[tuple[float, int, GridPos]] = []
    heappush(frontier, (heuristic(start, goal), next(tie_breaker), start))

    came_from: dict[GridPos, GridPos | None] = {start: None}
    cost_so_far: dict[GridPos, float] = {start: 0.0}
    visited: set[GridPos] = set()

    expanded_nodes = 0
    generated_nodes = 1

    while frontier:
        _, _, current = heappop(frontier)

        if current in visited:
            continue

        visited.add(current)
        expanded_nodes += 1

        if current == goal:
            path = reconstruct_path(came_from, goal)
            return SearchResult(
                algorithm="GREEDY",
                path=path,
                cost=cost_so_far[goal],
                expanded_nodes=expanded_nodes,
                generated_nodes=generated_nodes,
                runtime_ms=(perf_counter() - started_at) * 1000,
            )

        for next_pos, step_cost in get_neighbors(current):
            if next_pos in visited:
                continue

            if next_pos not in came_from:
                came_from[next_pos] = current
                cost_so_far[next_pos] = cost_so_far[current] + step_cost
                generated_nodes += 1

            heappush(
                frontier,
                (heuristic(next_pos, goal), next(tie_breaker), next_pos),
            )

    return SearchResult(
        algorithm="GREEDY",
        path=[],
        cost=float("inf"),
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )


# Alias ngắn để planner/test gọi dễ hơn.
greedy = greedy_best_first_search