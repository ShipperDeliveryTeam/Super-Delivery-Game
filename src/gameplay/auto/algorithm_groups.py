from __future__ import annotations

"""Khai báo các nhóm thuật toán dùng trong Play Mode và Auto Mode.

Mỗi level/group tương ứng với một nhóm thuật toán. Play Mode dùng danh sách
này để gán thuật toán cho NPC; Auto Visual cũng dùng để dựng demo/benchmark.
"""


GROUP_1_UNINFORMED = 1
GROUP_2_INFORMED = 2
GROUP_3_LOCAL_SEARCH = 3
GROUP_4_COMPLEX_ENVIRONMENT = 4
GROUP_5_CSP = 5
GROUP_6_ADVERSARIAL = 6


ALGORITHM_GROUPS = {
    # Nhóm 1: tìm kiếm không có thông tin, không dùng heuristic.
    GROUP_1_UNINFORMED: ["BFS", "DFS", "UCS"],
    # Nhóm 2: tìm kiếm có thông tin, dùng heuristic hướng tới goal.
    GROUP_2_INFORMED: ["GREEDY", "ASTAR", "IDA_STAR"],
    # Nhóm 3: local search, cải thiện lời giải dựa trên heuristic.
    GROUP_3_LOCAL_SEARCH: ["SIMPLE_HILL", "STEEPEST_HILL", "LOCAL_BEAM"],
    # Nhóm 4: môi trường phức tạp có bẫy/bất định.
    GROUP_4_COMPLEX_ENVIRONMENT: ["NO_OBSERVATION", "PARTIAL_OBSERVATION", "AND_OR_SEARCH"],
    # Nhóm 5: CSP, tối ưu thứ tự nhận/giao đơn dưới ràng buộc.
    GROUP_5_CSP: ["BACKTRACKING", "FORWARD_CHECKING", "AC3_BACKTRACKING"],
    # Nhóm 6: adversarial search, mô phỏng cạnh tranh hai người chơi.
    GROUP_6_ADVERSARIAL: ["MINIMAX", "ALPHA_BETA", "EXPECTIMAX"],
}


GROUP_NAMES = {
    GROUP_1_UNINFORMED: "Tìm kiếm không có thông tin",
    GROUP_2_INFORMED: "Tìm kiếm có thông tin",
    GROUP_3_LOCAL_SEARCH: "Tìm kiếm cục bộ",
    GROUP_4_COMPLEX_ENVIRONMENT: "Môi trường phức tạp",
    GROUP_5_CSP: "Tìm kiếm ràng buộc",
    GROUP_6_ADVERSARIAL: "Tìm kiếm đối kháng",
}


REPRESENTATIVE_ALGORITHMS = {
    GROUP_1_UNINFORMED: "UCS",
    GROUP_2_INFORMED: "ASTAR",
    GROUP_3_LOCAL_SEARCH: "LOCAL_BEAM",
    GROUP_4_COMPLEX_ENVIRONMENT: "AND_OR_SEARCH",
    GROUP_5_CSP: "FORWARD_CHECKING",
    GROUP_6_ADVERSARIAL: "ALPHA_BETA",
}


def get_algorithms_by_group(group_id: int) -> list[str]:
    """Trả về danh sách thuật toán của một level/group."""

    return list(ALGORITHM_GROUPS.get(group_id, []))


def get_group_name(group_id: int) -> str:
    """Tên tiếng Việt của group để hiển thị trên HUD/menu."""

    return GROUP_NAMES.get(group_id, "Không xác định")


def get_representative_algorithm(group_id: int) -> str:
    """Thuật toán đại diện dùng khi cần chạy một thuật toán tiêu biểu của group."""

    return REPRESENTATIVE_ALGORITHMS[group_id]


def get_representatives() -> list[str]:
    """Danh sách toàn bộ thuật toán đại diện."""

    return list(REPRESENTATIVE_ALGORITHMS.values())


def is_valid_group(group_id: int) -> bool:
    """Kiểm tra group id có tồn tại không."""

    return group_id in ALGORITHM_GROUPS
