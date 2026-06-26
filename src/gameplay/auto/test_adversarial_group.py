from __future__ import annotations

from src.ai.adversarial.alpha_beta import alpha_beta_search
from src.ai.adversarial.expectimax import expectimax_search
from src.ai.adversarial.minimax import minimax_search
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.route_cost_matrix import build_route_cost_matrix


def test_adversarial_group_on_map(map_id: int) -> None:
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    matrix = build_route_cost_matrix(
        map_id=map_id,
        algorithm="ASTAR",
    )

    depth_limit = len(order_ids)

    results = [
        minimax_search(
            order_ids=order_ids,
            orders=orders,
            matrix=matrix,
            depth_limit=depth_limit,
        ),
        alpha_beta_search(
            order_ids=order_ids,
            orders=orders,
            matrix=matrix,
            depth_limit=depth_limit,
        ),
        expectimax_search(
            order_ids=order_ids,
            orders=orders,
            matrix=matrix,
            depth_limit=depth_limit,
        ),
    ]

    ranked_results = sorted(
        results,
        key=lambda result: result.expected_utility,
        reverse=True,
    )

    print(f"Map {map_id} - Group 6: Adversarial Search")
    print(f"Depth limit: {depth_limit}")

    for rank, result in enumerate(ranked_results, start=1):
        print(
            f"#{rank} {result.algorithm}: "
            f"best_order={result.best_order_id}, "
            f"utility={round(result.expected_utility, 2)}, "
            f"expanded={result.expanded_nodes}, "
            f"generated={result.generated_nodes}, "
            f"pruned={result.pruned_nodes}, "
            f"runtime_ms={round(result.runtime_ms, 4)}"
        )

        print(f"   Best sequence: {result.best_sequence}")

    print("-" * 100)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        test_adversarial_group_on_map(current_map_id)