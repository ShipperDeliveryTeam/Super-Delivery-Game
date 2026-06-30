from __future__ import annotations

"""AC3 + Backtracking.

AC-3 được dùng như bước tiền xử lý để kiểm tra ràng buộc miền giá trị trước
khi backtracking. Sau đó solver vẫn dùng forward checking để cắt nhánh.
"""

from src.ai.pathfinding.csp.csp_model import (
    CSPRouteProblem,
    CSPRouteSearchResult,
    RouteCostProvider,
    solve_csp_route,
)


def ac3_backtracking_search(
    order_ids: list[str],
    capacity: int,
    cost_provider: RouteCostProvider,
    max_expanded_nodes: int = 20000,
) -> CSPRouteSearchResult:
    """Chạy CSP có AC-3 precheck, forward checking và thứ tự ưu tiên riêng."""

    return solve_csp_route(
        problem=CSPRouteProblem(
            order_ids=order_ids,
            capacity=capacity,
            cost_provider=cost_provider,
        ),
        algorithm="AC3_BACKTRACKING",
        action_strategy="AC3_PRIORITY",
        use_forward_checking=True,
        use_ac3_precheck=True,
        max_expanded_nodes=max_expanded_nodes,
    )
