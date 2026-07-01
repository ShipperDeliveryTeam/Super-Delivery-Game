from __future__ import annotations

"""Backtracking Search cho bai toan sap thu tu don hang.

Backtracking thuan: thu tung hanh dong hop le, sai thi quay lui.
"""

from src.ai.pathfinding.csp.csp_model import (
    CSPRouteProblem,
    CSPRouteSearchResult,
    RouteCostProvider,
    solve_csp_route,
)


def backtracking_search(
    order_ids: list[str],
    capacity: int,
    cost_provider: RouteCostProvider,
    max_expanded_nodes: int = 10000,
) -> CSPRouteSearchResult:
    return solve_csp_route(
        problem=CSPRouteProblem(
            order_ids=order_ids,
            capacity=capacity,
            cost_provider=cost_provider,
        ),
        algorithm="BACKTRACKING",
        action_strategy="SIMPLE",
        use_forward_checking=False,
        use_ac3_precheck=False,
        max_expanded_nodes=max_expanded_nodes,
    )
