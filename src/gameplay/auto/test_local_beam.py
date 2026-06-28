from __future__ import annotations

from src.gameplay.auto.delivery_search import delivery_search
from src.gameplay.auto.maps.tmx_loader import load_auto_map
from src.gameplay.auto.order_factory import load_orders_for_map


def test_local_search_group_on_map(map_id: int) -> None:
    map_data = load_auto_map(map_id)
    orders = load_orders_for_map(map_id)

    print(f"Map {map_id} - Group 3: Local Search Pathfinding")
    for algorithm in ("SIMPLE_HILL", "STEEPEST_HILL", "LOCAL_BEAM"):
        result = delivery_search(map_data, orders, algorithm)
        completed = sum(1 for action in result.actions if action.startswith("D_"))
        print(
            f"{algorithm}: completed={completed}/{len(orders)}, "
            f"cost={round(result.cost, 2)}, expanded={result.expanded_nodes}"
        )
    print("-" * 80)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        test_local_search_group_on_map(current_map_id)
