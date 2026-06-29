from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import permutations
from math import inf, sqrt
from time import perf_counter

from src.gameplay.auto.maps.graph_adapter import AutoMapGraph
from src.gameplay.auto.maps.tmx_loader import AutoMapData, GridPos
from src.gameplay.auto.models import AutoOrder


MatrixState = tuple[tuple[str, ...], ...]


@dataclass
class DeliveryNode:
    state: MatrixState
    pos: GridPos
    parent: "DeliveryNode | None"
    move: str
    carrying: bool
    delivery: str | None
    cost: float


@dataclass
class DeliverySearchResult:
    algorithm: str
    path: list[GridPos]
    actions: tuple[str, ...]
    cost: float
    expanded_nodes: int
    generated_nodes: int
    runtime_ms: float

    @property
    def found(self) -> bool:
        return bool(self.path)


def house_name(order: AutoOrder) -> str:
    return order.id.replace("O", "D", 1)


def make_state(map_data: AutoMapData, orders: list[AutoOrder], trap_cells=()) -> MatrixState:
    traps = {obj.grid_pos for obj in map_data.traffic_traps + map_data.block_traps}
    traps.update(trap_cells)
    stores = {order.store_pos for order in orders}
    houses = {order.customer_pos for order in orders}
    rows: list[list[str]] = []

    for y in range(map_data.height):
        row: list[str] = []
        for x in range(map_data.width):
            pos = (x, y)
            if not map_data.is_walkable(pos):
                row.append("#")
            elif pos in traps:
                row.append("T")
            elif pos in stores:
                row.append("S")
            elif pos in houses:
                row.append("H")
            else:
                row.append(".")
        rows.append(row)

    return tuple(tuple(row) for row in rows)


def change_to_road(state: MatrixState, pos: GridPos) -> MatrixState:
    x, y = pos
    rows = [list(row) for row in state]
    rows[y][x] = "."
    return tuple(tuple(row) for row in rows)


def make_path(node: DeliveryNode) -> list[GridPos]:
    path: list[GridPos] = []
    while node is not None:
        path.append(node.pos)
        node = node.parent
    path.reverse()
    return path


def make_actions(node: DeliveryNode) -> tuple[str, ...]:
    actions: list[str] = []
    while node is not None:
        if node.move.startswith("P_") or node.move.startswith("D_"):
            actions.append(node.move)
        node = node.parent
    actions.reverse()
    return tuple(actions)


def distance(map_id: int, a: GridPos, b: GridPos) -> float:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    if map_id == 1:
        return dx + dy
    return sqrt(dx * dx + dy * dy)


