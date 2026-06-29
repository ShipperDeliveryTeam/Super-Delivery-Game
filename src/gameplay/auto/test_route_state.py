from __future__ import annotations

import random

from src.ai.pathfinding.local_search.route_state import (
    build_default_route_actions,
    generate_route_neighbors,
    make_route_state,
    random_valid_route_actions,
)
from src.gameplay.auto.config import get_auto_map_config
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.route_cost_matrix import build_route_cost_matrix


def test_route_state_on_map(map_id: int) -> None:
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    matrix = build_route_cost_matrix(
        map_id=map_id,
        algorithm="ASTAR",
    )

    default_actions = build_default_route_actions(order_ids)

    default_state = make_route_state(
        actions=default_actions,
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
    )

    neighbors = generate_route_neighbors(
        state=default_state,
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
    )

    best_neighbor = min(
        neighbors,
        key=lambda state: state.total_cost,
        default=default_state,
    )

    rng = random.Random(42)

    random_actions = random_valid_route_actions(
        order_ids=order_ids,
        capacity=config.capacity,
        rng=rng,
    )

    random_state = make_route_state(
        actions=random_actions,
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
    )

    print(f"Map {map_id}")
    print(f"Capacity: {config.capacity}")
    print(f"Default route valid: {default_state.is_valid}")
    print(f"Default route cost: {round(default_state.total_cost, 2)}")
    print(f"Swap neighbors: {len(neighbors)}")
    print(f"Best neighbor cost: {round(best_neighbor.total_cost, 2)}")
    print(f"Random route valid: {random_state.is_valid}")
    print(f"Random route cost: {round(random_state.total_cost, 2)}")
    print(f"Default actions: {default_state.actions}")
    print(f"Best neighbor actions: {best_neighbor.actions}")
    print("-" * 80)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        test_route_state_on_map(current_map_id)