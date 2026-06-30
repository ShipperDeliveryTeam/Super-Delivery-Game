from __future__ import annotations

"""AND-OR Search ban don gian.

AND-OR o day tao nhieu case bay khac nhau de mo phong cac kha nang cua moi
truong. File nay chi tao case va actions bao cao, khong gop voi logic
No/Partial Observation.
"""

import random
from time import perf_counter

from src.ai.pathfinding.complex_search.no_observation import BeliefState, ComplexSearchResult


def make_case_list(possible_traps, known_traps=(), case_count=60, max_traps=None, seed=42):
    possible_traps = list(possible_traps)
    known_traps = tuple(known_traps)
    max_traps = max_traps or len(possible_traps) + len(known_traps)
    max_traps = max(1, max_traps)

    rng = random.Random(seed)
    cases = []

    for index in range(case_count):
        traps = list(known_traps)
        candidates = list(possible_traps)
        rng.shuffle(candidates)

        if index % 3 == 0:
            trap_count = max(1, max_traps // 2)
        elif index % 3 == 1:
            trap_count = max_traps
        else:
            trap_count = rng.randint(1, max_traps)

        for trap in candidates:
            if len(traps) >= trap_count:
                break
            if trap not in traps:
                traps.append(trap)

        cases.append(BeliefState(f"CASE_{index + 1}", tuple(traps)))

    return tuple(cases)


def make_report_actions(order_ids):
    actions = []
    for order_id in sorted(order_ids):
        actions.append(f"P_{order_id}")
        actions.append(f"D_{order_id}")
    return tuple(actions)


def and_or_search(
    order_ids,
    possible_traps=(),
    known_traps=(),
    capacity=1,
    beam_width=5,
    max_iterations=100,
    seed=42,
    max_traps=None,
):
    started_at = perf_counter()

    belief_states = make_case_list(
        possible_traps=possible_traps,
        known_traps=known_traps,
        case_count=60,
        max_traps=max_traps,
        seed=seed,
    )

    actions = make_report_actions(order_ids)
    cost = len(actions) * 10

    return ComplexSearchResult(
        algorithm="AND_OR_SEARCH",
        actions=actions,
        normal_cost=cost,
        decision_cost=cost,
        risk_mode="MANY_PREPLANNED_CASES",
        belief_states=belief_states,
        known_traps=tuple(known_traps),
        iterations=len(belief_states),
        expanded_nodes=len(belief_states),
        generated_nodes=len(belief_states) * max(1, len(order_ids)),
        runtime_ms=(perf_counter() - started_at) * 1000,
    )
