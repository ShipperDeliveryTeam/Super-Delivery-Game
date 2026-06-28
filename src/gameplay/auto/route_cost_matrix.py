from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt

from src.gameplay.auto.maps.graph_adapter import AutoMapGraph
from src.gameplay.auto.maps.tmx_loader import GridPos, load_auto_map
from src.gameplay.auto.models import AutoOrder
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.pathfinder_adapter import find_auto_path


@dataclass(frozen=True)
class RouteNode:
    label: str
    pos: GridPos
    kind: str
    order_id: str | None = None


@dataclass
class RouteCostEntry:
    from_label: str
    to_label: str
    cost: float
    steps: int
    path: list[GridPos]
    expanded_nodes: int
    generated_nodes: int
    runtime_ms: float

    @property
    def reachable(self) -> bool:
        return bool(self.path)


@dataclass
class RouteCostMatrix:
    map_id: int
    algorithm: str
    nodes: dict[str, RouteNode]
    costs: dict[tuple[str, str], RouteCostEntry] = field(default_factory=dict)

    def get_cost(self, from_label: str, to_label: str) -> float:
        if from_label == to_label:
            return 0.0

        entry = self.costs.get((from_label, to_label))

        if entry is None:
            return float("inf")

        return entry.cost

    def get_heuristic_cost(self, from_label: str, to_label: str) -> float:
        if from_label == to_label:
            return 0.0

        from_node = self.nodes.get(from_label)
        to_node = self.nodes.get(to_label)
        if from_node is None or to_node is None:
            return float("inf")

        dx = abs(from_node.pos[0] - to_node.pos[0])
        dy = abs(from_node.pos[1] - to_node.pos[1])
        if self.map_id == 1:
            return float(dx + dy)
        return sqrt(dx * dx + dy * dy)

    def get_path(self, from_label: str, to_label: str) -> list[GridPos]:
        entry = self.costs.get((from_label, to_label))

        if entry is None:
            return []

        return entry.path

    def is_reachable(self, from_label: str, to_label: str) -> bool:
        entry = self.costs.get((from_label, to_label))

        if entry is None:
            return False

        return entry.reachable


def build_route_nodes(
    start_position: GridPos,
    orders: list[AutoOrder],
) -> dict[str, RouteNode]:
    nodes: dict[str, RouteNode] = {
        "START": RouteNode(
            label="START",
            pos=start_position,
            kind="START",
            order_id=None,
        )
    }

    for order in orders:
        pickup_label = f"P_{order.id}"
        delivery_label = f"D_{order.id}"

        nodes[pickup_label] = RouteNode(
            label=pickup_label,
            pos=order.store_pos,
            kind="PICKUP",
            order_id=order.id,
        )

        nodes[delivery_label] = RouteNode(
            label=delivery_label,
            pos=order.customer_pos,
            kind="DELIVERY",
            order_id=order.id,
        )

    return nodes


def build_route_cost_matrix(
    map_id: int,
    algorithm: str = "ASTAR",
) -> RouteCostMatrix:
    """
    Tạo ma trận chi phí giữa START, các điểm nhận và các điểm giao.

    Local Search sẽ dùng ma trận này để đánh giá thứ tự giao hàng mà không cần
    gọi A* lại quá nhiều lần.
    """
    map_data = load_auto_map(map_id)
    graph = AutoMapGraph(map_data)
    orders = load_orders_for_map(map_id)

    nodes = build_route_nodes(
        start_position=map_data.start_position,
        orders=orders,
    )

    matrix = RouteCostMatrix(
        map_id=map_id,
        algorithm=algorithm,
        nodes=nodes,
    )

    labels = list(nodes.keys())

    for from_label in labels:
        for to_label in labels:
            if from_label == to_label:
                continue

            from_node = nodes[from_label]
            to_node = nodes[to_label]

            result = find_auto_path(
                graph=graph,
                start=from_node.pos,
                goal=to_node.pos,
                algorithm=algorithm,
            )

            matrix.costs[(from_label, to_label)] = RouteCostEntry(
                from_label=from_label,
                to_label=to_label,
                cost=result.cost,
                steps=max(0, len(result.path) - 1),
                path=result.path,
                expanded_nodes=result.expanded_nodes,
                generated_nodes=result.generated_nodes,
                runtime_ms=result.runtime_ms,
            )

    return matrix


def print_route_cost_matrix_summary(
    map_id: int,
    algorithm: str = "ASTAR",
) -> None:
    matrix = build_route_cost_matrix(
        map_id=map_id,
        algorithm=algorithm,
    )

    labels = list(matrix.nodes.keys())

    reachable_count = 0
    unreachable_count = 0
    total_runtime = 0.0
    total_expanded = 0

    for entry in matrix.costs.values():
        if entry.reachable:
            reachable_count += 1
        else:
            unreachable_count += 1

        total_runtime += entry.runtime_ms
        total_expanded += entry.expanded_nodes

    print(f"Map {map_id} route cost matrix")
    print(f"Algorithm: {algorithm}")
    print(f"Nodes: {len(labels)} -> {labels}")
    print(f"Pairs: {len(matrix.costs)}")
    print(f"Reachable pairs: {reachable_count}")
    print(f"Unreachable pairs: {unreachable_count}")
    print(f"Total expanded nodes: {total_expanded}")
    print(f"Total runtime ms: {round(total_runtime, 4)}")

    print("Sample costs:")
    for to_label in labels[1:7]:
        cost = matrix.get_cost("START", to_label)
        print(f"- START -> {to_label}: cost={round(cost, 2)}")

    print("-" * 80)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        print_route_cost_matrix_summary(
            map_id=current_map_id,
            algorithm="ASTAR",
        )