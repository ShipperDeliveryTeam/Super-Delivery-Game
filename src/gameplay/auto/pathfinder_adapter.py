from __future__ import annotations

from src.ai.pathfinding.astar import astar
from src.ai.pathfinding.bfs import bfs
from src.ai.pathfinding.dfs import dfs
from src.ai.pathfinding.greedy import greedy
from src.ai.pathfinding.ida_star import ida_star
from src.ai.pathfinding.search_common import GridPos, SearchResult
from src.ai.pathfinding.ucs import ucs
from src.gameplay.auto.maps.graph_adapter import AutoMapGraph


PATHFINDING_ALGORITHMS = {
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
    return algorithm.strip().upper().replace("-", "_").replace("*", "STAR")


def find_auto_path(
    graph: AutoMapGraph,
    start: GridPos,
    goal: GridPos,
    algorithm: str,
) -> SearchResult:
    algorithm_name = normalize_algorithm_name(algorithm)

    if algorithm_name not in PATHFINDING_ALGORITHMS:
        raise ValueError(f"Unsupported pathfinding algorithm: {algorithm}")

    search_fn = PATHFINDING_ALGORITHMS[algorithm_name]

    if algorithm_name in INFORMED_ALGORITHMS:
        return search_fn(
            start=start,
            goal=goal,
            get_neighbors=graph.get_neighbors,
            heuristic=graph.heuristic,
        )

    return search_fn(
        start=start,
        goal=goal,
        get_neighbors=graph.get_neighbors,
    )


def get_supported_pathfinding_algorithms() -> list[str]:
    return list(PATHFINDING_ALGORITHMS.keys())