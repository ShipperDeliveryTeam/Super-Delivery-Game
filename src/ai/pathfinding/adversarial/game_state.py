from __future__ import annotations

"""Mô hình trạng thái cho nhóm thuật toán đối kháng.

Nhóm này coi việc chọn đơn như một trò chơi hai người: Player cố tăng điểm
của mình, Opponent cố làm giảm lợi thế đó. Minimax, Alpha-Beta và Expectimax
đều dùng chung state, hàm sinh action và hàm utility trong file này.
"""

from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from src.gameplay.auto.models import AutoOrder
from src.gameplay.auto.route_cost_matrix import RouteCostMatrix


PLAYER_TURN = "PLAYER"
OPPONENT_TURN = "OPPONENT"


class AdversarialSearchFn(Protocol):
    """Kiểu hàm chuẩn của một thuật toán adversarial search."""

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
    """Một node trong cây game đối kháng."""

    remaining_order_ids: tuple[str, ...]
    player_label: str
    opponent_label: str
    player_score: float
    opponent_score: float
    turn: str
    depth: int


@dataclass
class AdversarialSearchStats:
    """Thống kê số node để báo cáo/so sánh thuật toán."""

    expanded_nodes: int = 0
    generated_nodes: int = 0
    pruned_nodes: int = 0


@dataclass
class AdversarialSearchResult:
    """Kết quả chọn đơn tốt nhất theo thuật toán đối kháng."""

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
    """Tạo trạng thái gốc: cả hai người chơi bắt đầu từ START và chưa có điểm."""

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
    """Chuyển danh sách order thành map id -> reward để tra cứu nhanh."""

    return {
        order.id: float(order.reward)
        for order in orders
    }


def calculate_order_trip_cost(
    matrix: RouteCostMatrix,
    current_label: str,
    order_id: str,
) -> float:
    """Chi phí đi từ vị trí hiện tại tới store rồi tới house của một đơn."""

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
    """Node lá nếu hết đơn hoặc đạt giới hạn độ sâu."""

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
    """Action hợp lệ chính là các đơn còn chưa ai chọn."""

    return list(state.remaining_order_ids)


def apply_action(
    state: AdversarialGameState,
    order_id: str,
    matrix: RouteCostMatrix,
    reward_map: dict[str, float],
) -> AdversarialGameState:
    """Sinh state con sau khi Player hoặc Opponent chọn một đơn."""

    remaining = tuple(
        current_order_id
        for current_order_id in state.remaining_order_ids
        if current_order_id != order_id
    )

    if state.turn == PLAYER_TURN:
        # Player chọn đơn: cộng gain vào player_score và chuyển lượt cho Opponent.
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

    # Opponent chọn đơn: cộng gain cho đối thủ và chuyển lượt về Player.
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

    def gain_of(order_id: str) -> float:
        return calculate_order_gain(
            matrix=matrix,
            reward_map=reward_map,
            current_label=current_label,
            order_id=order_id,
        )

    return sorted(actions, key=gain_of, reverse=reverse)


def now_ms_since(started_at: float) -> float:
    return (perf_counter() - started_at) * 1000
