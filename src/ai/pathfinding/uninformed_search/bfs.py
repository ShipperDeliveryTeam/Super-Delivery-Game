from __future__ import annotations

"""Breadth-First Search (BFS).

BFS mở rộng theo từng lớp khoảng cách từ start. Với bản đồ có mỗi bước đi
cùng chi phí, BFS đảm bảo tìm được đường có ít bước nhất.
"""

from collections import deque
from time import perf_counter
from src.ai.pathfinding.search_common import SearchResult, reconstruct_path

def bfs(start, goal, get_neighbors) -> SearchResult:
    """Tìm đường bằng hàng đợi FIFO: node vào trước sẽ được mở rộng trước."""

    started_at = perf_counter() # thời gian bắt đầu chạy thuật toán

    # Queue lưu các ô cần xét tiếp theo theo đúng thứ tự từng lớp.
    queue = deque()
    queue.append(start)

    # parent dùng để truy vết đường đi sau khi gặp goal.
    parent = {start: None}
    step = {start: 0}
    expanded_nodes = 0 # số node được lấy ra khỏi queue và xét
    generated_nodes = 1 # số node được thêm vào queue

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
            # Nếu đã có parent nghĩa là ô này đã được phát hiện trước đó.
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