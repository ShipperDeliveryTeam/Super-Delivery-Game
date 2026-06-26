from __future__ import annotations

from src.ai.local_search.hill_climbing import hill_climbing
from src.ai.local_search.local_beam import local_beam_search
from src.ai.local_search.simulated_annealing import simulated_annealing
from src.gameplay.auto.config import get_auto_map_config
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.route_cost_matrix import build_route_cost_matrix


def test_local_search_group_on_map(map_id: int) -> None:
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    matrix = build_route_cost_matrix(
        map_id=map_id,
        algorithm="ASTAR",
    )

    hill_result = hill_climbing(
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
        max_iterations=100,
    )

    beam_result = local_beam_search(
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
        beam_width=5,
        max_iterations=100,
        seed=42,
    )

    sa_result = simulated_annealing(
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
        initial_temperature=120.0,
        cooling_rate=0.985,
        min_temperature=0.01,
        max_iterations=1000,
        seed=42,
        restart_count=8,
    )

    rows = [
        (
            "HILL_CLIMBING",
            hill_result.initial_state.total_cost,
            hill_result.best_state.total_cost,
            hill_result.improved,
            hill_result.iterations,
            hill_result.expanded_nodes,
            hill_result.generated_nodes,
            hill_result.runtime_ms,
            hill_result.best_state.actions,
        ),
        (
            "LOCAL_BEAM",
            beam_result.initial_best_cost,
            beam_result.best_state.total_cost,
            beam_result.improved,
            beam_result.iterations,
            beam_result.expanded_nodes,
            beam_result.generated_nodes,
            beam_result.runtime_ms,
            beam_result.best_state.actions,
        ),
        (
            "SIMULATED_ANNEALING",
            sa_result.initial_state.total_cost,
            sa_result.best_state.total_cost,
            sa_result.improved,
            sa_result.iterations,
            sa_result.expanded_nodes,
            sa_result.generated_nodes,
            sa_result.runtime_ms,
            sa_result.best_state.actions,
        ),
    ]

    ranked_rows = sorted(rows, key=lambda row: row[2])

    print(f"Map {map_id} - Group 3: Local Search")
    print(f"Capacity: {config.capacity}")

    for rank, row in enumerate(ranked_rows, start=1):
        (
            algorithm,
            initial_cost,
            best_cost,
            improved,
            iterations,
            expanded_nodes,
            generated_nodes,
            runtime_ms,
            best_actions,
        ) = row

        print(
            f"#{rank} {algorithm}: "
            f"initial={round(initial_cost, 2)}, "
            f"best={round(best_cost, 2)}, "
            f"improved={improved}, "
            f"iterations={iterations}, "
            f"expanded={expanded_nodes}, "
            f"generated={generated_nodes}, "
            f"runtime_ms={round(runtime_ms, 4)}"
        )

        print(f"   Best actions: {best_actions}")

    print("-" * 100)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        test_local_search_group_on_map(current_map_id)