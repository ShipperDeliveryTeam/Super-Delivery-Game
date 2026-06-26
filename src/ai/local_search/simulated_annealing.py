from __future__ import annotations

import math
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
class SimulatedAnnealingResult:
    algorithm: str
    best_state: RouteState
    initial_state: RouteState
    iterations: int
    expanded_nodes: int
    generated_nodes: int
    accepted_worse_moves: int
    runtime_ms: float
    restart_count: int

    @property
    def improved(self) -> bool:
        return self.best_state.total_cost < self.initial_state.total_cost


def _build_initial_state(
    restart_index: int,
    order_ids: list[str],
    capacity: int,
    cost_provider: RouteCostProvider,
    rng: random.Random,
) -> RouteState:
    """
    Restart 0 dùng route mặc định.
    Các restart sau dùng route hợp lệ ngẫu nhiên.
    """
    if restart_index == 0:
        actions = build_default_route_actions(order_ids)
    else:
        actions = random_valid_route_actions(
            order_ids=order_ids,
            capacity=capacity,
            rng=rng,
        )

    return make_route_state(
        actions=actions,
        order_ids=order_ids,
        capacity=capacity,
        cost_provider=cost_provider,
    )


def simulated_annealing(
    order_ids: list[str],
    capacity: int,
    cost_provider: RouteCostProvider,
    initial_temperature: float = 120.0,
    cooling_rate: float = 0.985,
    min_temperature: float = 0.01,
    max_iterations: int = 1000,
    seed: int = 42,
    restart_count: int = 8,
) -> SimulatedAnnealingResult:
    """
    Simulated Annealing cho bài toán tối ưu thứ tự nhận/giao đơn.

    Bản này dùng multi-start:
    - Lần đầu chạy từ route mặc định.
    - Các lần sau chạy từ route hợp lệ ngẫu nhiên.
    - Giữ lại route tốt nhất sau tất cả restart.

    Mục tiêu:
    - Giữ đúng bản chất SA.
    - Giảm rủi ro bị kẹt ở nghiệm chưa tốt do yếu tố ngẫu nhiên.
    """
    started_at = perf_counter()
    rng = random.Random(seed)

    default_initial_state = make_route_state(
        actions=build_default_route_actions(order_ids),
        order_ids=order_ids,
        capacity=capacity,
        cost_provider=cost_provider,
    )

    global_best_state = default_initial_state

    total_iterations = 0
    total_expanded_nodes = 0
    total_generated_nodes = 1
    total_accepted_worse_moves = 0

    for restart_index in range(restart_count):
        current_state = _build_initial_state(
            restart_index=restart_index,
            order_ids=order_ids,
            capacity=capacity,
            cost_provider=cost_provider,
            rng=rng,
        )

        if current_state.better_than(global_best_state):
            global_best_state = current_state

        temperature = initial_temperature

        local_iterations = 0

        while temperature > min_temperature and local_iterations < max_iterations:
            local_iterations += 1
            total_iterations += 1
            total_expanded_nodes += 1

            neighbors = generate_route_neighbors(
                state=current_state,
                order_ids=order_ids,
                capacity=capacity,
                cost_provider=cost_provider,
            )

            total_generated_nodes += len(neighbors)

            if not neighbors:
                break

            candidate_state = rng.choice(neighbors)

            delta = candidate_state.total_cost - current_state.total_cost

            should_accept = False

            if delta <= 0:
                should_accept = True
            else:
                accept_probability = math.exp(-delta / temperature)

                if rng.random() < accept_probability:
                    should_accept = True
                    total_accepted_worse_moves += 1

            if should_accept:
                current_state = candidate_state

                if current_state.better_than(global_best_state):
                    global_best_state = current_state

            temperature *= cooling_rate

    return SimulatedAnnealingResult(
        algorithm="SIMULATED_ANNEALING",
        best_state=global_best_state,
        initial_state=default_initial_state,
        iterations=total_iterations,
        expanded_nodes=total_expanded_nodes,
        generated_nodes=total_generated_nodes,
        accepted_worse_moves=total_accepted_worse_moves,
        runtime_ms=(perf_counter() - started_at) * 1000,
        restart_count=restart_count,
    )