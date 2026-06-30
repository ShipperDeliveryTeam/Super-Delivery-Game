from __future__ import annotations

"""Ham xu ly route don gian cho CSP."""

import random
from dataclasses import dataclass


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
    return action_label.split("_", 1)[1]


def is_pickup(action_label: str) -> bool:
    return action_label.startswith("P_")


def is_delivery(action_label: str) -> bool:
    return action_label.startswith("D_")


def build_default_route_actions(order_ids) -> tuple[str, ...]:
    actions = []
    for order_id in order_ids:
        actions.append(f"P_{order_id}")
        actions.append(f"D_{order_id}")
    return tuple(actions)


def get_order_sequence(actions) -> list[str]:
    sequence = []
    for action in actions:
        if is_pickup(action):
            sequence.append(get_order_id(action))
    return sequence


def validate_route_actions(actions, order_ids, capacity) -> tuple[bool, str]:
    sequence = get_order_sequence(actions)

    if set(sequence) != set(order_ids):
        return False, "Route does not contain all orders."

    if len(sequence) != len(order_ids):
        return False, "Route contains duplicated orders."

    expected_actions = build_default_route_actions(sequence)
    if tuple(actions) != expected_actions:
        return False, "Each order must be pickup then delivery."

    return True, ""


def get_leg_cost(cost_provider, start_label, pickup_label, delivery_label):
    if hasattr(cost_provider, "get_heuristic_cost"):
        first = cost_provider.get_heuristic_cost(start_label, pickup_label)
        second = cost_provider.get_heuristic_cost(pickup_label, delivery_label)
    else:
        first = cost_provider.get_cost(start_label, pickup_label)
        second = cost_provider.get_cost(pickup_label, delivery_label)
    return first, second


def evaluate_route(actions, order_ids, capacity, cost_provider) -> RouteEvaluation:
    is_valid, reason = validate_route_actions(actions, order_ids, capacity)
    if not is_valid:
        return RouteEvaluation(tuple(actions), float("inf"), False, reason)

    total_cost = 0.0
    current_label = "START"

    for order_id in get_order_sequence(actions):
        pickup = f"P_{order_id}"
        delivery = f"D_{order_id}"
        first, second = get_leg_cost(cost_provider, current_label, pickup, delivery)

        if first == float("inf") or second == float("inf"):
            return RouteEvaluation(tuple(actions), float("inf"), False, "No path in route.")

        total_cost += first + second
        current_label = delivery

    return RouteEvaluation(tuple(actions), total_cost, True, "")


def make_route_state(actions, order_ids, capacity, cost_provider) -> RouteState:
    evaluation = evaluate_route(actions, order_ids, capacity, cost_provider)
    return RouteState(
        actions=evaluation.actions,
        total_cost=evaluation.total_cost,
        is_valid=evaluation.is_valid,
        reason=evaluation.reason,
    )


def generate_order_swap_neighbors(state, order_ids, capacity, cost_provider) -> list[RouteState]:
    neighbors = []
    sequence = get_order_sequence(state.actions)

    for i in range(len(sequence)):
        for j in range(i + 1, len(sequence)):
            new_sequence = list(sequence)
            new_sequence[i], new_sequence[j] = new_sequence[j], new_sequence[i]
            actions = build_default_route_actions(new_sequence)
            neighbor = make_route_state(actions, order_ids, capacity, cost_provider)
            if neighbor.is_valid:
                neighbors.append(neighbor)

    return neighbors


def generate_route_neighbors(state, order_ids, capacity, cost_provider) -> list[RouteState]:
    return generate_order_swap_neighbors(state, order_ids, capacity, cost_provider)


def random_valid_route_actions(order_ids, capacity, rng: random.Random) -> tuple[str, ...]:
    sequence = list(order_ids)
    rng.shuffle(sequence)
    return build_default_route_actions(sequence)
