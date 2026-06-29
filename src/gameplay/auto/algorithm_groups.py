from __future__ import annotations


GROUP_1_UNINFORMED = 1
GROUP_2_INFORMED = 2
GROUP_3_LOCAL_SEARCH = 3
GROUP_4_COMPLEX_ENVIRONMENT = 4
GROUP_5_CSP = 5
GROUP_6_ADVERSARIAL = 6


ALGORITHM_GROUPS = {
    GROUP_1_UNINFORMED: ["BFS", "DFS", "UCS"],
    GROUP_2_INFORMED: ["GREEDY", "ASTAR", "IDA_STAR"],
    GROUP_3_LOCAL_SEARCH: ["SIMPLE_HILL", "STEEPEST_HILL", "LOCAL_BEAM"],
    GROUP_4_COMPLEX_ENVIRONMENT: ["NO_OBSERVATION", "PARTIAL_OBSERVATION", "AND_OR_SEARCH"],
    GROUP_5_CSP: ["BACKTRACKING", "FORWARD_CHECKING", "AC3_BACKTRACKING"],
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
    return list(ALGORITHM_GROUPS.get(group_id, []))


def get_group_name(group_id: int) -> str:
    return GROUP_NAMES.get(group_id, "Không xác định")


def get_representative_algorithm(group_id: int) -> str:
    return REPRESENTATIVE_ALGORITHMS[group_id]


def get_representatives() -> list[str]:
    return list(REPRESENTATIVE_ALGORITHMS.values())


def is_valid_group(group_id: int) -> bool:
    return group_id in ALGORITHM_GROUPS