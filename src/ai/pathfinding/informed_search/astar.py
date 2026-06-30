from __future__ import annotations

"""A* Search.

A* kết hợp chi phí đã đi `g(n)` và ước lượng còn lại `h(n)`. Điểm ưu tiên là
`f(n) = g(n) + h(n)`, vì vậy thuật toán vừa hướng về đích vừa vẫn xét chi phí
đường đi thực tế.
"""

from heapq import heappop, heappush
from time import perf_counter

from src.ai.pathfinding.search_common import SearchResult, is_goal, reconstruct_path


def astar(start, goal, get_neighbors, heuristic) -> SearchResult:
    """Tìm đường bằng A*, thường là lựa chọn chính cho NPC trong game."""

    started_at = perf_counter()

    # Heap ưu tiên node có f-score nhỏ nhất.
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

        if is_goal(current, goal):
            path = reconstruct_path(parent, current)
            runtime = (perf_counter() - started_at) * 1000
            return SearchResult("ASTAR", path, cost[current], expanded_nodes, generated_nodes, runtime)

        for next_pos, step_cost in get_neighbors(current):
            new_cost = cost[current] + step_cost

            # Nếu từng tới next_pos bằng đường rẻ hơn hoặc bằng thì bỏ qua.
            if next_pos in cost and cost[next_pos] <= new_cost:
                continue

            parent[next_pos] = current
            cost[next_pos] = new_cost
            order += 1

            # f = g + h: chi phí đã đi + ước lượng khoảng cách tới goal.
            f_score = new_cost + heuristic(next_pos, goal)
            heappush(queue, (f_score, order, next_pos))
            generated_nodes += 1

    runtime = (perf_counter() - started_at) * 1000
    return SearchResult("ASTAR", [], float("inf"), expanded_nodes, generated_nodes, runtime)
