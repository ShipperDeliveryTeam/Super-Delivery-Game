from __future__ import annotations

from src.ai.pathfinding.astar import astar
from src.ai.pathfinding.greedy import greedy
from src.ai.pathfinding.ida_star import ida_star
from src.gameplay.auto.maps.graph_adapter import AutoMapGraph
from src.gameplay.auto.maps.tmx_loader import load_auto_map
from src.gameplay.auto.order_factory import load_orders_for_map


def test_group_2_on_map(map_id: int) -> None:
    map_data = load_auto_map(map_id)
    graph = AutoMapGraph(map_data)
    orders = load_orders_for_map(map_id)

    first_order = orders[0]

    start = map_data.start_position
    goal = first_order.store_pos

    print(f"Map {map_id}: {map_data.name}")
    print(f"Test path: start {start} -> first pickup {goal}")

    test_cases = [
        ("GREEDY", greedy),
        ("ASTAR", astar),
        ("IDA_STAR", ida_star),
    ]

    for _, algorithm in test_cases:
        result = algorithm(
            start=start,
            goal=goal,
            get_neighbors=graph.get_neighbors,
            heuristic=graph.heuristic,
        )

        status = "OK" if result.found else "NO PATH"

        print(
            f"- {result.algorithm}: {status}, "
            f"steps={len(result.path)}, "
            f"cost={round(result.cost, 2) if result.found else 'inf'}, "
            f"expanded={result.expanded_nodes}, "
            f"generated={result.generated_nodes}, "
            f"runtime_ms={round(result.runtime_ms, 4)}"
        )

    print("-" * 60)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        test_group_2_on_map(current_map_id)