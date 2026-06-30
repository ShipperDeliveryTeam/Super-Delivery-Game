from __future__ import annotations

"""Uniform Cost Search (UCS).

UCS luôn mở rộng node có tổng chi phí từ start nhỏ nhất. Thuật toán phù hợp
khi mỗi bước đi có thể có chi phí khác nhau, ví dụ đi chéo đắt hơn đi thẳng.
"""

from heapq import heappop, heappush
from time import perf_counter

from src.ai.pathfinding.search_common import SearchResult, reconstruct_path


def ucs(start, goal, get_neighbors) -> SearchResult:
    """Tìm đường tối ưu theo chi phí thực bằng priority queue."""

    started_at = perf_counter()

    # Heap lưu bộ (cost, order, node); order dùng để phá hòa khi cost bằng nhau.
    queue = []
    order = 0
    heappush(queue, (0, order, start))

    parent = {start: None}
    cost = {start: 0}

    expanded_nodes = 0
    generated_nodes = 1

    while queue:
        current_cost, _, current = heappop(queue)

        # Bỏ qua bản ghi cũ nếu node đã được tìm thấy với chi phí tốt hơn.
        if current_cost != cost[current]:
            continue

        expanded_nodes += 1

        if current == goal:
            path = reconstruct_path(parent, goal)
            runtime = (perf_counter() - started_at) * 1000
            return SearchResult("UCS", path, cost[goal], expanded_nodes, generated_nodes, runtime)

        for next_pos, step_cost in get_neighbors(current):
            new_cost = cost[current] + step_cost

            # Chỉ cập nhật khi tìm được đường rẻ hơn tới next_pos.
            if next_pos in cost and cost[next_pos] <= new_cost:
                continue

            parent[next_pos] = current
            cost[next_pos] = new_cost
            order += 1
            heappush(queue, (new_cost, order, next_pos))
            generated_nodes += 1

    runtime = (perf_counter() - started_at) * 1000
    return SearchResult("UCS", [], float("inf"), expanded_nodes, generated_nodes, runtime)
