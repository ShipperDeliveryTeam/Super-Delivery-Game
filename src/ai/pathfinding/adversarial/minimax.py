from __future__ import annotations

"""Minimax ban don gian."""

from time import perf_counter

from src.ai.pathfinding.adversarial.game_state import (
    PLAYER_TURN,
    AdversarialGameState,
    AdversarialSearchResult,
    apply_action,
    build_initial_state,
    build_reward_map,
    evaluate_state,
    now_ms_since,
)


def minimax_node(state, matrix, reward_map, depth_limit, stats):
    stats["expanded"] += 1

    if not state.remaining_order_ids or state.depth >= depth_limit:
        return evaluate_state(state), tuple()

    actions = list(state.remaining_order_ids)
    stats["generated"] += len(actions)

    if state.turn == PLAYER_TURN:
        best_value = float("-inf")
    else:
        best_value = float("inf")

    best_sequence = tuple()

    for order_id in actions:
        child = apply_action(state, order_id, matrix, reward_map)
        value, sequence = minimax_node(child, matrix, reward_map, depth_limit, stats)

        if state.turn == PLAYER_TURN and value > best_value:
            best_value = value
            best_sequence = (order_id, *sequence)

        if state.turn != PLAYER_TURN and value < best_value:
            best_value = value
            best_sequence = (order_id, *sequence)

    return best_value, best_sequence


def minimax_search(
    order_ids: list[str],
    orders,
    matrix,
    depth_limit: int = 6,
    initial_state: AdversarialGameState | None = None,
) -> AdversarialSearchResult:
    started_at = perf_counter()
    reward_map = build_reward_map(orders)
    state = initial_state or build_initial_state(order_ids)
    stats = {"expanded": 0, "generated": 0, "pruned": 0} # sinh ra, mở rộng, cắt tỉa

    value, sequence = minimax_node(state, matrix, reward_map, depth_limit, stats)
    best_order_id = sequence[0] if sequence else None

    return AdversarialSearchResult(
        algorithm="MINIMAX",
        best_order_id=best_order_id,
        best_sequence=sequence,
        expected_utility=value,
        expanded_nodes=stats["expanded"],
        generated_nodes=stats["generated"],
        pruned_nodes=stats["pruned"],
        runtime_ms=now_ms_since(started_at),
    )
