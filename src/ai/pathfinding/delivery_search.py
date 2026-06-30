from __future__ import annotations

from dataclasses import dataclass, field
from itertools import permutations
from math import sqrt
from time import perf_counter

from src.ai.pathfinding.informed_search.astar import astar
from src.ai.pathfinding.informed_search.greedy import greedy_best_first_search
from src.ai.pathfinding.informed_search.ida_star import ida_star
from src.ai.pathfinding.local_search.local_beam import local_beam_search
from src.ai.pathfinding.local_search.simple_hill import simple_hill
from src.ai.pathfinding.local_search.steepest_hill import steepest_hill
from src.ai.pathfinding.uninformed_search.bfs import bfs
from src.ai.pathfinding.uninformed_search.dfs import dfs
from src.ai.pathfinding.uninformed_search.ucs import ucs
from src.gameplay.auto.maps.graph_adapter import AutoMapGraph
from src.gameplay.auto.maps.tmx_loader import AutoMapData, GridPos
from src.gameplay.auto.models import AutoOrder


MatrixState = tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class DeliveryNode:
    """Mot node cua bai toan giao hang tong quat."""

    state: MatrixState
    pos: GridPos
    carrying: bool = False
    delivery: str | None = None
    move: str = field(default="START", compare=False)
    cost: float = field(default=0.0, compare=False)


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


def distance(map_id: int, a: GridPos, b: GridPos) -> float:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])

    if map_id == 1:
        return dx + dy

    return sqrt(dx * dx + dy * dy)


def change_to_road(state: MatrixState, pos: GridPos) -> MatrixState:
    x, y = pos
    rows = [list(row) for row in state]
    rows[y][x] = "."
    return tuple(tuple(row) for row in rows)


class DeliveryProblem:
    """Tao start, goal, neighbors, heuristic cho cac thuat toan pathfinding."""

    def __init__(self, map_data: AutoMapData, orders: list[AutoOrder], algorithm: str, trap_cells=()):
        self.map_data = map_data # Dữ liệu bản đồ
        self.orders = orders # Danh sách các đơn hàng
        self.algorithm = algorithm # Thuat toán tìm đường được sử dụng
        self.graph = AutoMapGraph(map_data) # Đồ thị biểu diễn bản đồ

        self.store_by_pos = {order.store_pos: order for order in orders} # ánh xạ vị trí cửa hàng đến đơn hàng
        self.customer_by_pos = {order.customer_pos: order for order in orders} # ánh xạ vị trí khách hàng đến đơn hàng
        self.customer_by_house = {house_name(order): order for order in orders} # ánh xạ tên nhà đến đơn hàng
        self.start_state = self.make_matrix_state(trap_cells) # Trạng thái ban đầu
        self.h_cache = {} # Cache cho giá trị heuristic để tránh tính toán lại nhiều lần

    def make_matrix_state(self, trap_cells=()) -> MatrixState:
        traps = {tuple(pos) for pos in trap_cells}
        if not traps:
            traps = {obj.grid_pos for obj in self.map_data.traffic_traps + self.map_data.block_traps}

        stores = set(self.store_by_pos)
        houses = set(self.customer_by_pos)
        rows = []

        for y in range(self.map_data.height):
            row = []
            for x in range(self.map_data.width):
                pos = (x, y)
                if not self.map_data.is_walkable(pos):
                    row.append("#")
                elif pos in traps:
                    row.append("T")
                elif pos in stores:
                    row.append("S")
                elif pos in houses:
                    row.append("H")
                else:
                    row.append(".")
            rows.append(tuple(row))

        return tuple(rows)

    def start_node(self) -> DeliveryNode:
        return DeliveryNode(
            state=self.start_state,
            pos=self.map_data.start_position,
            carrying=False,
            delivery=None,
            move="START",
            cost=0.0,
        )

    def is_goal(self, node: DeliveryNode) -> bool:
        if node.carrying:
            return False

        for row in node.state:
            if "S" in row:
                return False

        return True

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
            order = self.customer_by_pos.get(pos)
            if node.carrying and order and node.delivery == house_name(order):
                return 1.0
            return 10.0

        return 10.0

    def neighbors(self, node: DeliveryNode) -> list[tuple[DeliveryNode, float]]:
        result = []

        for next_pos, _ in self.graph.get_neighbors(node.pos):  # Lấy các vị trí lân cận của node hiện tại
            state = node.state  # Lấy trạng thái hiện tại của node
            carrying = node.carrying # Lấy trạng thái mang hàng hiện tại của node
            delivery = node.delivery # Lấy trạng thái giao hàng hiện tại của node
            move = self.move_name(node.pos, next_pos) # Lấy tên hành động di chuyển từ vị trí hiện tại đến vị trí tiếp theo

            order = self.store_by_pos.get(next_pos) # Nếu vị trí tiếp theo là cửa hàng, lấy đơn hàng tương ứng
            if order is not None and not carrying:
                x, y = next_pos
                if state[y][x] == "S": # Nếu ô tiếp theo là cửa hàng và chưa mang hàng, cập nhật trạng thái 
                    state = change_to_road(state, next_pos)
                    carrying = True 
                    delivery = house_name(order)
                    move = f"P_{order.id}" 
 
            order = self.customer_by_pos.get(next_pos) # Nếu vị trí tiếp theo là nhà giao hàng, lấy đơn hàng tương ứng
            if order is not None and carrying and delivery == house_name(order):
                x, y = next_pos
                if state[y][x] == "H":
                    state = change_to_road(state, next_pos)
                    carrying = False
                    delivery = None
                    move = f"D_{order.id}"

            step_cost = self.cell_cost(node, next_pos)
            child = DeliveryNode(
                state=state,
                pos=next_pos,
                carrying=carrying,
                delivery=delivery,
                move=move,
                cost=node.cost + step_cost,
            )
            result.append((child, step_cost))

        return result

    def simple_neighbors(self, node: DeliveryNode) -> list[DeliveryNode]:
        return [child for child, _ in self.neighbors(node)]

    def heuristic(self, node: DeliveryNode, _goal=None) -> float:
        key = (node.state, node.pos, node.carrying, node.delivery)
        if key in self.h_cache:
            return self.h_cache[key]

        if node.carrying:
            order = self.customer_by_house.get(node.delivery)
            if order is None:
                return float("inf")

            next_state = change_to_road(node.state, order.customer_pos)
            value = distance(self.map_data.map_id, node.pos, order.customer_pos)
            value += self.best_order_h(order.customer_pos, next_state)
        else:
            value = self.best_order_h(node.pos, node.state)

        self.h_cache[key] = value
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


