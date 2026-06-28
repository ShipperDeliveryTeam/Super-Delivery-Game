from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


class RouteCostProvider(Protocol):
    def get_cost(self, from_label: str, to_label: str) -> float:
        ...


@dataclass(frozen=True)
class RouteEvaluation:
    actions: tuple[str, ...]
    total_cost: float
    is_valid: bool
    reason: str = ""


@dataclass(frozen=True)
class RouteState:
    actions: tuple[str, ...]
    total_cost: float
    is_valid: bool
    reason: str = ""

    def better_than(self, other: "RouteState") -> bool:
        if self.is_valid and not other.is_valid:
            return True

        if not self.is_valid and other.is_valid:
            return False

        return self.total_cost < other.total_cost


def get_order_id(action_label: str) -> str:
    """
    P_O1 -> O1
    D_O1 -> O1
    """
    return action_label.split("_", 1)[1]


def is_pickup(action_label: str) -> bool:
    return action_label.startswith("P_")


def is_delivery(action_label: str) -> bool:
    return action_label.startswith("D_")


def build_default_route_actions(order_ids: Sequence[str]) -> tuple[str, ...]:
    """
    Route mặc định:
    P_O1 -> D_O1 -> P_O2 -> D_O2 -> ...
    """
    actions: list[str] = []

    for order_id in order_ids:
        actions.append(f"P_{order_id}")
        actions.append(f"D_{order_id}")

    return tuple(actions)


def validate_route_actions(
    actions: Sequence[str],
    order_ids: Sequence[str],
    capacity: int,
) -> tuple[bool, str]:
    expected = build_default_route_actions(get_order_sequence(actions))

    if tuple(actions) != expected:
        return False, "Route must pickup one order and deliver it immediately."

    if set(get_order_sequence(actions)) != set(order_ids):
        return False, "Route does not contain all orders."

    if len(get_order_sequence(actions)) != len(order_ids):
        return False, "Route contains duplicated orders."

    return True, ""


def get_order_sequence(actions: Sequence[str]) -> list[str]:
    sequence: list[str] = []
    for action in actions:
        if is_pickup(action):
            sequence.append(get_order_id(action))
    return sequence


def evaluate_route(
    actions: Sequence[str],
    order_ids: Sequence[str],
    capacity: int,
    cost_provider: RouteCostProvider,
) -> RouteEvaluation:
    is_valid, reason = validate_route_actions(
        actions=actions,
        order_ids=order_ids,
        capacity=capacity,
    )

    if not is_valid:
        return RouteEvaluation(tuple(actions), float("inf"), False, reason)

    total_cost = 0.0
    current_label = "START"

    # h(n) = START -> store -> house -> store -> house ...
    for order_id in get_order_sequence(actions):
        pickup = f"P_{order_id}"
        delivery = f"D_{order_id}"

        if hasattr(cost_provider, "get_heuristic_cost"):
            first_cost = cost_provider.get_heuristic_cost(current_label, pickup)
            second_cost = cost_provider.get_heuristic_cost(pickup, delivery)
        else:
            first_cost = cost_provider.get_cost(current_label, pickup)
            second_cost = cost_provider.get_cost(pickup, delivery)

        if first_cost == float("inf") or second_cost == float("inf"):
            return RouteEvaluation(tuple(actions), float("inf"), False, "No path in route.")

        total_cost += first_cost + second_cost
        current_label = delivery

    return RouteEvaluation(tuple(actions), total_cost, True, "")


def make_route_state(
    actions: Sequence[str],
    order_ids: Sequence[str],
    capacity: int,
    cost_provider: RouteCostProvider,
) -> RouteState:
    evaluation = evaluate_route(
        actions=actions,
        order_ids=order_ids,
        capacity=capacity,
        cost_provider=cost_provider,
    )

    return RouteState(
        actions=evaluation.actions,
        total_cost=evaluation.total_cost,
        is_valid=evaluation.is_valid,
        reason=evaluation.reason,
    )


def generate_order_swap_neighbors(
    state: RouteState,
    order_ids: Sequence[str],
    capacity: int,
    cost_provider: RouteCostProvider,
) -> list[RouteState]:
    neighbors: list[RouteState] = []
    order_sequence = get_order_sequence(state.actions)

    for i in range(len(order_sequence)):
        for j in range(i + 1, len(order_sequence)):
            candidate_sequence = order_sequence.copy()
            candidate_sequence[i], candidate_sequence[j] = candidate_sequence[j], candidate_sequence[i]
            candidate_actions = build_default_route_actions(candidate_sequence)
            candidate_state = make_route_state(candidate_actions, order_ids, capacity, cost_provider)
            if candidate_state.is_valid:
                neighbors.append(candidate_state)

    return neighbors


def generate_route_neighbors(
    state: RouteState,
    order_ids: Sequence[str],
    capacity: int,
    cost_provider: RouteCostProvider,
) -> list[RouteState]:
    return generate_order_swap_neighbors(state, order_ids, capacity, cost_provider)

def random_valid_route_actions(
    order_ids: Sequence[str],
    capacity: int,
    rng: random.Random,
) -> tuple[str, ...]:
    sequence = list(order_ids)
    rng.shuffle(sequence)
    return build_default_route_actions(sequence)
