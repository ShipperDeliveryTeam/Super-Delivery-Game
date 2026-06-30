from __future__ import annotations

"""Minimax Search.

Minimax duyệt cây quyết định hai người chơi. Player chọn nhánh có utility lớn
nhất, Opponent chọn nhánh làm utility nhỏ nhất.
"""

from time import perf_counter

from src.ai.pathfinding.adversarial.game_state import (
    PLAYER_TURN,
    AdversarialGameState,
    AdversarialSearchResult,
    AdversarialSearchStats,
    apply_action,
    build_initial_state,
    build_reward_map,
    evaluate_state,
    get_actions,
    is_terminal,
    now_ms_since,
)
from src.gameplay.auto.models import AutoOrder
from src.gameplay.auto.route_cost_matrix import RouteCostMatrix


def _minimax(
    state: AdversarialGameState,
    matrix: RouteCostMatrix,
    reward_map: dict[str, float],
    depth_limit: int,
    stats: AdversarialSearchStats,
) -> tuple[float, tuple[str, ...]]:
    """Đệ quy minimax trả về utility tốt nhất và chuỗi đơn tương ứng."""

    stats.expanded_nodes += 1

    if is_terminal(state, depth_limit):
        return evaluate_state(state), ()

    actions = get_actions(state)
    stats.generated_nodes += len(actions)

    if state.turn == PLAYER_TURN:
        # MAX node: Player muốn tối đa hóa utility.
        best_value = float("-inf")
        best_sequence: tuple[str, ...] = ()

        for action in actions:
            next_state = apply_action(
                state=state,
                order_id=action,
                matrix=matrix,
                reward_map=reward_map,
            )

            value, sequence = _minimax(
                state=next_state,
                matrix=matrix,
                reward_map=reward_map,
                depth_limit=depth_limit,
                stats=stats,
            )

            if value > best_value:
                best_value = value
                best_sequence = (action, *sequence)

        return best_value, best_sequence

    # MIN node: Opponent muốn làm utility của Player nhỏ nhất.
    best_value = float("inf")
    best_sequence = ()

    for action in actions:
        next_state = apply_action(
            state=state,
            order_id=action,
            matrix=matrix,
            reward_map=reward_map,
        )

        value, sequence = _minimax(
            state=next_state,
            matrix=matrix,
            reward_map=reward_map,
            depth_limit=depth_limit,
            stats=stats,
        )

        if value < best_value:
            best_value = value
            best_sequence = (action, *sequence)

    return best_value, best_sequence


def minimax_search(
    order_ids: list[str],
    orders: list[AutoOrder],
    matrix: RouteCostMatrix,
    depth_limit: int = 6,
    initial_state: AdversarialGameState | None = None,
) -> AdversarialSearchResult:
    """Hàm public chạy Minimax và đóng gói kết quả cho benchmark/visualizer."""

    started_at = perf_counter()
    reward_map = build_reward_map(orders)
    stats = AdversarialSearchStats()

    initial_state = initial_state or build_initial_state(order_ids)

    value, sequence = _minimax(
        state=initial_state,
        matrix=matrix,
        reward_map=reward_map,
        depth_limit=depth_limit,
        stats=stats,
    )

    best_order_id = sequence[0] if sequence else None

    return AdversarialSearchResult(
        algorithm="MINIMAX",
        best_order_id=best_order_id,
        best_sequence=sequence,
        expected_utility=value,
        expanded_nodes=stats.expanded_nodes,
        generated_nodes=stats.generated_nodes,
        pruned_nodes=stats.pruned_nodes,
        runtime_ms=now_ms_since(started_at),
    )
