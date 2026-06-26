from __future__ import annotations

from time import perf_counter

from src.ai.complex_search.uncertain_search_result import UncertainSearchResult
from src.ai.complex_search.uncertainty_model import UncertaintyModel
from src.ai.local_search.route_state import (
    RouteCostProvider,
    RouteState,
    get_order_id,
    is_delivery,
    is_pickup,
    make_route_state,
)


class NoObservationCostProvider:
    def __init__(self, uncertainty_model: UncertaintyModel) -> None:
        self.uncertainty_model = uncertainty_model

    def get_cost(self, from_label: str, to_label: str) -> float:
        return self.uncertainty_model.get_no_observation_cost(
            from_label,
            to_label,
        )


def _get_possible_actions(
    waiting: set[str],
    carrying: set[str],
    capacity: int,
) -> list[str]:
    actions: list[str] = []

    if len(carrying) < capacity:
        for order_id in sorted(waiting):
            actions.append(f"P_{order_id}")

    for order_id in sorted(carrying):
        actions.append(f"D_{order_id}")

    return actions


def _update_state(
    action: str,
    waiting: set[str],
    carrying: set[str],
    delivered: set[str],
) -> None:
    order_id = get_order_id(action)

    if is_pickup(action):
        waiting.remove(order_id)
        carrying.add(order_id)

    elif is_delivery(action):
        carrying.remove(order_id)
        delivered.add(order_id)


def no_observation_search(
    order_ids: list[str],
    capacity: int,
    uncertainty_model: UncertaintyModel,
) -> UncertainSearchResult:
    """
    No Observation Search.

    AI không biết rõ trap/rủi ro cụ thể nên chọn bước tiếp theo dựa trên
    chi phí kỳ vọng. Đây là cách mô phỏng belief-state đơn giản cho đồ án.
    """
    started_at = perf_counter()

    decision_provider: RouteCostProvider = NoObservationCostProvider(
        uncertainty_model,
    )

    waiting = set(order_ids)
    carrying: set[str] = set()
    delivered: set[str] = set()

    current_label = "START"
    actions: list[str] = []

    expanded_nodes = 0
    generated_nodes = 0

    while len(delivered) < len(order_ids):
        expanded_nodes += 1

        possible_actions = _get_possible_actions(
            waiting=waiting,
            carrying=carrying,
            capacity=capacity,
        )

        generated_nodes += len(possible_actions)

        if not possible_actions:
            break

        chosen_action = min(
            possible_actions,
            key=lambda action: (
                decision_provider.get_cost(current_label, action),
                action,
            ),
        )

        actions.append(chosen_action)

        _update_state(
            action=chosen_action,
            waiting=waiting,
            carrying=carrying,
            delivered=delivered,
        )

        current_label = chosen_action

    decision_state = make_route_state(
        actions=actions,
        order_ids=order_ids,
        capacity=capacity,
        cost_provider=decision_provider,
    )

    normal_state = make_route_state(
        actions=actions,
        order_ids=order_ids,
        capacity=capacity,
        cost_provider=uncertainty_model.matrix,
    )

    return UncertainSearchResult(
        algorithm="NO_OBSERVATION",
        best_state=normal_state,
        decision_cost=decision_state.total_cost,
        risk_mode="EXPECTED_COST",
        iterations=expanded_nodes,
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )