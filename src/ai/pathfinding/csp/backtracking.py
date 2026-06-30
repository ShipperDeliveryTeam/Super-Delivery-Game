from __future__ import annotations

"""Backtracking Search cho bài toán sắp thứ tự đơn hàng.

File này là wrapper cấu hình: dùng solver CSP chung, thử hành động theo thứ tự
từ điển và không bật forward checking hay AC-3.
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
    """Chạy CSP backtracking thuần để tìm route có chi phí tốt hơn route mặc định."""

    return solve_csp_route(
        problem=CSPRouteProblem(
            order_ids=order_ids,
            capacity=capacity,
            cost_provider=cost_provider,
        ),
        algorithm="BACKTRACKING",
        action_strategy="LEXICOGRAPHIC",
        use_forward_checking=False,
        use_ac3_precheck=False,
        max_expanded_nodes=max_expanded_nodes,
    )
