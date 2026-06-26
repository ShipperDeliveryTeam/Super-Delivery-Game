from __future__ import annotations

from src.ai.local_search.hill_climbing import hill_climbing
from src.gameplay.auto.config import get_auto_map_config
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.route_cost_matrix import build_route_cost_matrix


def test_hill_climbing_on_map(map_id: int) -> None:
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    matrix = build_route_cost_matrix(
        map_id=map_id,
        algorithm="ASTAR",
    )

    result = hill_climbing(
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
    )

    print(f"Map {map_id}")
    print(f"Capacity: {config.capacity}")
    print(f"Initial cost: {round(result.initial_state.total_cost, 2)}")
    print(f"Best cost: {round(result.best_state.total_cost, 2)}")
    print(f"Improved: {result.improved}")
    print(f"Iterations: {result.iterations}")
    print(f"Expanded: {result.expanded_nodes}")
    print(f"Generated: {result.generated_nodes}")
    print(f"Runtime ms: {round(result.runtime_ms, 4)}")
    print(f"Best actions: {result.best_state.actions}")
    print("-" * 80)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        test_hill_climbing_on_map(current_map_id)