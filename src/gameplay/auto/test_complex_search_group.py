from __future__ import annotations

from src.ai.pathfinding.complex_search.and_or_graph import and_or_search
from src.ai.pathfinding.complex_search.no_observation import no_observation_search
from src.ai.pathfinding.complex_search.partial_observation import partial_observation_search
from src.gameplay.auto.config import get_auto_map_config
from src.gameplay.auto.complex_traps import build_trap_setup
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.maps.tmx_loader import load_auto_map
from src.gameplay.auto.route_cost_matrix import build_route_cost_matrix


def test_complex_search_group_on_map(map_id: int) -> None:
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    map_data = load_auto_map(map_id)
    trap_setup = build_trap_setup(map_data, orders, "NO_OBSERVATION")
    max_traps = len(trap_setup.traps)

    no_obs_result = no_observation_search(
        order_ids=order_ids,
        possible_traps=trap_setup.possible_traps,
        capacity=config.capacity,
        max_traps=max_traps,
    )

    partial_result = partial_observation_search(
        order_ids=order_ids,
        possible_traps=trap_setup.possible_traps,
        known_traps=trap_setup.traps[:2],
        capacity=config.capacity,
        max_iterations=100,
        max_traps=max_traps,
    )

    and_or_result = and_or_search(
        order_ids=order_ids,
        possible_traps=trap_setup.possible_traps,
        capacity=config.capacity,
        beam_width=5,
        max_iterations=100,
        seed=42,
        max_traps=max_traps,
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