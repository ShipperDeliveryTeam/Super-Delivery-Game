from __future__ import annotations

import random
from time import perf_counter

from src.ai.complex_search.uncertain_search_result import UncertainSearchResult
from src.ai.complex_search.uncertainty_model import UncertaintyModel
from src.ai.local_search.route_state import (
    RouteCostProvider,
    RouteState,
    build_default_route_actions,
    generate_route_neighbors,
    make_route_state,
    random_valid_route_actions,
)


class AndOrCostProvider:
    def __init__(self, uncertainty_model: UncertaintyModel) -> None:
        self.uncertainty_model = uncertainty_model

    def get_cost(self, from_label: str, to_label: str) -> float:
        return self.uncertainty_model.get_and_or_cost(
            from_label,
            to_label,
        )


def _unique_states(states: list[RouteState]) -> list[RouteState]:
    unique: dict[tuple[str, ...], RouteState] = {}

    for state in states:
        if not state.is_valid:
            continue

        existing = unique.get(state.actions)

        if existing is None or state.total_cost < existing.total_cost:
            unique[state.actions] = state

    return list(unique.values())


def _select_best_k(
    states: list[RouteState],
    beam_width: int,
) -> list[RouteState]:
    unique_states = _unique_states(states)

    return sorted(
        unique_states,
        key=lambda state: state.total_cost,
    )[:beam_width]


def and_or_search(
    order_ids: list[str],
    capacity: int,
    uncertainty_model: UncertaintyModel,
    beam_width: int = 5,
    max_iterations: int = 100,
    seed: int = 42,
) -> UncertainSearchResult:
    """
    AND-OR Search.

    Mô phỏng tư duy:
    - OR node: AI chọn hành động tiếp theo.
    - AND node: môi trường có thể rơi vào trường hợp bình thường hoặc xấu.
    - Vì vậy thuật toán tối ưu theo worst-case cost.
    """
    started_at = perf_counter()
    rng = random.Random(seed)

    decision_provider: RouteCostProvider = AndOrCostProvider(
        uncertainty_model,
    )

    initial_states: list[RouteState] = []

    default_state = make_route_state(
        actions=build_default_route_actions(order_ids),
        order_ids=order_ids,
        capacity=capacity,
        cost_provider=decision_provider,
    )

    initial_states.append(default_state)

    while len(initial_states) < beam_width:
        random_actions = random_valid_route_actions(
            order_ids=order_ids,
            capacity=capacity,
            rng=rng,
        )

        random_state = make_route_state(
            actions=random_actions,
            order_ids=order_ids,
            capacity=capacity,
            cost_provider=decision_provider,
        )

        if random_state.is_valid:
            initial_states.append(random_state)

    beam = _select_best_k(
        states=initial_states,
        beam_width=beam_width,
    )

    best_state = beam[0]

    iterations = 0
    expanded_nodes = 0
    generated_nodes = len(initial_states)

    for _ in range(max_iterations):
        iterations += 1

        candidates: list[RouteState] = []
        candidates.extend(beam)

        for state in beam:
            expanded_nodes += 1

            neighbors = generate_route_neighbors(
                state=state,
                order_ids=order_ids,
                capacity=capacity,
                cost_provider=decision_provider,
            )

            generated_nodes += len(neighbors)
            candidates.extend(neighbors)

        next_beam = _select_best_k(
            states=candidates,
            beam_width=beam_width,
        )

        if not next_beam:
            break

        current_best = next_beam[0]

        if current_best.better_than(best_state):
            best_state = current_best
            beam = next_beam
        else:
            beam = next_beam
            break

    normal_state = make_route_state(
        actions=best_state.actions,
        order_ids=order_ids,
        capacity=capacity,
        cost_provider=uncertainty_model.matrix,
    )

    return UncertainSearchResult(
        algorithm="AND_OR_SEARCH",
        best_state=normal_state,
        decision_cost=best_state.total_cost,
        risk_mode="WORST_CASE_COST",
        iterations=iterations,
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )