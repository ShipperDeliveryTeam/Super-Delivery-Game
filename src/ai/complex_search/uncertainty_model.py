from __future__ import annotations

from dataclasses import dataclass

from src.gameplay.auto.route_cost_matrix import RouteCostMatrix


@dataclass(frozen=True)
class UncertainCost:
    normal_cost: float
    expected_cost: float
    worst_case_cost: float


class UncertaintyModel:
    """
    Mô hình bất định cho nhóm 4.

    Vì hiện tại TMX Auto chưa có trap thật, ta mô phỏng rủi ro dựa trên map:
    - Map 1: ít rủi ro
    - Map 2: có tuyết/giao thông, rủi ro trung bình
    - Map 3: nhiều ngã rẽ/ẩn chặn đường, rủi ro cao hơn
    """

    def __init__(self, matrix: RouteCostMatrix) -> None:
        self.matrix = matrix
        self.map_id = matrix.map_id

    def _risk_factor(self) -> float:
        if self.map_id == 1:
            return 0.05

        if self.map_id == 2:
            return 0.15

        if self.map_id == 3:
            return 0.25

        return 0.10

    def get_uncertain_cost(
        self,
        from_label: str,
        to_label: str,
    ) -> UncertainCost:
        normal_cost = self.matrix.get_cost(from_label, to_label)

        if normal_cost == float("inf"):
            return UncertainCost(
                normal_cost=float("inf"),
                expected_cost=float("inf"),
                worst_case_cost=float("inf"),
            )

        risk = self._risk_factor()

        expected_cost = normal_cost * (1.0 + risk)
        worst_case_cost = normal_cost * (1.0 + risk * 2.0)

        return UncertainCost(
            normal_cost=normal_cost,
            expected_cost=expected_cost,
            worst_case_cost=worst_case_cost,
        )

    def get_no_observation_cost(
        self,
        from_label: str,
        to_label: str,
    ) -> float:
        """
        Không quan sát:
        dùng chi phí kỳ vọng, vì AI không biết chính xác trap đang ở đâu.
        """
        return self.get_uncertain_cost(from_label, to_label).expected_cost

    def get_partial_observation_cost(
        self,
        from_label: str,
        to_label: str,
    ) -> float:
        """
        Quan sát một phần:
        giảm một nửa rủi ro vì AI có thêm thông tin môi trường.
        """
        uncertain_cost = self.get_uncertain_cost(from_label, to_label)

        if uncertain_cost.normal_cost == float("inf"):
            return float("inf")

        return (uncertain_cost.normal_cost + uncertain_cost.expected_cost) / 2.0

    def get_and_or_cost(
        self,
        from_label: str,
        to_label: str,
    ) -> float:
        """
        AND-OR Search:
        xét trường hợp xấu hơn để chọn phương án an toàn.
        """
        return self.get_uncertain_cost(from_label, to_label).worst_case_cost