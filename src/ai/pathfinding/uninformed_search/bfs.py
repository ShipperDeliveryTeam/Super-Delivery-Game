from __future__ import annotations
from collections import deque
from time import perf_counter
from src.ai.pathfinding.search_common import SearchResult, reconstruct_path

def bfs(start, goal, get_neighbors) -> SearchResult:

    started_at = perf_counter()

    queue = deque()
    queue.append(start)

    parent = {start: None}
    step = {start: 0}
    expanded_nodes = 0
    generated_nodes = 1

    while queue:
        current = queue.popleft()

        expanded_nodes += 1

        if current == goal:

            path = reconstruct_path(parent, goal)

            return SearchResult(

                algorithm="BFS",

                path=path,
                cost=step[goal],
                expanded_nodes=expanded_nodes,
                generated_nodes=generated_nodes,
                runtime_ms=(perf_counter() - started_at) * 1000,
            )

        for next_pos, _ in get_neighbors(current):

            if next_pos in parent:
                continue

            parent[next_pos] = current
            step[next_pos] = step[current] + 1
            queue.append(next_pos)
            generated_nodes += 1

    return SearchResult(

        algorithm="BFS",

        path=[],

        cost=float("inf"),

        expanded_nodes=expanded_nodes,

        generated_nodes=generated_nodes,

        runtime_ms=(perf_counter() - started_at) * 1000,
    )


