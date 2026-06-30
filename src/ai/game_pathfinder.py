"""Tim duong tren map cua game.

GamePathfinder giu thong tin cua map:
- map co bao nhieu cot, bao nhieu hang
- o nao bi chan
- co duoc di cheo khong
- co luat vong xuyen khong

Khi game can tim duong, game goi:

    find_path(start, goal, algorithm)

Ham nay se chon dung thuat toan va tra ve PathResult.
"""

from math import sqrt
import random

from src.ai.pathfinding.informed_search.astar import astar as pathfinding_astar
from src.ai.pathfinding.informed_search.greedy import greedy_best_first_search
from src.ai.pathfinding.informed_search.ida_star import ida_star as pathfinding_ida_star
from src.ai.pathfinding.local_search.local_beam import local_beam_search
from src.ai.pathfinding.local_search.simple_hill import simple_hill as pathfinding_simple_hill
from src.ai.pathfinding.local_search.steepest_hill import steepest_hill as pathfinding_steepest_hill
from src.ai.pathfinding.uninformed_search.bfs import bfs as pathfinding_bfs
from src.ai.pathfinding.uninformed_search.dfs import dfs as pathfinding_dfs
from src.ai.pathfinding.uninformed_search.ucs import ucs as pathfinding_ucs


class PathResult:
    """Ket qua ma gameplay can doc."""

    def __init__(self, path, expanded_nodes=0, success=False, algorithm=""):
        self.path = path
        self.expanded_nodes = expanded_nodes
        self.success = success
        self.algorithm = algorithm


