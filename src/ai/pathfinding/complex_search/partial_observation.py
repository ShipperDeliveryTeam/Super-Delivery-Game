from __future__ import annotations

"""Partial Observation.

Map co 3 bay. Thuat toan biet truoc 1 bay, sau do doan 2 bay con lai
trong tung belief state va chay A* rieng cho moi belief.
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
    map_data=None,
    orders=None,
    true_traps=(),
):
    started_at = perf_counter()

    known_traps = tuple(known_traps[:1])
    unknown_traps = []

    for trap in possible_traps:
        if trap not in known_traps:
            unknown_traps.append(trap)

    if max_traps is None:
        unknown_count = 2
    else:
        unknown_count = max(0, max_traps - len(known_traps))

    belief_states = make_belief_states(
        candidate_cells=unknown_traps,
        known_traps=known_traps,
        max_traps=max_traps,
        unknown_count=unknown_count,
    )

    return make_result(
        algorithm="PARTIAL_OBSERVATION",
        order_ids=list(order_ids),
        risk_mode="ONE_KNOWN_TWO_UNKNOWN_BELIEFS",
        belief_states=belief_states,
        known_traps=known_traps,
        started_at=started_at,
        map_data=map_data,
        orders=orders,
        true_traps=true_traps,
    )
