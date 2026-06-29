from __future__ import annotations

from time import perf_counter

from src.ai.pathfinding.search_common import SearchResult, calculate_path_cost


FOUND = "FOUND"


def ida_star(
    start,
    goal,
    get_neighbors,
    heuristic,
    max_iterations=300,
    max_expanded_nodes=300000,
) -> SearchResult:
    started_at = perf_counter()

    limit = heuristic(start, goal)
    path = [start]
    expanded_nodes = 0
    generated_nodes = 1

    def search(g_cost, current_limit):
        nonlocal expanded_nodes, generated_nodes

        current = path[-1]
        f_score = g_cost + heuristic(current, goal)

        if f_score > current_limit:
            return f_score

        if current == goal:
            return FOUND

        if expanded_nodes >= max_expanded_nodes:
            return float("inf")

        expanded_nodes += 1
        next_limit = float("inf")

        neighbors = get_neighbors(current)

        def next_score(item):
            next_pos, step_cost = item
            return step_cost + heuristic(next_pos, goal)

        neighbors.sort(key=next_score)

        for next_pos, step_cost in neighbors:
            if next_pos in path:
                continue

            path.append(next_pos)
            generated_nodes += 1

            result = search(g_cost + step_cost, current_limit)
            if result == FOUND:
                return FOUND

            if result < next_limit:
                next_limit = result

            path.pop()

        return next_limit

    for _ in range(max_iterations):
        result = search(0, limit)

        if result == FOUND:
            final_path = list(path)
            cost = calculate_path_cost(final_path, get_neighbors)
            runtime = (perf_counter() - started_at) * 1000
            return SearchResult("IDA_STAR", final_path, cost, expanded_nodes, generated_nodes, runtime)

        if result == float("inf"):
            break

        limit = result

    runtime = (perf_counter() - started_at) * 1000
    return SearchResult("IDA_STAR", [], float("inf"), expanded_nodes, generated_nodes, runtime)