class GamePathfinder:
    """Class nay giu map va goi cac thuat toan tim duong."""

    def __init__(
        self,
        cols,
        rows,
        blocked=None,
        allow_diagonal=False,
        roundabout_ring=None,
        roundabout_connections=None,
    ):
        self.cols = cols
        self.rows = rows
        self.blocked = blocked or set()
        self.allow_diagonal = bool(allow_diagonal)

        # Mot so map co vong xuyen nen can luu them luat di rieng.
        self.roundabout_ring = tuple(roundabout_ring or ())
        self._roundabout_nodes = set(self.roundabout_ring)

        self._roundabout_connection_edges = set()
        for a, b in (roundabout_connections or ()):
            self._roundabout_connection_edges.add(self._edge_key(a, b))

        self._roundabout_edges = self._build_roundabout_edges()

        self._roundabout_successor = {}
        for index, current in enumerate(self.roundabout_ring):
            previous_index = (index - 1) % len(self.roundabout_ring)
            self._roundabout_successor[current] = self.roundabout_ring[previous_index]

        self._diagonal_edges = self._build_diagonal_edges()

    def set_blocked(self, blocked):
        """Doi danh sach o bi chan."""

        self.blocked = blocked or set()
        self._diagonal_edges = self._build_diagonal_edges()

    def find_path(self, start, goal, algorithm="ASTAR"):
        """Chon thuat toan theo ten."""

        name = str(algorithm or "ASTAR").upper()

        if name == "BFS" or name == "BREADTH_FIRST_SEARCH":
            return self.bfs(start, goal)

        if name == "DFS" or name == "DEPTH_FIRST_SEARCH":
            return self.dfs(start, goal)

        if name == "UCS" or name == "UNIFORM_COST_SEARCH":
            return self.ucs(start, goal)

        if name in ("GREEDY", "GREEDY_BEST_FIRST", "GREEDY_BEST_FIRST_SEARCH"):
            return self.greedy_best_first(start, goal)

        if name in ("ASTAR", "A*", "A_STAR"):
            return self.astar(start, goal)

        if name in ("IDA_STAR", "IDASTAR", "IDA*"):
            return self.ida_star(start, goal)

        if name in ("BEAM", "BEAM_SEARCH", "LOCAL_BEAM"):
            return self.beam_search(start, goal, label=name)

        if name == "SIMPLE_HILL" or name == "HILL_CLIMBING":
            return self.simple_hill(start, goal)

        if name == "STEEPEST_HILL" or name == "STEEPEST_ASCENT":
            return self.steepest_hill(start, goal)

        # Cac nhom duoi day trong play mode van can mot path de NPC di duoc.
        # Vi vay ta dung thuat toan gan dung roi doi ten hien thi.
        if name == "NO_OBSERVATION" or name == "NO_OBS":
            result = self.partial_observation(start, goal, view_radius=0)
            result.algorithm = "NO_OBSERVATION"
            return result

        if name in ("PARTIAL", "PARTIAL_OBSERVATION", "PARTIALLY_OBSERVATION"):
            return self.partial_observation(start, goal, view_radius=7)

        if name == "AND_OR_SEARCH" or name == "AND_OR":
            result = self.astar(start, goal)
            result.algorithm = "AND_OR_SEARCH"
            return result

        if name in ("BACKTRACKING", "FORWARD_CHECKING", "AC3_BACKTRACKING"):
            result = self.ucs(start, goal)
            result.algorithm = name
            return result

        if name in ("MINIMAX", "ALPHA_BETA", "EXPECTIMAX"):
            result = self.greedy_best_first(start, goal)
            result.algorithm = name
            return result

        return self.astar(start, goal)

    def weighted_neighbors(self, pos):
        """Lay cac o hang xom kem chi phi di chuyen."""

        result = []

        for next_pos in self.neighbors(pos):
            cost = self.move_cost(pos, next_pos)
            result.append((next_pos, cost))

        return result

    def simple_neighbors(self, pos):
        """Lay cac o hang xom, khong can chi phi."""

        return list(self.neighbors(pos))

    def search_result_to_path_result(self, result, label):
        """Doi SearchResult cua BFS/UCS/A* ve PathResult cua game."""

        return PathResult(
            path=list(result.path),
            expanded_nodes=result.expanded_nodes,
            success=result.success,
            algorithm=label,
        )

    def local_result_to_path_result(self, result, label):
        """Doi ket qua local search ve PathResult cua game."""

        return PathResult(
            path=list(result.path),
            expanded_nodes=result.expanded_nodes,
            success=result.found,
            algorithm=label,
        )

    def fail_result(self, label):
        return PathResult([], 0, False, label)

    def bfs(self, start, goal):
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return self.fail_result("BFS")

        result = pathfinding_bfs(start, goal, self.weighted_neighbors)
        return self.search_result_to_path_result(result, "BFS")

    def dfs(self, start, goal, max_depth=None):
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return self.fail_result("DFS")

        if max_depth is None:
            max_depth = self.cols * self.rows

        result = pathfinding_dfs(
            start,
            goal,
            self.weighted_neighbors,
            max_depth=max_depth,
        )
        return self.search_result_to_path_result(result, "DFS")

    def ucs(self, start, goal):
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return self.fail_result("UCS")

        result = pathfinding_ucs(start, goal, self.weighted_neighbors)
        return self.search_result_to_path_result(result, "UCS")

    def greedy_best_first(self, start, goal):
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return self.fail_result("GREEDY")

        result = greedy_best_first_search(
            start,
            goal,
            self.weighted_neighbors,
            self.distance,
        )
        return self.search_result_to_path_result(result, "GREEDY")

    def astar(self, start, goal):
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return self.fail_result("ASTAR")

        result = pathfinding_astar(
            start,
            goal,
            self.weighted_neighbors,
            self.distance,
        )
        return self.search_result_to_path_result(result, "ASTAR")

    def ida_star(self, start, goal):
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return self.fail_result("IDA_STAR")

        result = pathfinding_ida_star(
            start,
            goal,
            self.weighted_neighbors,
            self.distance,
            max_iterations=80,
            max_expanded_nodes=min(4000, max(500, self.cols * self.rows * 3)),
        )
        path_result = self.search_result_to_path_result(result, "IDA_STAR")

        # Neu IDA* khong tim thay, dung A* de game van co duong di.
        if path_result.success:
            return path_result

        fallback = self.astar(start, goal)
        fallback.expanded_nodes += path_result.expanded_nodes
        fallback.algorithm = "IDA_STAR"
        return fallback

    def beam_search(self, start, goal, beam_width=4, label="BEAM"):
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return self.fail_result(label)

        result = local_beam_search(
            start,
            goal,
            self.simple_neighbors,
            lambda pos: self.distance(pos, goal),
            beam_width=beam_width,
            max_steps=self.cols * self.rows,
        )
        path_result = self.local_result_to_path_result(result, label)
        return self.finish_local_search(path_result, start, goal, label)

    def simple_hill(self, start, goal):
        label = "SIMPLE_HILL"

        if not self.is_walkable(start) or not self.is_walkable(goal):
            return self.fail_result(label)

        result = pathfinding_simple_hill(
            start,
            goal,
            self.simple_neighbors,
            lambda pos: self.distance(pos, goal),
            max_steps=self.cols * self.rows,
        )
        path_result = self.local_result_to_path_result(result, label)
        return self.finish_local_search(path_result, start, goal, label)

    def steepest_hill(self, start, goal):
        label = "STEEPEST_HILL"

        if not self.is_walkable(start) or not self.is_walkable(goal):
            return self.fail_result(label)

        result = pathfinding_steepest_hill(
            start,
            goal,
            self.simple_neighbors,
            lambda pos: self.distance(pos, goal),
            max_steps=self.cols * self.rows,
        )
        path_result = self.local_result_to_path_result(result, label)
        return self.finish_local_search(path_result, start, goal, label)

    def finish_local_search(self, path_result, start, goal, label):
        """Local search co the ket giua duong, nen thu noi tiep bang A*."""

        if path_result.success:
            return path_result

        if path_result.path:
            restart = path_result.path[-1]
            prefix = path_result.path[:-1]
        else:
            restart = start
            prefix = []

        fallback = self.astar(restart, goal)
        if fallback.success:
            return PathResult(
                path=prefix + fallback.path,
                expanded_nodes=path_result.expanded_nodes + fallback.expanded_nodes,
                success=True,
                algorithm=label,
            )

        return path_result

    def partial_observation(self, start, goal, view_radius=7):
        """Ban don gian: di gan ve dich, khi thay dich thi dung A*."""

        label = "PARTIAL_OBSERVATION"

        if not self.is_walkable(start) or not self.is_walkable(goal):
            return self.fail_result(label)

        current = start
        path = [start]
        expanded = 0
        visited_count = {start: 1}
        max_steps = min(250, max(50, self.cols * self.rows // 4))

        for _ in range(max_steps):
            if current == goal:
                return PathResult(path, expanded, True, label)

            if self.distance(current, goal) <= view_radius:
                rest = self.astar(current, goal)
                expanded += rest.expanded_nodes

                if rest.success and len(rest.path) > 1:
                    return PathResult(path[:-1] + rest.path, expanded, True, label)

            options = list(self.neighbors(current))
            if not options:
                break

            options.sort(
                key=lambda pos: (
                    self.distance(pos, goal) + visited_count.get(pos, 0) * 5,
                    random.random(),
                )
            )

            current = options[0]
            path.append(current)
            visited_count[current] = visited_count.get(current, 0) + 1
            expanded += 1

        rest = self.astar(current, goal)
        expanded += rest.expanded_nodes

        if rest.success and rest.path:
            return PathResult(path[:-1] + rest.path, expanded, True, label)

        return PathResult(path, expanded, current == goal, label)

    def neighbors(self, pos):
        """Sinh cac o co the di tu pos."""

        x, y = pos

        directions = [
            (1, 0),
            (0, 1),
            (-1, 0),
            (0, -1),
        ]

        if self.allow_diagonal:
            directions.extend(
                [
                    (1, 1),
                    (1, -1),
                    (-1, 1),
                    (-1, -1),
                ]
            )

        for dx, dy in directions:
            next_pos = (x + dx, y + dy)

            if self.can_step(pos, next_pos):
                yield next_pos

    def is_walkable(self, pos):
        """Kiem tra mot o co nam trong map va khong bi chan khong."""

        x, y = pos

        if x < 0 or x >= self.cols:
            return False

        if y < 0 or y >= self.rows:
            return False

        if pos in self.blocked:
            return False

        return True

    @staticmethod
    def manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def distance(self, a, b):
        """Uoc luong khoang cach tu a den b."""

        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])

        if not self.allow_diagonal:
            return dx + dy

        return sqrt(dx * dx + dy * dy)

    @staticmethod
    def move_cost(a, b):
        """Di ngang/doc ton 1, di cheo ton can bac hai cua 2."""

        if a[0] != b[0] and a[1] != b[1]:
            return 1.41421356237

        return 1.0

    def can_step(self, start, end):
        """Kiem tra co duoc di mot buoc tu start sang end khong."""

        if not self.is_walkable(start):
            return False

        if not self.is_walkable(end):
            return False

        if not self._roundabout_transition_allowed(start, end):
            return False

        return self._can_step(start, end)

    def _can_step(self, start, end):
        dx = end[0] - start[0]
        dy = end[1] - start[1]

        # Khong dung yen tai cho.
        if dx == 0 and dy == 0:
            return False

        # Chi duoc di sang o ke ben.
        if abs(dx) > 1 or abs(dy) > 1:
            return False

        if self._edge_key(start, end) in self._roundabout_edges:
            return True

        # Di ngang/doc.
        if dx == 0 or dy == 0:
            return True

        # Di cheo theo canh da cho phep.
        if self._edge_key(start, end) in self._diagonal_edges:
            return True

        # Truong hop hai o noi voi nhau bang goc nho.
        horizontal_side = (start[0] + dx, start[1])
        vertical_side = (start[0], start[1] + dy)
        return not self.is_walkable(horizontal_side) and not self.is_walkable(vertical_side)

    def is_roundabout_edge(self, start, end):
        if start not in self._roundabout_nodes:
            return False

        if end not in self._roundabout_nodes:
            return False

        return self._edge_key(start, end) in self._roundabout_edges

    def is_roundabout_connection(self, start, end):
        return self._edge_key(start, end) in self._roundabout_connection_edges

    def _roundabout_transition_allowed(self, start, end):
        start_in_roundabout = start in self._roundabout_nodes
        end_in_roundabout = end in self._roundabout_nodes

        if not start_in_roundabout and not end_in_roundabout:
            return True

        if start_in_roundabout and end_in_roundabout:
            return self._roundabout_successor.get(start) == end

        return self._edge_key(start, end) in self._roundabout_connection_edges

    def _build_roundabout_edges(self):
        edges = set(self._roundabout_connection_edges)

        if len(self.roundabout_ring) >= 2:
            for index, current in enumerate(self.roundabout_ring):
                next_index = (index + 1) % len(self.roundabout_ring)
                next_pos = self.roundabout_ring[next_index]
                edges.add(self._edge_key(current, next_pos))

        return edges

    @staticmethod
    def _edge_key(a, b):
        """Luu canh theo mot dang duy nhat."""

        if a <= b:
            return (a, b)

        return (b, a)

    def _build_diagonal_edges(self, minimum_run=4):
        """Tim cac doan duong cheo dai de cho phep di cheo."""

        if not self.allow_diagonal:
            return set()

        edges = set()

        for dx, dy in ((1, 1), (1, -1)):
            for y in range(self.rows):
                for x in range(self.cols):
                    start = (x, y)

                    if not self.is_walkable(start):
                        continue

                    previous = (x - dx, y - dy)
                    if self.is_walkable(previous):
                        continue

                    diagonal_line = []
                    current = start

                    while self.is_walkable(current):
                        diagonal_line.append(current)
                        current = (current[0] + dx, current[1] + dy)

                    if len(diagonal_line) < minimum_run:
                        continue

                    for i in range(len(diagonal_line) - 1):
                        first = diagonal_line[i]
                        second = diagonal_line[i + 1]
                        edges.add(self._edge_key(first, second))

        return edges
