from __future__ import annotations

from math import inf
from time import perf_counter

from src.ai.pathfinding.search_common import (
    GridPos,
    HeuristicFn,
    NeighborFn,
    SearchResult,
    calculate_path_cost,
)


_FOUND = "FOUND"


def ida_star(
    start: GridPos,
    goal: GridPos,
    get_neighbors: NeighborFn,
    heuristic: HeuristicFn,
    max_iterations: int = 300,
    max_expanded_nodes: int = 300000,
) -> SearchResult:
    started_at = perf_counter()

    bound = heuristic(start, goal)
    path: list[GridPos] = [start]
    path_set: set[GridPos] = {start}

    expanded_nodes = 0
    generated_nodes = 1

    def search(
        current: GridPos,
        g_cost: float,
        current_bound: float,
        best_g_in_iteration: dict[GridPos, float],
    ) -> float | str:
        nonlocal expanded_nodes, generated_nodes

        f_cost = g_cost + heuristic(current, goal)

        if f_cost > current_bound:
            return f_cost

        if current == goal:
            return _FOUND

        if expanded_nodes >= max_expanded_nodes:
            return inf

        expanded_nodes += 1
        best_g_in_iteration[current] = g_cost

        min_next_bound = inf

        neighbors = sorted(
            get_neighbors(current),
            key=lambda item: g_cost + item[1] + heuristic(item[0], goal),
        )

        for next_pos, step_cost in neighbors:
            if next_pos in path_set:
                continue

            new_g_cost = g_cost + step_cost

            if new_g_cost >= best_g_in_iteration.get(next_pos, inf):
                continue

            path.append(next_pos)
            path_set.add(next_pos)
            generated_nodes += 1

            result = search(
                current=next_pos,
                g_cost=new_g_cost,
                current_bound=current_bound,
                best_g_in_iteration=best_g_in_iteration,
            )

            if result == _FOUND:
                return _FOUND

            if isinstance(result, float) and result < min_next_bound:
                min_next_bound = result

            path.pop()
            path_set.remove(next_pos)

        return min_next_bound

    for _ in range(max_iterations):
        best_g_in_iteration: dict[GridPos, float] = {}

        result = search(
            current=start,
            g_cost=0.0,
            current_bound=bound,
            best_g_in_iteration=best_g_in_iteration,
        )

        if result == _FOUND:
            final_path = list(path)

            return SearchResult(
                algorithm="IDA_STAR",
                path=final_path,
                cost=calculate_path_cost(final_path, get_neighbors),
                expanded_nodes=expanded_nodes,
                generated_nodes=generated_nodes,
                runtime_ms=(perf_counter() - started_at) * 1000,
            )

        if result == inf:
            break

        bound = float(result)

    return SearchResult(
        algorithm="IDA_STAR",
        path=[],
        cost=float("inf"),
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )