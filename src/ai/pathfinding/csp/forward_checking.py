from __future__ import annotations

"""Forward Checking Search.

Van la backtracking, nhung sau moi hanh dong se kiem tra xem con
hanh dong hop le de di tiep khong. Neu khong, cat nhanh som.
"""

from src.ai.pathfinding.csp.csp_model import (
    CSPRouteProblem,
    CSPRouteSearchResult,
    RouteCostProvider,
    solve_csp_route,
)


def forward_checking_search(
    order_ids: list[str],
    capacity: int,
    cost_provider: RouteCostProvider,
    max_expanded_nodes: int = 15000,
) -> CSPRouteSearchResult:
    return solve_csp_route(
        problem=CSPRouteProblem(
            order_ids=order_ids,
            capacity=capacity,
            cost_provider=cost_provider,
        ),
        algorithm="FORWARD_CHECKING",
        action_strategy="SIMPLE",
        use_forward_checking=True,
        use_ac3_precheck=False,
        max_expanded_nodes=max_expanded_nodes,
    )
