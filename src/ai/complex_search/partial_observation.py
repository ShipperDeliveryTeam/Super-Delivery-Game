from __future__ import annotations

from time import perf_counter

from src.ai.complex_search.uncertain_search_result import UncertainSearchResult
from src.ai.complex_search.uncertainty_model import UncertaintyModel
from src.ai.local_search.route_state import (
    RouteCostProvider,
    build_default_route_actions,
    generate_route_neighbors,
    make_route_state,
)


class PartialObservationCostProvider:
    def __init__(self, uncertainty_model: UncertaintyModel) -> None:
        self.uncertainty_model = uncertainty_model

    def get_cost(self, from_label: str, to_label: str) -> float:
        return self.uncertainty_model.get_partial_observation_cost(
            from_label,
            to_label,
        )


def partial_observation_search(
    order_ids: list[str],
    capacity: int,
    uncertainty_model: UncertaintyModel,
    max_iterations: int = 100,
) -> UncertainSearchResult:
    """
    Partial Observation Search.

    AI biết một phần môi trường nên chi phí rủi ro được giảm.
    Sau đó dùng cải thiện cục bộ để tìm thứ tự nhận/giao tốt hơn.
    """
    started_at = perf_counter()

    decision_provider: RouteCostProvider = PartialObservationCostProvider(
        uncertainty_model,
    )

    initial_actions = build_default_route_actions(order_ids)

    current_state = make_route_state(
        actions=initial_actions,
        order_ids=order_ids,
        capacity=capacity,
        cost_provider=decision_provider,
    )

    best_state = current_state

    iterations = 0
    expanded_nodes = 0
    generated_nodes = 1

    for _ in range(max_iterations):
        iterations += 1
        expanded_nodes += 1

        neighbors = generate_route_neighbors(
            state=current_state,
            order_ids=order_ids,
            capacity=capacity,
            cost_provider=decision_provider,
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

    normal_state = make_route_state(
        actions=best_state.actions,
        order_ids=order_ids,
        capacity=capacity,
        cost_provider=uncertainty_model.matrix,
    )

    return UncertainSearchResult(
        algorithm="PARTIAL_OBSERVATION",
        best_state=normal_state,
        decision_cost=best_state.total_cost,
        risk_mode="PARTIAL_RISK_COST",
        iterations=iterations,
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )