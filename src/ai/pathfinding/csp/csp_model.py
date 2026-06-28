from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from src.ai.pathfinding.local_search.route_state import (
    RouteState,
    build_default_route_actions,
    get_order_id,
    is_delivery,
    is_pickup,
    make_route_state,
)


class RouteCostProvider(Protocol):
    def get_cost(self, from_label: str, to_label: str) -> float:
        ...


@dataclass(frozen=True)
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


@dataclass
class PartialRoute:
    actions: list[str]
    waiting: set[str]
    carrying: set[str]
    delivered: set[str]
    current_label: str
    total_cost: float


def make_initial_partial_route(order_ids: Sequence[str]) -> PartialRoute:
    return PartialRoute(
        actions=[],
        waiting=set(order_ids),
        carrying=set(),
        delivered=set(),
        current_label="START",
        total_cost=0.0,
    )


def get_valid_actions(
    partial: PartialRoute,
    capacity: int,
) -> list[str]:
    # Nếu đang cầm hàng thì bắt buộc giao đúng đơn đó trước.
    if partial.carrying:
        order_id = sorted(partial.carrying)[0]
        return [f"D_{order_id}"]

    # Nếu không cầm hàng thì chọn một đơn chưa giao để nhận.
    actions: list[str] = []
    for order_id in sorted(partial.waiting):
        actions.append(f"P_{order_id}")

    return actions


def apply_action(
    partial: PartialRoute,
    action: str,
    step_cost: float,
) -> PartialRoute:
    order_id = get_order_id(action)

    waiting = set(partial.waiting)
    carrying = set(partial.carrying)
    delivered = set(partial.delivered)

    if is_pickup(action):
        waiting.remove(order_id)
        carrying.add(order_id)

    elif is_delivery(action):
        carrying.remove(order_id)
        delivered.add(order_id)

    else:
        raise ValueError(f"Unknown CSP action: {action}")

    return PartialRoute(
        actions=[*partial.actions, action],
        waiting=waiting,
        carrying=carrying,
        delivered=delivered,
        current_label=action,
        total_cost=partial.total_cost + step_cost,
    )


def has_forward_solution(
    partial: PartialRoute,
    capacity: int,
    order_count: int,
) -> bool:
    """
    Kiểm tra nhanh sau khi chọn một hành động.
    """
    if len(partial.delivered) == order_count:
        return True

    return bool(
        get_valid_actions(
            partial=partial,
            capacity=capacity,
        )
    )


def order_actions(
    actions: list[str],
    partial: PartialRoute,
    problem: CSPRouteProblem,
    strategy: str,
) -> list[str]:
    """
    Sắp xếp thứ tự thử đơn cho 3 kiểu CSP.
    """
    if strategy == "LEXICOGRAPHIC":
        return sorted(actions)

    if strategy == "NEAREST_COST":
        return sorted(
            actions,
            key=lambda action: (
                problem.cost_provider.get_cost(partial.current_label, action),
                action,
            ),
        )

    if strategy == "AC3_PRIORITY":
        return sorted(
            actions,
            key=lambda action: (
                0 if is_delivery(action) else 1,
                problem.cost_provider.get_cost(partial.current_label, action),
                action,
            ),
        )

    return actions


def run_ac3_precheck(order_ids: Sequence[str]) -> bool:
    """
    AC-3 preprocessing đơn giản cho mô hình route:

    AC-3 đơn giản: kiểm tra miền đơn hàng trước khi backtracking.
    """
    for order_id in order_ids:
        if not order_id:
            return False

    return True


def solve_csp_route(
    problem: CSPRouteProblem,
    algorithm: str,
    action_strategy: str,
    use_forward_checking: bool,
    use_ac3_precheck: bool,
    max_expanded_nodes: int,
) -> CSPRouteSearchResult:
    started_at = perf_counter()

    if use_ac3_precheck and not run_ac3_precheck(problem.order_ids):
        raise ValueError("AC-3 preprocessing failed.")

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

    order_count = len(problem.order_ids)

    def backtrack(partial: PartialRoute) -> None:
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

        if partial.total_cost >= best_cost:
            backtracks += 1
            return

        if len(partial.delivered) == order_count:
            candidate_state = make_route_state(
                actions=partial.actions,
                order_ids=problem.order_ids,
                capacity=problem.capacity,
                cost_provider=problem.cost_provider,
            )

            if candidate_state.is_valid and candidate_state.total_cost < best_cost:
                best_state = candidate_state
                best_cost = candidate_state.total_cost

            return

        actions = get_valid_actions(
            partial=partial,
            capacity=problem.capacity,
        )

        generated_nodes += len(actions)

        if not actions:
            backtracks += 1
            return

        ordered_actions = order_actions(
            actions=actions,
            partial=partial,
            problem=problem,
            strategy=action_strategy,
        )

        for action in ordered_actions:
            step_cost = problem.cost_provider.get_cost(
                partial.current_label,
                action,
            )

            if step_cost == float("inf"):
                backtracks += 1
                continue

            next_partial = apply_action(
                partial=partial,
                action=action,
                step_cost=step_cost,
            )

            if use_forward_checking and not has_forward_solution(
                partial=next_partial,
                capacity=problem.capacity,
                order_count=order_count,
            ):
                backtracks += 1
                continue

            backtrack(next_partial)

            if stopped_by_limit:
                return

    backtrack(make_initial_partial_route(problem.order_ids))

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