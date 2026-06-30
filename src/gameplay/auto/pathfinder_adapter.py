from __future__ import annotations

"""Adapter gọi các thuật toán pathfinding trong Auto Mode.

Auto Mode dùng `AutoMapGraph`, còn thuật toán trong `src/ai/pathfinding` chỉ
cần hàm get_neighbors/heuristic. Adapter này nối hai phần đó lại với nhau.
"""

from src.ai.pathfinding.informed_search import astar, greedy, ida_star
from src.ai.pathfinding.search_common import GridPos, SearchResult
from src.ai.pathfinding.uninformed_search import bfs, dfs, ucs
from src.gameplay.auto.maps.graph_adapter import AutoMapGraph


PATHFINDING_ALGORITHMS = {
    # Map tên thuật toán trong UI/benchmark sang hàm triển khai thật.
    "BFS": bfs,
    "DFS": dfs,
    "UCS": ucs,
    "GREEDY": greedy,
    "ASTAR": astar,
    "IDA_STAR": ida_star,
}


INFORMED_ALGORITHMS = {
    "GREEDY",
    "ASTAR",
    "IDA_STAR",
}


def normalize_algorithm_name(algorithm: str) -> str:
    """Chuẩn hóa tên nhập vào: A*, ida-star... về dạng key nội bộ."""

    return algorithm.strip().upper().replace("-", "_").replace("*", "STAR")


def find_auto_path(
    graph: AutoMapGraph,
    start: GridPos,
    goal: GridPos,
    algorithm: str,
) -> SearchResult:
    """Tìm đường trên AutoMapGraph bằng thuật toán được chọn."""

    algorithm_name = normalize_algorithm_name(algorithm)

    if algorithm_name not in PATHFINDING_ALGORITHMS:
        raise ValueError(f"Unsupported pathfinding algorithm: {algorithm}")

    search_fn = PATHFINDING_ALGORITHMS[algorithm_name]

    if algorithm_name in INFORMED_ALGORITHMS:
        # Thuật toán informed cần thêm heuristic.
        return search_fn(
            start=start,
            goal=goal,
            get_neighbors=graph.get_neighbors,
            heuristic=graph.heuristic,
        )

    # Thuật toán uninformed chỉ cần danh sách neighbor.
    return search_fn(
        start=start,
        goal=goal,
        get_neighbors=graph.get_neighbors,
    )


def get_supported_pathfinding_algorithms() -> list[str]:
    """Danh sách thuật toán pathfinding cơ bản mà adapter hỗ trợ."""

    return list(PATHFINDING_ALGORITHMS.keys())
