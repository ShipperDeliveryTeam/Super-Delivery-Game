from __future__ import annotations

from src.ai.pathfinding.csp.ac3_backtracking import ac3_backtracking_search
from src.ai.pathfinding.csp.backtracking import backtracking_search
from src.ai.pathfinding.csp.forward_checking import forward_checking_search
from src.gameplay.auto.config import get_auto_map_config
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.route_cost_matrix import build_route_cost_matrix


def test_csp_group_on_map(map_id: int) -> None:
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    matrix = build_route_cost_matrix(
        map_id=map_id,
        algorithm="ASTAR",
    )

    results = [
        backtracking_search(
            order_ids=order_ids,
            capacity=config.capacity,
            cost_provider=matrix,
            max_expanded_nodes=10000,
        ),
        forward_checking_search(
            order_ids=order_ids,
            capacity=config.capacity,
            cost_provider=matrix,
            max_expanded_nodes=15000,
        ),
        ac3_backtracking_search(
            order_ids=order_ids,
            capacity=config.capacity,
            cost_provider=matrix,
            max_expanded_nodes=20000,
        ),
    ]

    ranked_results = sorted(
        results,
        key=lambda result: result.best_state.total_cost,
    )

    print(f"Map {map_id} - Group 5: CSP / Constraint Satisfaction")
    print(f"Capacity: {config.capacity}")

    for rank, result in enumerate(ranked_results, start=1):
        print(
            f"#{rank} {result.algorithm}: "
            f"initial={round(result.initial_state.total_cost, 2)}, "
            f"best={round(result.best_state.total_cost, 2)}, "
            f"improved={result.improved}, "
            f"iterations={result.iterations}, "
            f"expanded={result.expanded_nodes}, "
            f"generated={result.generated_nodes}, "
            f"backtracks={result.backtracks}, "
            f"stopped_by_limit={result.stopped_by_limit}, "
            f"runtime_ms={round(result.runtime_ms, 4)}"
        )

        print(f"   Best actions: {result.best_state.actions}")

    print("-" * 100)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        test_csp_group_on_map(current_map_id)