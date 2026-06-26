from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from src.ai.local_search.route_state import (
    RouteCostProvider,
    RouteState,
    build_default_route_actions,
    generate_route_neighbors,
    make_route_state,
)


@dataclass
class LocalSearchResult:
    algorithm: str
    best_state: RouteState
    initial_state: RouteState
    iterations: int
    expanded_nodes: int
    generated_nodes: int
    runtime_ms: float

    @property
    def improved(self) -> bool:
        return self.best_state.total_cost < self.initial_state.total_cost


def hill_climbing(
    order_ids: list[str],
    capacity: int,
    cost_provider: RouteCostProvider,
    max_iterations: int = 100,
) -> LocalSearchResult:
    started_at = perf_counter()

    initial_actions = build_default_route_actions(order_ids)

    current_state = make_route_state(
        actions=initial_actions,
        order_ids=order_ids,
        capacity=capacity,
        cost_provider=cost_provider,
    )

    best_state = current_state

    expanded_nodes = 0
    generated_nodes = 1
    iterations = 0

    for _ in range(max_iterations):
        iterations += 1
        expanded_nodes += 1

        neighbors = generate_route_neighbors(
            state=current_state,
            order_ids=order_ids,
            capacity=capacity,
            cost_provider=cost_provider,
        )

        generated_nodes += len(neighbors)

        if not neighbors:
            break

        best_neighbor = min(
            neighbors,
            key=lambda state: state.total_cost,
        )

        if not best_neighbor.better_than(current_state):
            break

        current_state = best_neighbor

        if current_state.better_than(best_state):
            best_state = current_state

    return LocalSearchResult(
        algorithm="HILL_CLIMBING",
        best_state=best_state,
        initial_state=make_route_state(
            actions=initial_actions,
            order_ids=order_ids,
            capacity=capacity,
            cost_provider=cost_provider,
        ),
        iterations=iterations,
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )