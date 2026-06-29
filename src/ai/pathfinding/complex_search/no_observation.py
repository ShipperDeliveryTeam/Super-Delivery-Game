from __future__ import annotations

import random
from dataclasses import dataclass
from time import perf_counter


@dataclass
class BeliefState:
    name: str
    traps: tuple[tuple[int, int], ...]


@dataclass
class ComplexSearchResult:
    algorithm: str
    actions: tuple[str, ...]
    normal_cost: float
    decision_cost: float
    risk_mode: str
    belief_states: tuple[BeliefState, ...]
    known_traps: tuple[tuple[int, int], ...]
    iterations: int
    expanded_nodes: int
    generated_nodes: int
    runtime_ms: float


def make_actions(order_ids):
    actions = []
    for order_id in order_ids:
        actions.append(f"P_{order_id}")
        actions.append(f"D_{order_id}")
    return tuple(actions)


def _seed_from_traps(possible_traps, known_traps=()):
    total = 0
    for x, y in list(possible_traps) + list(known_traps):
        total += x * 31 + y * 17
    return total + len(possible_traps) * 101 + len(known_traps) * 53


def make_belief_states(possible_traps, known_traps=(), max_traps=None):
    possible_traps = list(possible_traps)
    known_traps = tuple(known_traps)

    if not possible_traps and not known_traps:
        return (BeliefState("B1", tuple()), BeliefState("B2", tuple()))

    rng = random.Random(_seed_from_traps(possible_traps, known_traps))
    belief_states = []

    if max_traps is None:
        max_count = len(possible_traps) + len(known_traps)
    else:
        max_count = max_traps
    max_count = max(1, max_count)

    for index in range(2):
        min_count = max(1, len(known_traps))
        trap_count = rng.randint(min_count, max_count)

        candidates = list(possible_traps)
        rng.shuffle(candidates)

        traps = list(known_traps)
        for trap in candidates:
            if len(traps) >= trap_count:
                break
            if trap not in traps:
                traps.append(trap)

        belief_states.append(BeliefState(f"B{index + 1}", tuple(traps)))

    return tuple(belief_states)


def union_belief_traps(belief_states):
    traps = []
    for belief in belief_states:
        for trap in belief.traps:
            if trap not in traps:
                traps.append(trap)
    return tuple(traps)


def belief_cost(actions, belief_states):
    normal_cost = len(actions) * 10
    risk_cost = 0

    for belief in belief_states:
        risk_cost += len(belief.traps) * 5

    return normal_cost + risk_cost


def make_result(algorithm, order_ids, risk_mode, belief_states, known_traps, started_at):
    actions = make_actions(order_ids)
    normal_cost = len(actions) * 10
    decision_cost = belief_cost(actions, belief_states)

    return ComplexSearchResult(
        algorithm=algorithm,
        actions=actions,
        normal_cost=normal_cost,
        decision_cost=decision_cost,
        risk_mode=risk_mode,
        belief_states=belief_states,
        known_traps=tuple(known_traps),
        iterations=len(belief_states),
        expanded_nodes=len(belief_states),
        generated_nodes=len(belief_states) * max(1, len(order_ids)),
        runtime_ms=(perf_counter() - started_at) * 1000,
    )


def no_observation_search(order_ids, possible_traps=(), capacity=1, max_traps=None):
    started_at = perf_counter()

    # Không biết bẫy ở đâu: tạo 2 belief state, mỗi belief có nhiều bẫy giả định.
    belief_states = make_belief_states(possible_traps, max_traps=max_traps)

    return make_result(
        algorithm="NO_OBSERVATION",
        order_ids=list(order_ids),
        risk_mode="TWO_UNKNOWN_BELIEFS",
        belief_states=belief_states,
        known_traps=(),
        started_at=started_at,
    )
