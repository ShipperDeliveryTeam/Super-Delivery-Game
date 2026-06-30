from __future__ import annotations

"""Forward Checking Search.

Biến thể này vẫn dùng backtracking nhưng sau mỗi hành động sẽ kiểm tra sớm
xem phần route còn lại có còn khả năng hoàn thành không. Nếu không, nhánh đó
bị cắt ngay.
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
    """Chạy CSP với forward checking và ưu tiên hành động có chi phí gần nhất."""

    return solve_csp_route(
        problem=CSPRouteProblem(
            order_ids=order_ids,
            capacity=capacity,
            cost_provider=cost_provider,
        ),
        algorithm="FORWARD_CHECKING",
        action_strategy="NEAREST_COST",
        use_forward_checking=True,
        use_ac3_precheck=False,
        max_expanded_nodes=max_expanded_nodes,
    )
