from __future__ import annotations

"""Depth-First Search (DFS).

DFS đi sâu theo một nhánh trước khi quay lui. Thuật toán này ít tốn bộ nhớ
hơn BFS nhưng không đảm bảo đường đi ngắn nhất.
"""

from time import perf_counter
from src.ai.pathfinding.search_common import SearchResult, is_goal, reconstruct_path

def dfs(start, goal, get_neighbors, max_depth=5000) -> SearchResult:
    """Tìm đường bằng stack LIFO và giới hạn độ sâu để tránh lặp vô hạn."""

    started_at = perf_counter()
    stack = [(start, 0)]
    parent = {start: None}
    step = {start: 0}

    reached = set()

    expanded_nodes = 0
    generated_nodes = 1

    while stack:

        current, depth = stack.pop()

        # reached giúp tránh mở rộng lại một node đã xử lý.
        if current in reached:
            continue

        reached.add(current)

        expanded_nodes += 1

        if is_goal(current, goal):
            path = reconstruct_path(parent, current)

            return SearchResult(

                algorithm="DFS",
                path=path,
                cost=step[current],
                expanded_nodes=expanded_nodes,
                generated_nodes=generated_nodes,
                runtime_ms=(perf_counter() - started_at) * 1000,
            )

        if depth >= max_depth:
            continue

        neighbors = get_neighbors(current)
        # Đảo thứ tự để khi push vào stack, thứ tự duyệt gần giống danh sách neighbor ban đầu.
        neighbors.reverse()

        for next_pos, _ in neighbors:
            if next_pos in reached:
                continue

            if next_pos not in parent:
                parent[next_pos] = current
                step[next_pos] = step[current] + 1
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


