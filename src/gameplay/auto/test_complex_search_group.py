from __future__ import annotations

from src.ai.complex_search.and_or_graph import and_or_search
from src.ai.complex_search.no_observation import no_observation_search
from src.ai.complex_search.partial_observation import partial_observation_search
from src.ai.complex_search.uncertainty_model import UncertaintyModel
from src.gameplay.auto.config import get_auto_map_config
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.route_cost_matrix import build_route_cost_matrix


def test_complex_search_group_on_map(map_id: int) -> None:
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    matrix = build_route_cost_matrix(
        map_id=map_id,
        algorithm="ASTAR",
    )

    uncertainty_model = UncertaintyModel(matrix)

    no_obs_result = no_observation_search(
        order_ids=order_ids,
        capacity=config.capacity,
        uncertainty_model=uncertainty_model,
    )

    partial_result = partial_observation_search(
        order_ids=order_ids,
        capacity=config.capacity,
        uncertainty_model=uncertainty_model,
        max_iterations=100,
    )

    and_or_result = and_or_search(
        order_ids=order_ids,
        capacity=config.capacity,
        uncertainty_model=uncertainty_model,
        beam_width=5,
        max_iterations=100,
        seed=42,
    )

    results = [
        no_obs_result,
        partial_result,
        and_or_result,
    ]

    ranked_results = sorted(
        results,
        key=lambda result: result.normal_cost,
    )

    print(f"Map {map_id} - Group 4: Complex / Uncertain Search")
    print(f"Capacity: {config.capacity}")

    for rank, result in enumerate(ranked_results, start=1):
        print(
            f"#{rank} {result.algorithm}: "
            f"normal_cost={round(result.normal_cost, 2)}, "
            f"decision_cost={round(result.decision_cost, 2)}, "
            f"risk_mode={result.risk_mode}, "
            f"iterations={result.iterations}, "
            f"expanded={result.expanded_nodes}, "
            f"generated={result.generated_nodes}, "
            f"runtime_ms={round(result.runtime_ms, 4)}"
        )

        print(f"   Best actions: {result.actions}")

    print("-" * 100)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        test_complex_search_group_on_map(current_map_id)