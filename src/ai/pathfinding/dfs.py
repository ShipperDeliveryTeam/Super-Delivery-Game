from __future__ import annotations

from time import perf_counter

from src.ai.pathfinding.search_common import GridPos, NeighborFn, SearchResult, reconstruct_path


def dfs(
    start: GridPos,
    goal: GridPos,
    get_neighbors: NeighborFn,
    max_depth: int = 5000,
) -> SearchResult:
    started_at = perf_counter()

    stack: list[tuple[GridPos, int]] = [(start, 0)]
    came_from: dict[GridPos, GridPos | None] = {start: None}
    cost_so_far: dict[GridPos, float] = {start: 0.0}
    visited: set[GridPos] = set()

    expanded_nodes = 0
    generated_nodes = 1

    while stack:
        current, depth = stack.pop()

        if current in visited:
            continue

        visited.add(current)
        expanded_nodes += 1

        if current == goal:
            path = reconstruct_path(came_from, goal)
            return SearchResult(
                algorithm="DFS",
                path=path,
                cost=cost_so_far[goal],
                expanded_nodes=expanded_nodes,
                generated_nodes=generated_nodes,
                runtime_ms=(perf_counter() - started_at) * 1000,
            )

        if depth >= max_depth:
            continue

        for next_pos, step_cost in reversed(get_neighbors(current)):
            if next_pos in visited:
                continue

            if next_pos not in came_from:
                came_from[next_pos] = current
                cost_so_far[next_pos] = cost_so_far[current] + step_cost
                generated_nodes += 1

            stack.append((next_pos, depth + 1))

    return SearchResult(
        algorithm="DFS",
        path=[],
        cost=float("inf"),
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )