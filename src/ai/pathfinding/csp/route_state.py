from __future__ import annotations

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
    order_set = set(order_ids)
    used_actions = set()
    picked = set()
    delivered = set()
    carrying = set()

    if len(actions) != len(order_ids) * 2:
        return False, "Route length is not enough."

    for action in actions:
        if action in used_actions:
            return False, "Action is duplicated."
        used_actions.add(action)

        if "_" not in action:
            return False, "Action label is invalid."

        order_id = get_order_id(action)
        if order_id not in order_set:
            return False, "Action has unknown order id."

        if is_pickup(action):
            if order_id in picked:
                return False, "Order is picked twice."
            if len(carrying) >= capacity:
                return False, "Capacity is exceeded."

            picked.add(order_id)
            carrying.add(order_id)

        elif is_delivery(action):
            if order_id not in picked:
                return False, "Delivery appears before pickup."
            if order_id not in carrying:
                return False, "Order is not being carried."

            carrying.remove(order_id)
            delivered.add(order_id)

        else:
            return False, "Action must be pickup or delivery."

    if picked != order_set:
        return False, "Not all orders are picked."
    if delivered != order_set:
        return False, "Not all orders are delivered."
    if carrying:
        return False, "Some orders are still being carried."

    return True, ""


def get_action_cost(cost_provider, from_label, to_label):
    if hasattr(cost_provider, "get_heuristic_cost"):
        return cost_provider.get_heuristic_cost(from_label, to_label)
    return cost_provider.get_cost(from_label, to_label)


def evaluate_route(actions, order_ids, capacity, cost_provider) -> RouteEvaluation:
    is_valid, reason = validate_route_actions(actions, order_ids, capacity)
    if not is_valid:
        return RouteEvaluation(tuple(actions), float("inf"), False, reason)

    total_cost = 0.0
    current_label = "START"

    for action in actions:
        step_cost = get_action_cost(cost_provider, current_label, action)
        if step_cost == float("inf"):
            return RouteEvaluation(tuple(actions), float("inf"), False, "No path in route.")

        total_cost += step_cost
        current_label = action

    return RouteEvaluation(tuple(actions), total_cost, True, "")


def make_route_state(actions, order_ids, capacity, cost_provider) -> RouteState :
    evaluation = evaluate_route(actions, order_ids, capacity, cost_provider) # kiểm tra tính hợp lệ của các hành động và tính toán chi phí tổng thể của route
    return RouteState(
        actions=evaluation.actions,
        total_cost=evaluation.total_cost,
        is_valid=evaluation.is_valid,
        reason=evaluation.reason,
    )


def generate_order_swap_neighbors(state, order_ids, capacity, cost_provider) -> list[RouteState]:
    neighbors = []
    actions = list(state.actions)

    for i in range(len(actions)):
        for j in range(i + 1, len(actions)):
            candidate_actions = list(actions)
            candidate_actions[i], candidate_actions[j] = candidate_actions[j], candidate_actions[i]
            candidate = make_route_state(candidate_actions, order_ids, capacity, cost_provider)
            if candidate.is_valid:
                neighbors.append(candidate)

    return neighbors


def generate_route_neighbors(state, order_ids, capacity, cost_provider) -> list[RouteState]:
    return generate_order_swap_neighbors(state, order_ids, capacity, cost_provider)


def random_valid_route_actions(order_ids, capacity, rng: random.Random) -> tuple[str, ...]:
    waiting = set(order_ids)
    carrying = set()
    delivered = set()
    actions = []

    while len(delivered) < len(order_ids):
        choices = []

        if len(carrying) < capacity:
            for order_id in waiting:
                choices.append(f"P_{order_id}")

        for order_id in carrying:
            choices.append(f"D_{order_id}")

        action = rng.choice(choices)
        order_id = get_order_id(action)
        actions.append(action)

        if is_pickup(action):
            waiting.remove(order_id)
            carrying.add(order_id)
        else:
            carrying.remove(order_id)
            delivered.add(order_id)

    return tuple(actions)
