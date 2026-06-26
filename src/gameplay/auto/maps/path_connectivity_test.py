from __future__ import annotations

import heapq
from itertools import count

from src.gameplay.auto.maps.graph_adapter import AutoMapGraph
from src.gameplay.auto.maps.tmx_loader import GridPos, load_auto_map
from src.gameplay.auto.order_factory import load_orders_for_map


def find_path_dijkstra(
    graph: AutoMapGraph,
    start: GridPos,
    goal: GridPos,
) -> tuple[list[GridPos], float]:
    if start == goal:
        return [start], 0.0

    counter = count()
    frontier: list[tuple[float, int, GridPos, list[GridPos]]] = []
    heapq.heappush(frontier, (0.0, next(counter), start, [start]))

    best_cost: dict[GridPos, float] = {start: 0.0}

    while frontier:
        current_cost, _, current_pos, path = heapq.heappop(frontier)

        if current_pos == goal:
            return path, current_cost

        if current_cost > best_cost.get(current_pos, float("inf")):
            continue

        for next_pos, step_cost in graph.get_neighbors(current_pos):
            new_cost = current_cost + step_cost

            if new_cost >= best_cost.get(next_pos, float("inf")):
                continue

            best_cost[next_pos] = new_cost
            heapq.heappush(
                frontier,
                (new_cost, next(counter), next_pos, path + [next_pos]),
            )

    return [], float("inf")


def test_map_connectivity(map_id: int) -> None:
    map_data = load_auto_map(map_id)
    graph = AutoMapGraph(map_data)
    orders = load_orders_for_map(map_id)

    print(f"Map {map_id}: {map_data.name}")
    print(f"Start: {map_data.start_position}")

    all_ok = True

    for order in orders:
        pickup_path, pickup_cost = find_path_dijkstra(
            graph=graph,
            start=map_data.start_position,
            goal=order.store_pos,
        )

        delivery_path, delivery_cost = find_path_dijkstra(
            graph=graph,
            start=order.store_pos,
            goal=order.customer_pos,
        )

        pickup_ok = bool(pickup_path)
        delivery_ok = bool(delivery_path)

        if not pickup_ok or not delivery_ok:
            all_ok = False

        print(
            f"- {order.id}: "
            f"start -> store {order.store_pos}: {'OK' if pickup_ok else 'NO PATH'} "
            f"(steps={len(pickup_path)}, cost={round(pickup_cost, 2) if pickup_ok else 'inf'}), "
            f"store -> customer {order.customer_pos}: {'OK' if delivery_ok else 'NO PATH'} "
            f"(steps={len(delivery_path)}, cost={round(delivery_cost, 2) if delivery_ok else 'inf'})"
        )

    if all_ok:
        print("Result: OK - all orders are reachable.")
    else:
        print("Result: ERROR - some orders are unreachable.")

    print("-" * 60)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        test_map_connectivity(current_map_id)