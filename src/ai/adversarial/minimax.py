from __future__ import annotations

from time import perf_counter

from src.ai.adversarial.game_state import (
    OPPONENT_TURN,
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
    stats.expanded_nodes += 1

    if is_terminal(state, depth_limit):
        return evaluate_state(state), ()

    actions = get_actions(state)
    stats.generated_nodes += len(actions)

    if state.turn == PLAYER_TURN:
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
) -> AdversarialSearchResult:
    started_at = perf_counter()
    reward_map = build_reward_map(orders)
    stats = AdversarialSearchStats()

    initial_state = build_initial_state(order_ids)

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