class DeliverySearch:
    def __init__(self, map_data: AutoMapData, orders: list[AutoOrder], algorithm: str, trap_cells=()) -> None:
        self.map_data = map_data
        self.orders = orders
        self.algorithm = algorithm
        self.graph = AutoMapGraph(map_data)
        self.start_state = make_state(map_data, orders, trap_cells)
        self.house_by_pos = {order.customer_pos: house_name(order) for order in orders}
        self.local_h_cache = {}
        self.expanded = 0
        self.generated = 0

    def start_node(self) -> DeliveryNode:
        return DeliveryNode(
            state=self.start_state,
            pos=self.map_data.start_position,
            parent=None,
            move="START",
            carrying=False,
            delivery=None,
            cost=0.0,
        )

    def node_key(self, node: DeliveryNode) -> tuple:
        return node.pos, node.carrying, node.delivery, node.state

    def cell_cost(self, node: DeliveryNode, pos: GridPos) -> float:
        if self.algorithm in ("BFS", "DFS"):
            return 1.0

        x, y = pos
        cell = node.state[y][x]
        if cell == "T":
            return 50.0
        if cell == "S":
            return 1.0 if not node.carrying else 10.0
        if cell == "H":
            house = self.house_by_pos.get(pos)
            if node.carrying and node.delivery == house:
                return 1.0
            return 10.0
        return 10.0

    def make_child(
        self,
        node: DeliveryNode,
        next_pos: GridPos,
        order: AutoOrder,
        action: str,
    ) -> DeliveryNode:
        state = node.state
        carrying = node.carrying
        delivery = node.delivery
        move = self.move_name(node.pos, next_pos)

        if action == "PICKUP" and next_pos == order.store_pos and not carrying:
            state = change_to_road(state, next_pos)
            carrying = True
            delivery = house_name(order)
            move = f"P_{order.id}"

        if action == "DELIVERY" and next_pos == order.customer_pos:
            if carrying and delivery == house_name(order):
                state = change_to_road(state, next_pos)
                carrying = False
                delivery = None
                move = f"D_{order.id}"

        return DeliveryNode(
            state=state,
            pos=next_pos,
            parent=node,
            move=move,
            carrying=carrying,
            delivery=delivery,
            cost=node.cost + self.cell_cost(node, next_pos),
        )

    def children(self, node: DeliveryNode, order: AutoOrder, action: str) -> list[DeliveryNode]:
        result: list[DeliveryNode] = []
        for next_pos, _ in self.graph.get_neighbors(node.pos):
            result.append(self.make_child(node, next_pos, order, action))
        return result

    def priority(self, node: DeliveryNode, goal: GridPos) -> float:
        h = distance(self.map_data.map_id, node.pos, goal)
        if self.algorithm == "GREEDY":
            return h
        if self.algorithm in ("ASTAR", "IDA_STAR"):
            return node.cost + h
        return node.cost

    def find_segment(
        self,
        start: DeliveryNode,
        goal: GridPos,
        order: AutoOrder,
        action: str,
    ) -> DeliveryNode | None:
        if self.algorithm == "BFS":
            return self.bfs(start, goal, order, action)
        if self.algorithm == "DFS":
            return self.dfs(start, goal, order, action)
        if self.algorithm == "SIMPLE_HILL":
            return self.simple_hill_segment(start, goal, order, action)
        if self.algorithm == "STEEPEST_HILL":
            return self.steepest_hill_segment(start, goal, order, action)
        if self.algorithm == "LOCAL_BEAM":
            return self.local_beam_segment(start, goal, order, action)
        return self.best_first(start, goal, order, action)

    def local_h(self, node: DeliveryNode, order: AutoOrder | None = None, action: str = "") -> float:
        key = (node.pos, node.state, node.carrying, node.delivery, getattr(order, "id", None), action)
        if key in self.local_h_cache:
            return self.local_h_cache[key]

        if node.carrying:
            for order_item in self.orders:
                if house_name(order_item) == node.delivery:
                    after_delivery = change_to_road(node.state, order_item.customer_pos)
                    value = distance(self.map_data.map_id, node.pos, order_item.customer_pos)
                    value += self.best_order_h(order_item.customer_pos, after_delivery)
                    self.local_h_cache[key] = value
                    return value
            return float("inf")

        value = self.best_order_h(node.pos, node.state)
        self.local_h_cache[key] = value
        return value

    def best_order_h(self, start_pos: GridPos, state: MatrixState) -> float:
        orders_left = []
        for order in self.orders:
            x, y = order.store_pos
            if state[y][x] == "S":
                orders_left.append(order)

        if not orders_left:
            return 0.0

        best = float("inf")
        for order_list in permutations(orders_left):
            total = 0.0
            current_pos = start_pos
            for order in order_list:
                total += distance(self.map_data.map_id, current_pos, order.store_pos)
                total += distance(self.map_data.map_id, order.store_pos, order.customer_pos)
                current_pos = order.customer_pos

            if total < best:
                best = total

        return best

    def simple_hill_segment(self, start: DeliveryNode, goal: GridPos, order: AutoOrder, action: str) -> DeliveryNode | None:
        current = start
        max_steps = self.map_data.width * self.map_data.height * 4

        for _ in range(max_steps):
            self.expanded += 1
            if current.pos == goal:
                return current

            current_h = self.local_h(current, order, action)
            best_h = current_h
            best_nodes = []

            for child in self.children(current, order, action):
                self.generated += 1
                child_h = self.local_h(child, order, action)

                if child_h < best_h:
                    best_h = child_h
                    best_nodes = [child]
                elif child_h == best_h and child_h <= current_h:
                    best_nodes.append(child)

            if not best_nodes:
                return None

            current = random.choice(best_nodes)

        return current if current.pos == goal else None

    def steepest_hill_segment(self, start: DeliveryNode, goal: GridPos, order: AutoOrder, action: str) -> DeliveryNode | None:
        current = start
        max_steps = self.map_data.width * self.map_data.height * 4

        for _ in range(max_steps):
            self.expanded += 1
            if current.pos == goal:
                return current

            current_h = self.local_h(current, order, action)
            best_h = current_h
            best_nodes = []

            for child in self.children(current, order, action):
                self.generated += 1
                child_h = self.local_h(child, order, action)

                if child_h < best_h:
                    best_h = child_h
                    best_nodes = [child]
                elif child_h == best_h and child_h <= current_h:
                    best_nodes.append(child)

            if not best_nodes:
                return None

            current = random.choice(best_nodes)

        return current if current.pos == goal else None

    def local_beam_segment(self, start: DeliveryNode, goal: GridPos, order: AutoOrder, action: str) -> DeliveryNode | None:
        beam = [start]
        beam_width = 5
        max_steps = self.map_data.width * self.map_data.height * 4

        for _ in range(max_steps):
            candidates = []

            for node in beam:
                self.expanded += 1
                if node.pos == goal:
                    return node

                for child in self.children(node, order, action):
                    self.generated += 1
                    h = self.local_h(child, order, action)
                    candidates.append((h, child.cost, child))

            if not candidates:
                return None

            candidates.sort(key=lambda item: (item[0], item[1]))
            beam = [item[2] for item in candidates[:beam_width]]

        for node in beam:
            if node.pos == goal:
                return node
        return None

    def bfs(self, start: DeliveryNode, goal: GridPos, order: AutoOrder, action: str) -> DeliveryNode | None:
        frontier: deque[DeliveryNode] = deque([start])
        reached = {self.node_key(start)}
        self.generated += 1

        while frontier:
            node = frontier.popleft()
            self.expanded += 1
            if node.pos == goal:
                return node

            for child in self.children(node, order, action):
                key = self.node_key(child)
                if key in reached:
                    continue
                reached.add(key)
                frontier.append(child)
                self.generated += 1

        return None

    def dfs(self, start: DeliveryNode, goal: GridPos, order: AutoOrder, action: str) -> DeliveryNode | None:
        frontier: list[DeliveryNode] = [start]
        reached = {self.node_key(start)}
        self.generated += 1

        while frontier:
            node = frontier.pop()
            self.expanded += 1
            if node.pos == goal:
                return node

            for child in reversed(self.children(node, order, action)):
                key = self.node_key(child)
                if key in reached:
                    continue
                reached.add(key)
                frontier.append(child)
                self.generated += 1

        return None

    def best_first(self, start: DeliveryNode, goal: GridPos, order: AutoOrder, action: str) -> DeliveryNode | None:
        frontier: list[tuple[float, int, DeliveryNode]] = []
        reached = {self.node_key(start): start.cost}
        order_number = 0

        heappush(frontier, (self.priority(start, goal), order_number, start))
        self.generated += 1

        while frontier:
            _, _, node = heappop(frontier)
            if node.cost > reached.get(self.node_key(node), inf):
                continue

            self.expanded += 1
            if node.pos == goal:
                return node

            for child in self.children(node, order, action):
                key = self.node_key(child)
                if child.cost >= reached.get(key, inf):
                    continue

                reached[key] = child.cost
                order_number += 1
                heappush(frontier, (self.priority(child, goal), order_number, child))
                self.generated += 1

        return None

    def choose_order(self, current: DeliveryNode) -> tuple[AutoOrder | None, DeliveryNode | None]:
        best_order = None
        best_node = None
        best_score = inf

        for order in self.orders:
            x, y = order.store_pos
            if current.state[y][x] != "S":
                continue

            node = self.find_segment(current, order.store_pos, order, "PICKUP")
            if node is None:
                continue

            if self.algorithm in ("BFS", "DFS"):
                score = len(make_path(node))
            elif self.algorithm == "GREEDY":
                score = distance(self.map_data.map_id, order.store_pos, order.customer_pos)
            elif self.algorithm in ("SIMPLE_HILL", "STEEPEST_HILL", "LOCAL_BEAM"):
                score = self.local_h(node)
            else:
                score = node.cost

            if score < best_score:
                best_score = score
                best_order = order
                best_node = node

        return best_order, best_node

    def solve(self) -> DeliveryNode:
        current = self.start_node()

        for _ in self.orders:
            order, pickup_node = self.choose_order(current)
            if order is None or pickup_node is None:
                break

            delivery_node = self.find_segment(
                start=pickup_node,
                goal=order.customer_pos,
                order=order,
                action="DELIVERY",
            )
            if delivery_node is None:
                break

            current = delivery_node

        return current

    @staticmethod
    def move_name(current: GridPos, next_pos: GridPos) -> str:
        dx = next_pos[0] - current[0]
        dy = next_pos[1] - current[1]
        if dx == 1:
            return "RIGHT"
        if dx == -1:
            return "LEFT"
        if dy == 1:
            return "DOWN"
        if dy == -1:
            return "UP"
        return "MOVE"


def delivery_search(map_data: AutoMapData, orders: list[AutoOrder], algorithm: str, trap_cells=()) -> DeliverySearchResult:
    started_at = perf_counter()
    name = algorithm.strip().upper().replace("-", "_").replace("*", "STAR")
    search = DeliverySearch(map_data, orders, name, trap_cells)
    end_node = search.solve()

    return DeliverySearchResult(
        algorithm=name,
        path=make_path(end_node),
        actions=make_actions(end_node),
        cost=end_node.cost,
        expanded_nodes=search.expanded,
        generated_nodes=search.generated,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )
