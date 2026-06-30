from __future__ import annotations

"""CSP route solver ban don gian.

Bai toan: sap xep thu tu don hang. Moi don luon di theo cap:
P_Ox -> D_Ox. Vi vay backtracking chi can chon thu tu cac order_id.
"""

from dataclasses import dataclass
from time import perf_counter

from src.ai.pathfinding.csp.route_state import (
    RouteState,
    build_default_route_actions,
    make_route_state,
)


class RouteCostProvider:
    def get_cost(self, from_label: str, to_label: str) -> float:
        raise NotImplementedError


@dataclass
class CSPRouteProblem:
    order_ids: list[str]
    capacity: int
    cost_provider: RouteCostProvider


@dataclass
class CSPRouteSearchResult:
    algorithm: str
    best_state: RouteState
    initial_state: RouteState
    iterations: int
    expanded_nodes: int
    generated_nodes: int
    backtracks: int
    runtime_ms: float
    stopped_by_limit: bool

    @property
    def improved(self) -> bool:
        return self.best_state.total_cost < self.initial_state.total_cost


def route_cost_for_order(cost_provider, current_label: str, order_id: str) -> float:
    pickup = f"P_{order_id}"
    delivery = f"D_{order_id}"
    first = cost_provider.get_cost(current_label, pickup)
    second = cost_provider.get_cost(pickup, delivery)
    return first + second


def build_actions_from_order_sequence(order_sequence) -> tuple[str, ...]:
    actions = []
    for order_id in order_sequence:
        actions.append(f"P_{order_id}")
        actions.append(f"D_{order_id}")
    return tuple(actions)


def ac3_input_ok(order_ids) -> bool:
    """AC-3 ban don gian: order id phai co va khong trung."""

    seen = set()
    for order_id in order_ids:
        if not order_id or order_id in seen:
            return False
        seen.add(order_id)
    return True


def sort_next_orders(order_ids, current_label, cost_provider, strategy):
    order_ids = list(order_ids)

    if strategy == "LEXICOGRAPHIC":
        return sorted(order_ids)

    def cost_key(order_id):
        return route_cost_for_order(cost_provider, current_label, order_id), order_id

    return sorted(order_ids, key=cost_key)


def solve_csp_route(
    problem: CSPRouteProblem,
    algorithm: str,
    action_strategy: str,
    use_forward_checking: bool,
    use_ac3_precheck: bool,
    max_expanded_nodes: int,
) -> CSPRouteSearchResult:
    started_at = perf_counter()

    if use_ac3_precheck and not ac3_input_ok(problem.order_ids):
        raise ValueError("AC3 precheck failed.")

    initial_actions = build_default_route_actions(problem.order_ids)
    initial_state = make_route_state(
        actions=initial_actions,
        order_ids=problem.order_ids,
        capacity=problem.capacity,
        cost_provider=problem.cost_provider,
    )

    best_state = initial_state
    best_cost = initial_state.total_cost

    iterations = 0
    expanded_nodes = 0
    generated_nodes = 1
    backtracks = 0
    stopped_by_limit = False

    def backtrack(order_sequence, remaining_orders, current_label, current_cost):
        nonlocal best_state
        nonlocal best_cost
        nonlocal iterations
        nonlocal expanded_nodes
        nonlocal generated_nodes
        nonlocal backtracks
        nonlocal stopped_by_limit

        if expanded_nodes >= max_expanded_nodes:
            stopped_by_limit = True
            return

        iterations += 1
        expanded_nodes += 1

        if current_cost >= best_cost:
            backtracks += 1
            return

        if not remaining_orders:
            actions = build_actions_from_order_sequence(order_sequence)
            candidate = make_route_state(
                actions=actions,
                order_ids=problem.order_ids,
                capacity=problem.capacity,
                cost_provider=problem.cost_provider,
            )

            if candidate.is_valid and candidate.total_cost < best_cost:
                best_state = candidate
                best_cost = candidate.total_cost
            return

        next_orders = sort_next_orders(
            remaining_orders,
            current_label,
            problem.cost_provider,
            action_strategy,
        )
        generated_nodes += len(next_orders)

        for order_id in next_orders:
            step_cost = route_cost_for_order(problem.cost_provider, current_label, order_id)

            if step_cost == float("inf"):
                backtracks += 1
                continue

            new_cost = current_cost + step_cost
            if use_forward_checking and new_cost >= best_cost:
                backtracks += 1
                continue

            new_remaining = [item for item in remaining_orders if item != order_id]
            backtrack(
                order_sequence=[*order_sequence, order_id],
                remaining_orders=new_remaining,
                current_label=f"D_{order_id}",
                current_cost=new_cost,
            )

            if stopped_by_limit:
                return

    backtrack(
        order_sequence=[],
        remaining_orders=list(problem.order_ids),
        current_label="START",
        current_cost=0.0,
    )

    return CSPRouteSearchResult(
        algorithm=algorithm,
        best_state=best_state,
        initial_state=initial_state,
        iterations=iterations,
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        backtracks=backtracks,
        runtime_ms=(perf_counter() - started_at) * 1000,
        stopped_by_limit=stopped_by_limit,
    )
