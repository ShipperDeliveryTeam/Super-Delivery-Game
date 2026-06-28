from __future__ import annotations

from heapq import heappop, heappush
from time import perf_counter

from src.ai.pathfinding.search_common import SearchResult, reconstruct_path


def ucs(start, goal, get_neighbors) -> SearchResult:
    started_at = perf_counter()

    queue = []
    order = 0
    heappush(queue, (0, order, start))

    parent = {start: None}
    cost = {start: 0}

    expanded_nodes = 0
    generated_nodes = 1

    while queue:
        current_cost, _, current = heappop(queue)

        if current_cost != cost[current]:
            continue

        expanded_nodes += 1

        if current == goal:
            path = reconstruct_path(parent, goal)
            return SearchResult("UCS", path, cost[goal], expanded_nodes, generated_nodes, (perf_counter() - started_at) * 1000)

        for next_pos, step_cost in get_neighbors(current):
            new_cost = cost[current] + step_cost

            if next_pos in cost and cost[next_pos] <= new_cost:
                continue

            parent[next_pos] = current
            cost[next_pos] = new_cost
            order += 1
            heappush(queue, (new_cost, order, next_pos))
            generated_nodes += 1

    return SearchResult("UCS", [], float("inf"), expanded_nodes, generated_nodes, (perf_counter() - started_at) * 1000)
