from __future__ import annotations

from dataclasses import dataclass

from src.ai.pathfinding.search_common import SearchResult
from src.gameplay.auto.maps.graph_adapter import AutoMapGraph
from src.gameplay.auto.maps.tmx_loader import AutoMapData, GridPos, load_auto_map
from src.gameplay.auto.models import AutoOrder
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.pathfinder_adapter import find_auto_path


@dataclass
class DeliveryStep:
    order_id: str
    action: str
    start: GridPos
    goal: GridPos
    path: list[GridPos]
    cost: float
    expanded_nodes: int
    generated_nodes: int
    runtime_ms: float


@dataclass
class DeliveryPlanResult:
    map_id: int
    algorithm: str
    total_orders: int
    completed_orders: int
    total_cost: float
    total_steps: int
    expanded_nodes: int
    generated_nodes: int
    runtime_ms: float
    steps: list[DeliveryStep]

    @property
    def success(self) -> bool:
        return self.total_orders > 0 and self.completed_orders >= self.total_orders


class AutoPlanner:
    def __init__(
        self,
        map_data: AutoMapData,
        algorithm: str,
    ) -> None:
        self.map_data = map_data
        self.algorithm = algorithm
        self.graph = AutoMapGraph(map_data)

    def _find_path(
        self,
        start: GridPos,
        goal: GridPos,
    ) -> SearchResult:
        return find_auto_path(
            graph=self.graph,
            start=start,
            goal=goal,
            algorithm=self.algorithm,
        )

    def build_sequential_delivery_plan(
        self,
        orders: list[AutoOrder],
    ) -> DeliveryPlanResult:
        """
        Planner cơ bản cho nhóm 1 và nhóm 2.

        Chiến lược:
        - Đi theo thứ tự đơn cố định từ TMX.
        - Mỗi đơn: đi tới store để nhận, sau đó đi tới customer để giao.
        - Mục tiêu bước này là kiểm tra thuật toán pathfinding chạy được đủ các đơn đang bật.
        """
        current_pos = self.map_data.start_position

        steps: list[DeliveryStep] = []

        completed_orders = 0
        total_cost = 0.0
        total_path_steps = 0
        total_expanded = 0
        total_generated = 0
        total_runtime_ms = 0.0

        for order in orders:
            pickup_result = self._find_path(
                start=current_pos,
                goal=order.store_pos,
            )

            if not pickup_result.found:
                break

            steps.append(
                DeliveryStep(
                    order_id=order.id,
                    action="PICKUP",
                    start=current_pos,
                    goal=order.store_pos,
                    path=pickup_result.path,
                    cost=pickup_result.cost,
                    expanded_nodes=pickup_result.expanded_nodes,
                    generated_nodes=pickup_result.generated_nodes,
                    runtime_ms=pickup_result.runtime_ms,
                )
            )

            current_pos = order.store_pos
            total_cost += pickup_result.cost
            total_path_steps += max(0, len(pickup_result.path) - 1)
            total_expanded += pickup_result.expanded_nodes
            total_generated += pickup_result.generated_nodes
            total_runtime_ms += pickup_result.runtime_ms

            delivery_result = self._find_path(
                start=current_pos,
                goal=order.customer_pos,
            )

            if not delivery_result.found:
                break

            steps.append(
                DeliveryStep(
                    order_id=order.id,
                    action="DELIVERY",
                    start=current_pos,
                    goal=order.customer_pos,
                    path=delivery_result.path,
                    cost=delivery_result.cost,
                    expanded_nodes=delivery_result.expanded_nodes,
                    generated_nodes=delivery_result.generated_nodes,
                    runtime_ms=delivery_result.runtime_ms,
                )
            )

            current_pos = order.customer_pos
            total_cost += delivery_result.cost
            total_path_steps += max(0, len(delivery_result.path) - 1)
            total_expanded += delivery_result.expanded_nodes
            total_generated += delivery_result.generated_nodes
            total_runtime_ms += delivery_result.runtime_ms

            completed_orders += 1

        return DeliveryPlanResult(
            map_id=self.map_data.map_id,
            algorithm=self.algorithm,
            total_orders=len(orders),
            completed_orders=completed_orders,
            total_cost=total_cost,
            total_steps=total_path_steps,
            expanded_nodes=total_expanded,
            generated_nodes=total_generated,
            runtime_ms=total_runtime_ms,
            steps=steps,
        )


def build_plan_for_map(
    map_id: int,
    algorithm: str,
) -> DeliveryPlanResult:
    map_data = load_auto_map(map_id)
    orders = load_orders_for_map(map_id)

    planner = AutoPlanner(
        map_data=map_data,
        algorithm=algorithm,
    )

    return planner.build_sequential_delivery_plan(orders)
