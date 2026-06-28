from __future__ import annotations

import random
from time import perf_counter

from src.ai.pathfinding.complex_search.no_observation import BeliefState, make_result


def _make_and_or_cases(possible_traps, known_traps=(), case_count=60, max_traps=None, seed=42):
    possible_traps = list(possible_traps)
    known_traps = tuple(known_traps)

    if max_traps is None:
        max_traps = len(possible_traps) + len(known_traps)
    max_traps = max(1, max_traps)

    rng = random.Random(seed + len(possible_traps) * 17 + len(known_traps) * 31)
    cases = []

    for index in range(case_count):
        if index % 3 == 0:
            trap_count = rng.randint(max(1, len(known_traps)), max(1, max_traps // 2))
        elif index % 3 == 1:
            trap_count = rng.randint(max(1, max_traps // 2), max_traps)
        else:
            trap_count = rng.randint(max(1, len(known_traps)), max_traps)
        traps = list(known_traps)

        candidates = list(possible_traps)
        rng.shuffle(candidates)

        for trap in candidates:
            if len(traps) >= trap_count:
                break
            if trap not in traps:
                traps.append(trap)

        cases.append(BeliefState(f"CASE_{index + 1}", tuple(traps)))

    return tuple(cases)


def and_or_search(order_ids, possible_traps=(), known_traps=(), capacity=1, beam_width=5, max_iterations=100, seed=42, max_traps=None):
    started_at = perf_counter()

    # Riêng AND-OR sinh nhiều nhánh khả năng để chọn một plan dùng được cho các nhánh.
    belief_states = _make_and_or_cases(
        possible_traps=possible_traps,
        known_traps=known_traps,
        case_count=60,
        max_traps=max_traps,
        seed=seed,
    )

    return make_result(
        algorithm="AND_OR_SEARCH",
        order_ids=sorted(order_ids),
        risk_mode="MANY_PREPLANNED_CASES",
        belief_states=belief_states,
        known_traps=known_traps,
        started_at=started_at,
    )