DeliverySearch = DeliveryProblem


def normalize_algorithm_name(algorithm: str) -> str:
    return algorithm.strip().upper().replace("-", "_").replace("*", "STAR")


def run_algorithm(problem: DeliveryProblem, algorithm: str):
    start = problem.start_node()
    goal = problem.is_goal

    if algorithm == "BFS":
        return bfs(start, goal, problem.neighbors)

    if algorithm == "DFS":
        max_depth = problem.map_data.width * problem.map_data.height * max(1, len(problem.orders)) * 4
        return dfs(start, goal, problem.neighbors, max_depth=max_depth)

    if algorithm == "UCS":
        return ucs(start, goal, problem.neighbors)

    if algorithm == "GREEDY":
        return greedy_best_first_search(start, goal, problem.neighbors, problem.heuristic)

    if algorithm == "ASTAR":
        return astar(start, goal, problem.neighbors, problem.heuristic)

    if algorithm == "IDA_STAR":
        return ida_star(
            start,
            goal,
            problem.neighbors,
            problem.heuristic,
            max_iterations=200,
            max_expanded_nodes=max(50000, problem.map_data.width * problem.map_data.height * 20),
        )

    if algorithm == "SIMPLE_HILL":
        return simple_hill(
            start,
            goal,
            problem.simple_neighbors,
            lambda node: problem.heuristic(node, goal),
            max_steps=problem.map_data.width * problem.map_data.height * max(1, len(problem.orders)) * 4,
        )

    if algorithm == "STEEPEST_HILL":
        return steepest_hill(
            start,
            goal,
            problem.simple_neighbors,
            lambda node: problem.heuristic(node, goal),
            max_steps=problem.map_data.width * problem.map_data.height * max(1, len(problem.orders)) * 4,
        )

    if algorithm == "LOCAL_BEAM":
        return local_beam_search(
            start,
            goal,
            problem.simple_neighbors,
            lambda node: problem.heuristic(node, goal),
            beam_width=5,
            max_steps=problem.map_data.width * problem.map_data.height * max(1, len(problem.orders)) * 4,
        )

    return astar(start, goal, problem.neighbors, problem.heuristic)


def result_path_positions(state_path: list[DeliveryNode]) -> list[GridPos]:
    return [node.pos for node in state_path]


def result_actions(state_path: list[DeliveryNode]) -> tuple[str, ...]:
    actions = []

    for node in state_path:
        if node.move.startswith("P_") or node.move.startswith("D_"):
            actions.append(node.move)

    return tuple(actions)


def delivery_search(map_data: AutoMapData, orders: list[AutoOrder], algorithm: str, trap_cells=()) -> DeliverySearchResult:
    started_at = perf_counter()
    name = normalize_algorithm_name(algorithm) #truyền tên thuật toán vào hàm normalize_algorithm_name 
    problem = DeliveryProblem(map_data, orders, name, trap_cells)
    result = run_algorithm(problem, name)

    found = bool(getattr(result, "success", getattr(result, "found", False)))

    if found:
        state_path = list(result.path)
    else:
        state_path = []

    if not found:
        total_cost = float("inf")
    elif hasattr(result, "cost"):
        total_cost = result.cost
    elif state_path:
        total_cost = state_path[-1].cost
    else:
        total_cost = float("inf")

    return DeliverySearchResult(
        algorithm=name,
        path=result_path_positions(state_path),
        actions=result_actions(state_path),
        cost=total_cost,
        expanded_nodes=result.expanded_nodes,
        generated_nodes=result.generated_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )
