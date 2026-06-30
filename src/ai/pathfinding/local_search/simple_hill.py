from __future__ import annotations

"""Simple Hill Climbing.

Thuật toán leo đồi đơn giản chỉ nhìn các hàng xóm hiện tại và chọn hướng làm
heuristic tốt hơn. Nó chạy nhanh nhưng dễ kẹt ở local optimum hoặc plateau.
"""

import random
from dataclasses import dataclass
from time import perf_counter
from typing import Callable


GridPos = tuple[int, int]
NeighborFn = Callable[[GridPos], list[GridPos]]
HeuristicFn = Callable[[GridPos], float]


@dataclass
class LocalPathResult:
    """Kết quả chuẩn cho các thuật toán local search."""

    algorithm: str
    path: list[GridPos]
    found: bool
    expanded_nodes: int
    generated_nodes: int
    runtime_ms: float


def simple_hill(
    start: GridPos,
    goal: GridPos,
    get_neighbors: NeighborFn,
    heuristic: HeuristicFn,
    max_steps: int = 1000,
) -> LocalPathResult:
    """Di chuyển từng bước tới neighbor có heuristic tốt hơn hiện tại."""

    started_at = perf_counter()
    current = start
    path = [start]
    expanded = 0
    generated = 0

    for _ in range(max_steps):
        expanded += 1
        if current == goal:
            break

        current_h = heuristic(current)
        best_h = current_h
        best_neighbors = []

        for neighbor in get_neighbors(current):
            generated += 1
            neighbor_h = heuristic(neighbor)

            # Chỉ nhận neighbor nếu nó không tệ hơn điểm hiện tại.
            if neighbor_h < best_h:
                best_h = neighbor_h
                best_neighbors = [neighbor]
            elif neighbor_h == best_h and neighbor_h <= current_h:
                best_neighbors.append(neighbor)

        # Không còn hướng tốt hơn: thuật toán dừng tại local optimum.
        if not best_neighbors:
            break

        # Nếu có nhiều lựa chọn ngang nhau, chọn ngẫu nhiên để tránh hành vi quá cứng.
        current = random.choice(best_neighbors)
        path.append(current)

    return LocalPathResult(
        algorithm="SIMPLE_HILL",
        path=path,
        found=path[-1] == goal,
        expanded_nodes=expanded,
        generated_nodes=generated,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )
