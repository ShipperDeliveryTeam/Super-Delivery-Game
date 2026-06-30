from __future__ import annotations

"""Partial Observation Search.

Thuật toán này mô phỏng trường hợp shipper biết trước một phần thông tin bẫy.
Trong game, hai bẫy đầu tiên được coi là đã biết và xuất hiện trong mọi belief.
"""

from time import perf_counter

from src.ai.pathfinding.complex_search.no_observation import make_belief_states, make_result


def partial_observation_search(
    order_ids,
    possible_traps=(),
    known_traps=(),
    capacity=1,
    max_iterations=100,
    max_traps=None,
):
    """Tạo belief state với một phần bẫy đã biết trước."""

    started_at = perf_counter()

    # Biết trước 2 bẫy thật. Hai bẫy này luôn nằm trong mọi belief state.
    known_traps = tuple(known_traps[:2])
    unknown_traps = []

    for trap in possible_traps:
        if trap not in known_traps:
            unknown_traps.append(trap)

    belief_states = make_belief_states(unknown_traps, known_traps, max_traps=max_traps)

    return make_result(
        algorithm="PARTIAL_OBSERVATION",
        order_ids=list(order_ids),
        risk_mode="TWO_KNOWN_TRAPS_IN_ALL_BELIEFS",
        belief_states=belief_states,
        known_traps=known_traps,
        started_at=started_at,
    )
