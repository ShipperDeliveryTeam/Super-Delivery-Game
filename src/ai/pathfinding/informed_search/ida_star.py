from __future__ import annotations

from time import perf_counter

from src.ai.pathfinding.search_common import SearchResult, calculate_path_cost


FOUND = "FOUND"


def ida_star(start, goal, get_neighbors, heuristic, max_iterations=300, max_expanded_nodes=300000) -> SearchResult:
    started_at = perf_counter()

    limit = heuristic(start, goal)
    path = [start]
    expanded_nodes = 0
    generated_nodes = 1

    def search(g, limit):
        nonlocal expanded_nodes, generated_nodes

        current = path[-1]
        f = g + heuristic(current, goal)

        if f > limit:
            return f

        if current == goal:
            return FOUND

        if expanded_nodes >= max_expanded_nodes:
            return float("inf")

        expanded_nodes += 1
        min_limit = float("inf")

        neighbors = get_neighbors(current)
        neighbors.sort(key=lambda item: item[1] + heuristic(item[0], goal))

        for next_pos, step_cost in neighbors:
            if next_pos in path:
                continue

            path.append(next_pos)
            generated_nodes += 1

            result = search(g + step_cost, limit)
            if result == FOUND:
                return FOUND

            if result < min_limit:
                min_limit = result

            path.pop()

        return min_limit

    for _ in range(max_iterations):
        result = search(0, limit)

        if result == FOUND:
            final_path = list(path)
            cost = calculate_path_cost(final_path, get_neighbors)
            return SearchResult("IDA_STAR", final_path, cost, expanded_nodes, generated_nodes, (perf_counter() - started_at) * 1000)

        if result == float("inf"):
            break

        limit = result

    return SearchResult("IDA_STAR", [], float("inf"), expanded_nodes, generated_nodes, (perf_counter() - started_at) * 1000)
