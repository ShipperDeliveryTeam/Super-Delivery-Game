from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from src.gameplay.auto.models import AutoOrder
from src.gameplay.auto.route_cost_matrix import RouteCostMatrix


PLAYER_TURN = "PLAYER"
OPPONENT_TURN = "OPPONENT"


class AdversarialSearchFn(Protocol):
    def __call__(
        self,
        order_ids: list[str],
        orders: list[AutoOrder],
        matrix: RouteCostMatrix,
        depth_limit: int,
    ) -> "AdversarialSearchResult":
        ...


@dataclass(frozen=True)
class AdversarialGameState:
    remaining_order_ids: tuple[str, ...]
    player_label: str
    opponent_label: str
    player_score: float
    opponent_score: float
    turn: str
    depth: int


@dataclass
class AdversarialSearchStats:
    expanded_nodes: int = 0
    generated_nodes: int = 0
    pruned_nodes: int = 0


@dataclass
class AdversarialSearchResult:
    algorithm: str
    best_order_id: str | None
    best_sequence: tuple[str, ...]
    expected_utility: float
    expanded_nodes: int
    generated_nodes: int
    pruned_nodes: int
    runtime_ms: float

    @property
    def found(self) -> bool:
        return self.best_order_id is not None


def build_initial_state(order_ids: list[str]) -> AdversarialGameState:
    return AdversarialGameState(
        remaining_order_ids=tuple(order_ids),
        player_label="START",
        opponent_label="START",
        player_score=0.0,
        opponent_score=0.0,
        turn=PLAYER_TURN,
        depth=0,
    )


def build_reward_map(orders: list[AutoOrder]) -> dict[str, float]:
    return {
        order.id: float(order.reward)
        for order in orders
    }


def calculate_order_trip_cost(
    matrix: RouteCostMatrix,
    current_label: str,
    order_id: str,
) -> float:
    pickup_label = f"P_{order_id}"
    delivery_label = f"D_{order_id}"

    return (
        matrix.get_cost(current_label, pickup_label)
        + matrix.get_cost(pickup_label, delivery_label)
    )


def calculate_order_gain(
    matrix: RouteCostMatrix,
    reward_map: dict[str, float],
    current_label: str,
    order_id: str,
) -> float:
    """
    Điểm lợi ích khi chọn một đơn.

    reward cao thì tốt.
    quãng đường/cost cao thì bị trừ.
    """
    reward = reward_map[order_id]
    trip_cost = calculate_order_trip_cost(
        matrix=matrix,
        current_label=current_label,
        order_id=order_id,
    )

    return reward - trip_cost


def is_terminal(
    state: AdversarialGameState,
    depth_limit: int,
) -> bool:
    return (
        not state.remaining_order_ids
        or state.depth >= depth_limit
    )


def evaluate_state(state: AdversarialGameState) -> float:
    """
    Utility của Player.
    Player muốn utility lớn.
    Opponent muốn utility nhỏ.
    """
    return state.player_score - state.opponent_score


def get_actions(state: AdversarialGameState) -> list[str]:
    return list(state.remaining_order_ids)


def apply_action(
    state: AdversarialGameState,
    order_id: str,
    matrix: RouteCostMatrix,
    reward_map: dict[str, float],
) -> AdversarialGameState:
    remaining = tuple(
        current_order_id
        for current_order_id in state.remaining_order_ids
        if current_order_id != order_id
    )

    if state.turn == PLAYER_TURN:
        gain = calculate_order_gain(
            matrix=matrix,
            reward_map=reward_map,
            current_label=state.player_label,
            order_id=order_id,
        )

        return AdversarialGameState(
            remaining_order_ids=remaining,
            player_label=f"D_{order_id}",
            opponent_label=state.opponent_label,
            player_score=state.player_score + gain,
            opponent_score=state.opponent_score,
            turn=OPPONENT_TURN,
            depth=state.depth + 1,
        )

    gain = calculate_order_gain(
        matrix=matrix,
        reward_map=reward_map,
        current_label=state.opponent_label,
        order_id=order_id,
    )

    return AdversarialGameState(
        remaining_order_ids=remaining,
        player_label=state.player_label,
        opponent_label=f"D_{order_id}",
        player_score=state.player_score,
        opponent_score=state.opponent_score + gain,
        turn=PLAYER_TURN,
        depth=state.depth + 1,
    )


def order_actions_by_gain(
    state: AdversarialGameState,
    actions: list[str],
    matrix: RouteCostMatrix,
    reward_map: dict[str, float],
) -> list[str]:
    """
    Sắp xếp action tốt trước để Alpha-Beta prune hiệu quả hơn.
    """
    if state.turn == PLAYER_TURN:
        current_label = state.player_label
        reverse = True
    else:
        current_label = state.opponent_label
        reverse = False

    return sorted(
        actions,
        key=lambda order_id: calculate_order_gain(
            matrix=matrix,
            reward_map=reward_map,
            current_label=current_label,
            order_id=order_id,
        ),
        reverse=reverse,
    )


def now_ms_since(started_at: float) -> float:
    return (perf_counter() - started_at) * 1000