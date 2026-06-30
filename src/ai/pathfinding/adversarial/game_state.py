from __future__ import annotations

"""Du lieu dung chung cho Minimax, Alpha-Beta va Expectimax."""

from dataclasses import dataclass
from time import perf_counter


PLAYER_TURN = "PLAYER"
OPPONENT_TURN = "OPPONENT"


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


def build_reward_map(orders) -> dict[str, float]:
    rewards = {}
    for order in orders:
        rewards[order.id] = float(order.reward)
    return rewards


def calculate_order_trip_cost(matrix, current_label: str, order_id: str) -> float:
    pickup = f"P_{order_id}"
    delivery = f"D_{order_id}"
    return matrix.get_cost(current_label, pickup) + matrix.get_cost(pickup, delivery)


def calculate_order_gain(matrix, reward_map: dict[str, float], current_label: str, order_id: str) -> float:
    reward = reward_map[order_id]
    cost = calculate_order_trip_cost(matrix, current_label, order_id)
    return reward - cost


def evaluate_state(state: AdversarialGameState) -> float:
    return state.player_score - state.opponent_score


def apply_action(state: AdversarialGameState, order_id: str, matrix, reward_map) -> AdversarialGameState:
    remaining = []
    for current_order_id in state.remaining_order_ids:
        if current_order_id != order_id:
            remaining.append(current_order_id)

    if state.turn == PLAYER_TURN:
        gain = calculate_order_gain(matrix, reward_map, state.player_label, order_id)
        return AdversarialGameState(
            remaining_order_ids=tuple(remaining),
            player_label=f"D_{order_id}",
            opponent_label=state.opponent_label,
            player_score=state.player_score + gain,
            opponent_score=state.opponent_score,
            turn=OPPONENT_TURN,
            depth=state.depth + 1,
        )

    gain = calculate_order_gain(matrix, reward_map, state.opponent_label, order_id)
    return AdversarialGameState(
        remaining_order_ids=tuple(remaining),
        player_label=state.player_label,
        opponent_label=f"D_{order_id}",
        player_score=state.player_score,
        opponent_score=state.opponent_score + gain,
        turn=PLAYER_TURN,
        depth=state.depth + 1,
    )


def order_actions_by_gain(state: AdversarialGameState, actions: list[str], matrix, reward_map):
    if state.turn == PLAYER_TURN:
        label = state.player_label
        reverse = True
    else:
        label = state.opponent_label
        reverse = False

    def score(order_id):
        return calculate_order_gain(matrix, reward_map, label, order_id)

    return sorted(actions, key=score, reverse=reverse)


def now_ms_since(started_at: float) -> float:
    return (perf_counter() - started_at) * 1000
