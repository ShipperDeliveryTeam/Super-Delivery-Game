from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush
import random
from typing import Dict, Iterable, List, Optional, Tuple

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
    ):
        self.cols = cols
        self.rows = rows
        self.blocked = blocked or set()
        self.allow_diagonal = bool(allow_diagonal)
        self._diagonal_edges = self._build_diagonal_edges()

    def set_blocked(self, blocked: set[GridPos]) -> None:
        self.blocked = blocked or set()
        self._diagonal_edges = self._build_diagonal_edges()

    def find_path(self, start: GridPos, goal: GridPos, algorithm: str = "ASTAR") -> PathResult:
        algorithm = str(algorithm or "ASTAR").upper()

        if algorithm in ("BFS", "BREADTH_FIRST_SEARCH"):
            return self.bfs(start, goal)

        if algorithm in ("ASTAR", "A*", "A_STAR"):
            return self.astar(start, goal)

        if algorithm in ("BEAM", "BEAM_SEARCH"):
            return self.beam_search(start, goal, beam_width=4)

        if algorithm in ("PARTIAL", "PARTIAL_OBSERVATION", "PARTIALLY_OBSERVATION"):
            return self.partial_observation(start, goal, view_radius=7)

        if algorithm in ("Q_LEARNING", "Q-LEARNING", "QLEARNING"):
            return self.q_learning_like(start, goal)

        return self.astar(start, goal)

    def bfs(self, start: GridPos, goal: GridPos) -> PathResult:
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return PathResult([], 0, False, "BFS")

        queue = deque([start])
        came_from: Dict[GridPos, Optional[GridPos]] = {start: None}
        expanded = 0

        while queue:
            current = queue.popleft()
            expanded += 1

            if current == goal:
                return PathResult(self.reconstruct(came_from, start, goal), expanded, True, "BFS")

            for nxt in self.neighbors(current):
                if nxt not in came_from:
                    came_from[nxt] = current
                    queue.append(nxt)

        return PathResult([], expanded, False, "BFS")

    def astar(self, start: GridPos, goal: GridPos) -> PathResult:
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return PathResult([], 0, False, "ASTAR")

        open_heap = []
        heappush(open_heap, (0, 0, start))

        came_from: Dict[GridPos, Optional[GridPos]] = {start: None}
        g_score: Dict[GridPos, float] = {start: 0.0}

        expanded = 0
        counter = 0
        closed = set()

        while open_heap:
            _, _, current = heappop(open_heap)

            if current in closed:
                continue

            closed.add(current)
            expanded += 1

            if current == goal:
                return PathResult(self.reconstruct(came_from, start, goal), expanded, True, "ASTAR")

            for nxt in self.neighbors(current):
                new_cost = g_score[current] + self.move_cost(current, nxt)

                if nxt not in g_score or new_cost < g_score[nxt]:
                    g_score[nxt] = new_cost
                    priority = new_cost + self.distance(nxt, goal)
                    counter += 1
                    heappush(open_heap, (priority, counter, nxt))
                    came_from[nxt] = current

        return PathResult([], expanded, False, "ASTAR")

    def beam_search(self, start: GridPos, goal: GridPos, beam_width: int = 4) -> PathResult:
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return PathResult([], 0, False, "BEAM")

        frontier = [(start, [start])]
        visited = {start}
        expanded = 0
        max_layers = self.cols + self.rows

        for _ in range(max_layers):
            candidates = []

            for current, path in frontier:
                expanded += 1

                if current == goal:
                    return PathResult(path, expanded, True, "BEAM")

                for nxt in self.neighbors(current):
                    if nxt not in visited:
                        visited.add(nxt)
                        score = self.distance(nxt, goal)
                        candidates.append((score, nxt, path + [nxt]))

            if not candidates:
                break

            candidates.sort(key=lambda item: item[0])
            frontier = [(pos, path) for _, pos, path in candidates[:beam_width]]

        return PathResult([], expanded, False, "BEAM")

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

    def q_learning_like(self, start: GridPos, goal: GridPos) -> PathResult:
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return PathResult([], 0, False, "Q_LEARNING")

        current = start
        path = [start]
        expanded = 0
        visited_count: Dict[GridPos, int] = {start: 1}

        max_steps = min(180, max(40, self.cols + self.rows + 30))
        no_progress_count = 0
        best_distance = self.distance(start, goal)

        for _ in range(max_steps):
            if current == goal:
                return PathResult(path, expanded, True, "Q_LEARNING")

            options = list(self.neighbors(current))

            if not options:
                break

            if random.random() < 0.10:
                nxt = random.choice(options)
            else:
                def reward(pos: GridPos) -> float:
                    distance_reward = -self.distance(pos, goal) * 2.0
                    repeat_penalty = -visited_count.get(pos, 0) * 6.0
                    random_tie_break = random.random() * 0.01
                    return distance_reward + repeat_penalty + random_tie_break

                nxt = max(options, key=reward)

            current_distance = self.distance(nxt, goal)

            if current_distance < best_distance:
                best_distance = current_distance
                no_progress_count = 0
            else:
                no_progress_count += 1

            current = nxt
            path.append(current)
            visited_count[current] = visited_count.get(current, 0) + 1
            expanded += 1

            if no_progress_count >= 18 or current_distance <= 8:
                fallback = self.astar(current, goal)
                expanded += fallback.expanded_nodes

                if fallback.success and fallback.path:
                    return PathResult(path[:-1] + fallback.path, expanded, True, "Q_LEARNING")

        fallback = self.astar(current, goal)
        expanded += fallback.expanded_nodes

        if fallback.success and fallback.path:
            return PathResult(path[:-1] + fallback.path, expanded, True, "Q_LEARNING")

        return PathResult(path, expanded, current == goal, "Q_LEARNING")

    def neighbors(self, pos: GridPos) -> Iterable[GridPos]:
        x, y = pos

        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        if self.allow_diagonal:
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])

        for dx, dy in directions:
            nxt = (x + dx, y + dy)

            if self.is_walkable(nxt) and self._can_step(pos, nxt):
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

    @staticmethod
    def reconstruct(came_from: Dict[GridPos, Optional[GridPos]], start: GridPos, goal: GridPos) -> List[GridPos]:
        if goal not in came_from:
            return []

        current = goal
        path = [current]

        while current != start:
            current = came_from[current]

            if current is None:
                break

            path.append(current)

        path.reverse()
        return path
