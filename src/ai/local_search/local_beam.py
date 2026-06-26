from __future__ import annotations

import random
from dataclasses import dataclass
from time import perf_counter

from src.ai.local_search.route_state import (
    RouteCostProvider,
    RouteState,
    build_default_route_actions,
    generate_route_neighbors,
    make_route_state,
    random_valid_route_actions,
)


@dataclass
class LocalBeamResult:
    algorithm: str
    best_state: RouteState
    initial_states: list[RouteState]
    iterations: int
    expanded_nodes: int
    generated_nodes: int
    runtime_ms: float

    @property
    def initial_best_cost(self) -> float:
        return min(state.total_cost for state in self.initial_states)

    @property
    def improved(self) -> bool:
        return self.best_state.total_cost < self.initial_best_cost


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


def local_beam_search(
    order_ids: list[str],
    capacity: int,
    cost_provider: RouteCostProvider,
    beam_width: int = 5,
    max_iterations: int = 100,
    seed: int = 42,
) -> LocalBeamResult:
    """
    Local Beam Search cho bài toán tối ưu thứ tự nhận/giao đơn.

    Ý tưởng:
    - Không chỉ giữ 1 route hiện tại như Hill Climbing.
    - Giữ k route tốt nhất cùng lúc.
    - Mỗi vòng sinh láng giềng từ cả k route.
    - Chọn lại k route tốt nhất để tiếp tục.
    """
    started_at = perf_counter()
    rng = random.Random(seed)

    initial_states: list[RouteState] = []

    default_actions = build_default_route_actions(order_ids)

    default_state = make_route_state(
        actions=default_actions,
        order_ids=order_ids,
        capacity=capacity,
        cost_provider=cost_provider,
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
            cost_provider=cost_provider,
        )

        if random_state.is_valid:
            initial_states.append(random_state)

    beam = _select_best_k(
        states=initial_states,
        beam_width=beam_width,
    )

    best_state = beam[0]

    expanded_nodes = 0
    generated_nodes = len(initial_states)
    iterations = 0

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
                cost_provider=cost_provider,
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
            # Không còn route tốt hơn nữa thì dừng.
            beam = next_beam
            break

    return LocalBeamResult(
        algorithm="LOCAL_BEAM",
        best_state=best_state,
        initial_states=initial_states,
        iterations=iterations,
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )