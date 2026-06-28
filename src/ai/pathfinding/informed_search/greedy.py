from __future__ import annotations

from heapq import heappop, heappush
from time import perf_counter

from src.ai.pathfinding.search_common import SearchResult, reconstruct_path


def greedy_best_first_search(start, goal, get_neighbors, heuristic) -> SearchResult:
    started_at = perf_counter()

    queue = []
    order = 0
    heappush(queue, (heuristic(start, goal), order, start))

    parent = {start: None}
    cost = {start: 0}
    reached = set()

    expanded_nodes = 0
    generated_nodes = 1

    while queue:
        _, _, current = heappop(queue)

        if current in reached:
            continue

        reached.add(current)
        expanded_nodes += 1

        if current == goal:
            path = reconstruct_path(parent, goal)
            return SearchResult("GREEDY", path, cost[goal], expanded_nodes, generated_nodes, (perf_counter() - started_at) * 1000)

        for next_pos, step_cost in get_neighbors(current):
            if next_pos in reached:
                continue

            if next_pos not in parent:
                parent[next_pos] = current
                cost[next_pos] = cost[current] + step_cost
                generated_nodes += 1

            order += 1
            heappush(queue, (heuristic(next_pos, goal), order, next_pos))

    return SearchResult("GREEDY", [], float("inf"), expanded_nodes, generated_nodes, (perf_counter() - started_at) * 1000)


greedy = greedy_best_first_search
