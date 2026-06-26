from __future__ import annotations

from collections import deque
from time import perf_counter

from src.ai.pathfinding.search_common import GridPos, NeighborFn, SearchResult, reconstruct_path


def bfs(
    start: GridPos,
    goal: GridPos,
    get_neighbors: NeighborFn,
) -> SearchResult:
    started_at = perf_counter()

    frontier: deque[GridPos] = deque([start])
    came_from: dict[GridPos, GridPos | None] = {start: None}
    cost_so_far: dict[GridPos, float] = {start: 0.0}

    expanded_nodes = 0
    generated_nodes = 1

    while frontier:
        current = frontier.popleft()
        expanded_nodes += 1

        if current == goal:
            path = reconstruct_path(came_from, goal)
            return SearchResult(
                algorithm="BFS",
                path=path,
                cost=cost_so_far[goal],
                expanded_nodes=expanded_nodes,
                generated_nodes=generated_nodes,
                runtime_ms=(perf_counter() - started_at) * 1000,
            )

        for next_pos, step_cost in get_neighbors(current):
            if next_pos in came_from:
                continue

            came_from[next_pos] = current
            cost_so_far[next_pos] = cost_so_far[current] + step_cost
            frontier.append(next_pos)
            generated_nodes += 1

    return SearchResult(
        algorithm="BFS",
        path=[],
        cost=float("inf"),
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )