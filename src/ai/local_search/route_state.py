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
    expected_actions = {f"P_{order_id}" for order_id in order_ids}
    expected_actions.update({f"D_{order_id}" for order_id in order_ids})

    if set(actions) != expected_actions:
        return False, "Route does not contain exactly all pickup/delivery actions."

    if len(actions) != len(expected_actions):
        return False, "Route contains duplicated actions."

    picked: set[str] = set()
    delivered: set[str] = set()
    carrying: set[str] = set()

    for action in actions:
        order_id = get_order_id(action)

        if is_pickup(action):
            if order_id in picked:
                return False, f"Order {order_id} is picked more than once."

            if len(carrying) >= capacity:
                return False, f"Capacity exceeded before picking {order_id}."

            picked.add(order_id)
            carrying.add(order_id)

        elif is_delivery(action):
            if order_id not in picked:
                return False, f"Order {order_id} is delivered before pickup."

            if order_id in delivered:
                return False, f"Order {order_id} is delivered more than once."

            if order_id not in carrying:
                return False, f"Order {order_id} is not currently carried."

            carrying.remove(order_id)
            delivered.add(order_id)

        else:
            return False, f"Unknown action label: {action}"

    if len(delivered) != len(order_ids):
        return False, "Not all orders are delivered."

    return True, ""


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
        return RouteEvaluation(
            actions=tuple(actions),
            total_cost=float("inf"),
            is_valid=False,
            reason=reason,
        )

    total_cost = 0.0
    current_label = "START"

    for action in actions:
        step_cost = cost_provider.get_cost(current_label, action)

        if step_cost == float("inf"):
            return RouteEvaluation(
                actions=tuple(actions),
                total_cost=float("inf"),
                is_valid=False,
                reason=f"No path from {current_label} to {action}.",
            )

        total_cost += step_cost
        current_label = action

    return RouteEvaluation(
        actions=tuple(actions),
        total_cost=total_cost,
        is_valid=True,
        reason="",
    )


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


def generate_swap_neighbors(
    state: RouteState,
    order_ids: Sequence[str],
    capacity: int,
    cost_provider: RouteCostProvider,
) -> list[RouteState]:
    """
    Tạo láng giềng bằng cách đổi chỗ 2 hành động.
    Chỉ giữ các route hợp lệ.
    """
    neighbors: list[RouteState] = []
    actions = list(state.actions)

    for i in range(len(actions)):
        for j in range(i + 1, len(actions)):
            candidate = actions.copy()
            candidate[i], candidate[j] = candidate[j], candidate[i]

            candidate_state = make_route_state(
                actions=candidate,
                order_ids=order_ids,
                capacity=capacity,
                cost_provider=cost_provider,
            )

            if candidate_state.is_valid:
                neighbors.append(candidate_state)

    return neighbors


def random_valid_route_actions(
    order_ids: Sequence[str],
    capacity: int,
    rng: random.Random,
) -> tuple[str, ...]:
    waiting = set(order_ids)
    carrying: set[str] = set()
    delivered: set[str] = set()
    actions: list[str] = []

    while len(delivered) < len(order_ids):
        possible_actions: list[str] = []

        if len(carrying) < capacity:
            for order_id in waiting:
                possible_actions.append(f"P_{order_id}")

        for order_id in sorted(carrying):
            possible_actions.append(f"D_{order_id}")

        if not possible_actions:
            break

        chosen_action = rng.choice(possible_actions)
        chosen_order_id = get_order_id(chosen_action)

        actions.append(chosen_action)

        if is_pickup(chosen_action):
            waiting.remove(chosen_order_id)
            carrying.add(chosen_order_id)
        else:
            carrying.remove(chosen_order_id)
            delivered.add(chosen_order_id)

    return tuple(actions)


def mutate_route_by_swap(
    actions: Sequence[str],
    order_ids: Sequence[str],
    capacity: int,
    rng: random.Random,
    max_attempts: int = 100,
) -> tuple[str, ...]:
    actions_list = list(actions)

    for _ in range(max_attempts):
        candidate = actions_list.copy()
        i, j = rng.sample(range(len(candidate)), 2)
        candidate[i], candidate[j] = candidate[j], candidate[i]

        is_valid, _ = validate_route_actions(
            actions=candidate,
            order_ids=order_ids,
            capacity=capacity,
        )

        if is_valid:
            return tuple(candidate)

    return tuple(actions)

def generate_order_swap_neighbors(
    state: RouteState,
    order_ids: Sequence[str],
    capacity: int,
    cost_provider: RouteCostProvider,
) -> list[RouteState]:
    """
    Tạo láng giềng bằng cách đổi thứ tự nguyên cặp đơn:
    P_Oi, D_Oi <-> P_Oj, D_Oj

    Cách này đặc biệt quan trọng với Map 1 vì capacity = 1.
    """
    neighbors: list[RouteState] = []

    order_sequence: list[str] = []

    for action in state.actions:
        if is_pickup(action):
            order_sequence.append(get_order_id(action))

    for i in range(len(order_sequence)):
        for j in range(i + 1, len(order_sequence)):
            candidate_sequence = order_sequence.copy()
            candidate_sequence[i], candidate_sequence[j] = (
                candidate_sequence[j],
                candidate_sequence[i],
            )

            candidate_actions = build_default_route_actions(candidate_sequence)

            candidate_state = make_route_state(
                actions=candidate_actions,
                order_ids=order_ids,
                capacity=capacity,
                cost_provider=cost_provider,
            )

            if candidate_state.is_valid:
                neighbors.append(candidate_state)

    return neighbors


def generate_route_neighbors(
    state: RouteState,
    order_ids: Sequence[str],
    capacity: int,
    cost_provider: RouteCostProvider,
) -> list[RouteState]:
    """
    Gom nhiều kiểu tạo láng giềng:
    - đổi từng action hợp lệ
    - đổi nguyên cặp pickup/delivery của đơn

    Dùng hàm này cho Hill Climbing, Local Beam và Simulated Annealing.
    """
    neighbors: list[RouteState] = []

    neighbors.extend(
        generate_swap_neighbors(
            state=state,
            order_ids=order_ids,
            capacity=capacity,
            cost_provider=cost_provider,
        )
    )

    neighbors.extend(
        generate_order_swap_neighbors(
            state=state,
            order_ids=order_ids,
            capacity=capacity,
            cost_provider=cost_provider,
        )
    )

    unique_neighbors: dict[tuple[str, ...], RouteState] = {}

    for neighbor in neighbors:
        unique_neighbors[neighbor.actions] = neighbor

    return list(unique_neighbors.values())