from __future__ import annotations

from heapq import heappop, heappush
from time import perf_counter

from src.ai.pathfinding.search_common import SearchResult, reconstruct_path


def astar(start, goal, get_neighbors, heuristic) -> SearchResult:
    started_at = perf_counter()

    queue = []
    order = 0
    heappush(queue, (heuristic(start, goal), order, start))

    parent = {start: None}
    cost = {start: 0}

    expanded_nodes = 0
    generated_nodes = 1

    while queue:
        _, _, current = heappop(queue)
        expanded_nodes += 1

        if current == goal:
            path = reconstruct_path(parent, goal)
            runtime = (perf_counter() - started_at) * 1000
            return SearchResult("ASTAR", path, cost[goal], expanded_nodes, generated_nodes, runtime)

        for next_pos, step_cost in get_neighbors(current):
            new_cost = cost[current] + step_cost

            if next_pos in cost and cost[next_pos] <= new_cost:
                continue

            parent[next_pos] = current
            cost[next_pos] = new_cost
            order += 1

            f_score = new_cost + heuristic(next_pos, goal)
            heappush(queue, (f_score, order, next_pos))
            generated_nodes += 1

    runtime = (perf_counter() - started_at) * 1000
    return SearchResult("ASTAR", [], float("inf"), expanded_nodes, generated_nodes, runtime)
