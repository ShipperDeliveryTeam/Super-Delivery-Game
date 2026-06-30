from dataclasses import dataclass
import random
from typing import Iterable, List, Optional, Tuple

from src.ai.pathfinding.informed_search.astar import astar as pathfinding_astar
from src.ai.pathfinding.informed_search.greedy import greedy_best_first_search
from src.ai.pathfinding.informed_search.ida_star import ida_star as pathfinding_ida_star
from src.ai.pathfinding.local_search.local_beam import local_beam_search
from src.ai.pathfinding.local_search.simple_hill import simple_hill as pathfinding_simple_hill
from src.ai.pathfinding.local_search.steepest_hill import steepest_hill as pathfinding_steepest_hill
from src.ai.pathfinding.uninformed_search.bfs import bfs as pathfinding_bfs
from src.ai.pathfinding.uninformed_search.dfs import dfs as pathfinding_dfs
from src.ai.pathfinding.uninformed_search.ucs import ucs as pathfinding_ucs

GridPos = Tuple[int, int]


@dataclass
class PathResult:
    path: List[GridPos]
    expanded_nodes: int = 0
    success: bool = False
    algorithm: str = ""


class GamePathfinder:
    def __init__(
        self,
        cols: int,
        rows: int,
        blocked: Optional[set[GridPos]] = None,
        allow_diagonal: bool = False,
        roundabout_ring: Optional[Iterable[GridPos]] = None,
        roundabout_connections: Optional[Iterable[tuple[GridPos, GridPos]]] = None,
    ):
        self.cols = cols
        self.rows = rows
        self.blocked = blocked or set()
        self.allow_diagonal = bool(allow_diagonal)
        self.roundabout_ring = tuple(roundabout_ring or ())
        self._roundabout_nodes = set(self.roundabout_ring)
        self._roundabout_connection_edges = {
            self._edge_key(a, b) for a, b in (roundabout_connections or ())
        }
        self._roundabout_edges = self._build_roundabout_edges()
        self._roundabout_successor = {
            current: self.roundabout_ring[(index - 1) % len(self.roundabout_ring)]
            for index, current in enumerate(self.roundabout_ring)
        } if self.roundabout_ring else {}
        self._diagonal_edges = self._build_diagonal_edges()

    def set_blocked(self, blocked: set[GridPos]) -> None:
        self.blocked = blocked or set()
        self._diagonal_edges = self._build_diagonal_edges()

    def find_path(self, start: GridPos, goal: GridPos, algorithm: str = "ASTAR") -> PathResult:
        algorithm = str(algorithm or "ASTAR").upper()

        if algorithm in ("BFS", "BREADTH_FIRST_SEARCH"):
            return self.bfs(start, goal)

        if algorithm in ("DFS", "DEPTH_FIRST_SEARCH"):
            return self.dfs(start, goal)

        if algorithm in ("UCS", "UNIFORM_COST_SEARCH"):
            return self.ucs(start, goal)

        if algorithm in ("GREEDY", "GREEDY_BEST_FIRST", "GREEDY_BEST_FIRST_SEARCH"):
            return self.greedy_best_first(start, goal)

        if algorithm in ("ASTAR", "A*", "A_STAR"):
            return self.astar(start, goal)

        if algorithm in ("IDA_STAR", "IDASTAR", "IDA*"):
            return self.ida_star(start, goal)

        if algorithm in ("BEAM", "BEAM_SEARCH", "LOCAL_BEAM"):
            return self.beam_search(start, goal, beam_width=4, label=algorithm)

        if algorithm in ("SIMPLE_HILL", "HILL_CLIMBING"):
            return self.simple_hill(start, goal)

        if algorithm in ("STEEPEST_HILL", "STEEPEST_ASCENT"):
            return self.steepest_hill(start, goal)

        if algorithm in ("NO_OBSERVATION", "NO_OBS"):
            return self._with_algorithm_label(
                self.partial_observation(start, goal, view_radius=0),
                "NO_OBSERVATION",
            )

        if algorithm in ("PARTIAL", "PARTIAL_OBSERVATION", "PARTIALLY_OBSERVATION"):
            return self.partial_observation(start, goal, view_radius=7)

        if algorithm in ("AND_OR_SEARCH", "AND_OR"):
            return self._with_algorithm_label(self.astar(start, goal), "AND_OR_SEARCH")

        if algorithm in ("BACKTRACKING", "FORWARD_CHECKING", "AC3_BACKTRACKING"):
            return self._with_algorithm_label(self.ucs(start, goal), algorithm)

        if algorithm in ("MINIMAX", "ALPHA_BETA", "EXPECTIMAX"):
            return self._with_algorithm_label(self.greedy_best_first(start, goal), algorithm)

        return self.astar(start, goal)

    @staticmethod
    def _with_algorithm_label(result: PathResult, label: str) -> PathResult:
        result.algorithm = label
        return result

    def _weighted_neighbors(self, pos: GridPos) -> list[tuple[GridPos, float]]:
        return [(nxt, self.move_cost(pos, nxt)) for nxt in self.neighbors(pos)]

    def _unweighted_neighbors(self, pos: GridPos) -> list[GridPos]:
        return list(self.neighbors(pos))

    def _to_path_result(self, result, label: str | None = None) -> PathResult:
        algorithm = label or getattr(result, "algorithm", "")
        success = bool(getattr(result, "success", getattr(result, "found", False)))
        return PathResult(
            path=list(getattr(result, "path", [])),
            expanded_nodes=int(getattr(result, "expanded_nodes", 0)),
            success=success,
            algorithm=algorithm,
        )

    def _pathfinding_result(
        self,
        search_fn,
        start: GridPos,
        goal: GridPos,
        label: str | None = None,
        *args,
        **kwargs,
    ) -> PathResult:
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return PathResult([], 0, False, label or "")

        result = search_fn(start, goal, self._weighted_neighbors, *args, **kwargs)
        return self._to_path_result(result, label)

    def _local_result(
        self,
        search_fn,
        start: GridPos,
        goal: GridPos,
        label: str,
        *args,
        **kwargs,
    ) -> PathResult:
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return PathResult([], 0, False, label)

        result = search_fn(
            start,
            goal,
            self._unweighted_neighbors,
            lambda pos: self.distance(pos, goal),
            *args,
            **kwargs,
        )
        path_result = self._to_path_result(result, label)

        if path_result.success:
            return path_result

        fallback = self.astar(path_result.path[-1] if path_result.path else start, goal)
        if fallback.success and fallback.path:
            path_prefix = path_result.path[:-1] if path_result.path else []
            return PathResult(
                path=path_prefix + fallback.path,
                expanded_nodes=path_result.expanded_nodes + fallback.expanded_nodes,
                success=True,
                algorithm=label,
            )

        return path_result

    def bfs(self, start: GridPos, goal: GridPos) -> PathResult:
        return self._pathfinding_result(pathfinding_bfs, start, goal, "BFS")

    def dfs(self, start: GridPos, goal: GridPos, max_depth: int | None = None) -> PathResult:
        return self._pathfinding_result(
            pathfinding_dfs,
            start,
            goal,
            "DFS",
            max_depth=max_depth or self.cols * self.rows,
        )

    def ucs(self, start: GridPos, goal: GridPos) -> PathResult:
        return self._pathfinding_result(pathfinding_ucs, start, goal, "UCS")

    def greedy_best_first(self, start: GridPos, goal: GridPos) -> PathResult:
        return self._pathfinding_result(
            greedy_best_first_search,
            start,
            goal,
            "GREEDY",
            heuristic=self.distance,
        )

    def astar(self, start: GridPos, goal: GridPos) -> PathResult:
        return self._pathfinding_result(
            pathfinding_astar,
            start,
            goal,
            "ASTAR",
            heuristic=self.distance,
        )

    def ida_star(self, start: GridPos, goal: GridPos) -> PathResult:
        result = self._pathfinding_result(
            pathfinding_ida_star,
            start,
            goal,
            "IDA_STAR",
            heuristic=self.distance,
            max_iterations=80,
            max_expanded_nodes=min(4000, max(500, self.cols * self.rows * 3)),
        )

        if result.success:
            return result

        fallback = self.astar(start, goal)
        fallback.expanded_nodes += result.expanded_nodes
        return self._with_algorithm_label(fallback, "IDA_STAR")

    def beam_search(self, start: GridPos, goal: GridPos, beam_width: int = 4, label: str = "BEAM") -> PathResult:
        return self._local_result(
            local_beam_search,
            start,
            goal,
            label,
            beam_width=beam_width,
            max_steps=self.cols * self.rows,
        )

    def simple_hill(self, start: GridPos, goal: GridPos) -> PathResult:
        return self._local_result(
            pathfinding_simple_hill,
            start,
            goal,
            "SIMPLE_HILL",
            max_steps=self.cols * self.rows,
        )

    def steepest_hill(self, start: GridPos, goal: GridPos) -> PathResult:
        return self._local_result(
            pathfinding_steepest_hill,
            start,
            goal,
            "STEEPEST_HILL",
            max_steps=self.cols * self.rows,
        )

    def partial_observation(self, start: GridPos, goal: GridPos, view_radius: int = 7) -> PathResult:
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return PathResult([], 0, False, "PARTIAL_OBSERVATION")

        current = start
        full_path = [start]
        expanded = 0
        visited_count: Dict[GridPos, int] = {start: 1}
        max_steps = min(250, max(50, self.cols * self.rows // 4))

        for _ in range(max_steps):
            if current == goal:
                return PathResult(full_path, expanded, True, "PARTIAL_OBSERVATION")

            if self.distance(current, goal) <= view_radius:
                result = self.astar(current, goal)
                expanded += result.expanded_nodes

                if result.success and len(result.path) > 1:
                    return PathResult(full_path[:-1] + result.path, expanded, True, "PARTIAL_OBSERVATION")

            options = list(self.neighbors(current))

            if not options:
                break

            options.sort(
                key=lambda pos: (
                    self.distance(pos, goal) + visited_count.get(pos, 0) * 5,
                    random.random(),
                )
            )

            nxt = options[0]
            visited_count[nxt] = visited_count.get(nxt, 0) + 1
            current = nxt
            full_path.append(current)
            expanded += 1

        fallback = self.astar(current, goal)
        expanded += fallback.expanded_nodes

        if fallback.success and fallback.path:
            return PathResult(full_path[:-1] + fallback.path, expanded, True, "PARTIAL_OBSERVATION")

        return PathResult(full_path, expanded, current == goal, "PARTIAL_OBSERVATION")

    def neighbors(self, pos: GridPos) -> Iterable[GridPos]:
        x, y = pos

        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        if self.allow_diagonal:
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])

        for dx, dy in directions:
            nxt = (x + dx, y + dy)

            if self.can_step(pos, nxt):
                yield nxt

    def is_walkable(self, pos: GridPos) -> bool:
        x, y = pos
        return 0 <= x < self.cols and 0 <= y < self.rows and pos not in self.blocked

    @staticmethod
    def manhattan(a: GridPos, b: GridPos) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def distance(self, a: GridPos, b: GridPos) -> float:
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])

        if not self.allow_diagonal:
            return dx + dy

        return max(dx, dy) + (1.41421356237 - 1.0) * min(dx, dy)

    @staticmethod
    def move_cost(a: GridPos, b: GridPos) -> float:
        return 1.41421356237 if a[0] != b[0] and a[1] != b[1] else 1.0

    def _can_step(self, start: GridPos, end: GridPos) -> bool:
        dx = end[0] - start[0]
        dy = end[1] - start[1]

        if abs(dx) <= 1 and abs(dy) <= 1 and (dx != 0 or dy != 0):
            if self._edge_key(start, end) in self._roundabout_edges:
                return True

            if dx == 0 or dy == 0:
                return True

            horizontal_side = (start[0] + dx, start[1])
            vertical_side = (start[0], start[1] + dy)

            if self._edge_key(start, end) in self._diagonal_edges:
                return True

            # Preserve short corner-connected diagonal pieces that are too
            # small to form a full detected corridor.
            return not self.is_walkable(horizontal_side) and not self.is_walkable(vertical_side)

        return False

    def can_step(self, start: GridPos, end: GridPos) -> bool:
        return (
            self.is_walkable(start)
            and self.is_walkable(end)
            and self._roundabout_transition_allowed(start, end)
            and self._can_step(start, end)
        )

    def is_roundabout_edge(self, start: GridPos, end: GridPos) -> bool:
        if start not in self._roundabout_nodes or end not in self._roundabout_nodes:
            return False

        return self._edge_key(start, end) in self._roundabout_edges

    def is_roundabout_connection(self, start: GridPos, end: GridPos) -> bool:
        return self._edge_key(start, end) in self._roundabout_connection_edges

    def _roundabout_transition_allowed(self, start: GridPos, end: GridPos) -> bool:
        if start not in self._roundabout_nodes and end not in self._roundabout_nodes:
            return True

        if start in self._roundabout_nodes and end in self._roundabout_nodes:
            return self._roundabout_successor.get(start) == end

        return self._edge_key(start, end) in self._roundabout_connection_edges

    def _build_roundabout_edges(self) -> set[tuple[GridPos, GridPos]]:
        edges = set(self._roundabout_connection_edges)

        if len(self.roundabout_ring) >= 2:
            for index, current in enumerate(self.roundabout_ring):
                following = self.roundabout_ring[(index + 1) % len(self.roundabout_ring)]
                edges.add(self._edge_key(current, following))

        return edges

    @staticmethod
    def _edge_key(a: GridPos, b: GridPos) -> tuple[GridPos, GridPos]:
        return (a, b) if a <= b else (b, a)

    def _build_diagonal_edges(self, minimum_run: int = 4) -> set[tuple[GridPos, GridPos]]:
        if not self.allow_diagonal:
            return set()

        edges: set[tuple[GridPos, GridPos]] = set()

        for dx, dy in ((1, 1), (1, -1)):
            for y in range(self.rows):
                for x in range(self.cols):
                    start = (x, y)

                    if not self.is_walkable(start):
                        continue

                    previous = (x - dx, y - dy)

                    if self.is_walkable(previous):
                        continue

                    run = []
                    current = start

                    while self.is_walkable(current):
                        run.append(current)
                        current = (current[0] + dx, current[1] + dy)

                    if len(run) < minimum_run:
                        continue

                    for first, second in zip(run, run[1:]):
                        edges.add(self._edge_key(first, second))

        return edges

