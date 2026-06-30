"""Cac ham dung chung cho thuat toan tim duong.

File nay chi giu nhung thu that su can:
- SearchResult: ket qua sau khi chay thuat toan.
- reconstruct_path: dung lai duong di tu bang parent.
- calculate_path_cost: tinh tong chi phi cua mot duong di.
"""


GridPos = tuple[int, int]


class SearchResult:
    """Ket qua don gian cua mot lan tim duong."""

    def __init__(self, algorithm, path, cost, expanded_nodes, generated_nodes, runtime_ms):
        self.algorithm = algorithm
        self.path = path
        self.cost = cost
        self.expanded_nodes = expanded_nodes
        self.generated_nodes = generated_nodes
        self.runtime_ms = runtime_ms

        # Cac file khac trong project co cho dung ca found va success.
        self.found = len(path) > 0
        self.success = self.found


def reconstruct_path(parent, goal):
    """Duyet nguoc tu goal ve start roi dao nguoc lai."""

    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()
    return path


def is_goal(current, goal):
    """Goal co the la mot gia tri hoac mot ham kiem tra."""

    if callable(goal):
        return goal(current)

    return current == goal


def calculate_path_cost(path, get_neighbors):
    """Tinh tong chi phi cua path."""

    if len(path) <= 1:
        return 0

    total = 0

    for i in range(len(path) - 1):
        current = path[i]
        next_pos = path[i + 1]

        for neighbor, step_cost in get_neighbors(current):
            if neighbor == next_pos:
                total += step_cost
                break

    return total
