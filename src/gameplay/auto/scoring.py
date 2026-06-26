from __future__ import annotations

from src.gameplay.auto.models import AutoOrder, RunResult


RANK_BONUS = {
    1: 1.20,
    2: 1.10,
    3: 1.00,
}


def calculate_late_penalty(order: AutoOrder, delivered_at: float) -> float:
    """
    Phạt giao trễ.

    Nếu giao đúng hạn: không phạt.
    Nếu trễ: phạt theo số giây trễ, tối đa 50% reward.
    """
    if delivered_at <= order.deadline:
        return 0.0

    late_seconds = delivered_at - order.deadline
    return min(order.reward * 0.5, late_seconds * 1.0)


def calculate_order_score(order: AutoOrder, delivered_at: float) -> float:
    """
    Điểm cơ bản cho một đơn hàng.
    """
    penalty = calculate_late_penalty(order, delivered_at)
    return max(0.0, order.reward - penalty)


def calculate_competition_score(order: AutoOrder, delivered_at: float) -> float:
    """
    Điểm cho Competition Mode.

    Giao đúng hạn: reward + 20% bonus.
    Giao trễ: reward - penalty.
    """
    if delivered_at <= order.deadline:
        return order.reward * 1.2

    return calculate_order_score(order, delivered_at)


def _benchmark_sort_key(result: RunResult) -> tuple:
    """
    Xếp hạng Benchmark công bằng.

    Nhóm 1-5:
    - Ưu tiên hoàn thành đủ 6 đơn.
    - Sau đó ưu tiên completed_orders nhiều hơn.
    - Sau đó ưu tiên finish_time / total_distance thấp hơn.

    Nhóm 6:
    - Đây là nhóm đối kháng, không dùng distance.
    - Ưu tiên total_score / utility cao hơn.
    - Nếu utility bằng nhau, thuật toán expanded_nodes ít hơn đứng trước.
    """
    is_failed = 0 if result.completed_orders == 6 else 1

    if result.algorithm_group == 6:
        return (
            is_failed,
            -result.completed_orders,
            -result.total_score,
            result.expanded_nodes,
        )

    return (
        is_failed,
        -result.completed_orders,
        result.finish_time,
        result.expanded_nodes,
    )

def apply_benchmark_rank_bonus(results: list[RunResult]) -> list[RunResult]:
    """
    Xếp hạng Benchmark Mode.

    Nhanh/tốt nhất: 120%
    Thứ hai: 110%
    Thứ ba trở đi: 100%

    Thuật toán fail vẫn được xếp hạng sau các thuật toán hoàn thành đủ 6 đơn.
    """
    ranked = sorted(results, key=_benchmark_sort_key)

    for index, result in enumerate(ranked, start=1):
        result.rank = index

        bonus = RANK_BONUS.get(index, 1.0)

        # Chỉ cộng bonus nếu hoàn thành đủ 6 đơn.
        if result.completed_orders == 6:
            result.total_score = round(result.total_score * bonus, 2)
        else:
            result.total_score = round(result.total_score, 2)

    return ranked