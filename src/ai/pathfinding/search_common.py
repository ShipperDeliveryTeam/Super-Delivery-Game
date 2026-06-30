from __future__ import annotations

"""Các kiểu dữ liệu và hàm dùng chung cho toàn bộ thuật toán tìm đường.

Những thuật toán như BFS, DFS, UCS, A* đều trả về cùng một kiểu
`SearchResult` để phần game có thể đọc path, chi phí và số node đã mở rộng
mà không cần biết chi tiết thuật toán bên trong.
"""

from collections.abc import Callable
from dataclasses import dataclass


GridPos = tuple[int, int]
NeighborFn = Callable[[GridPos], list[tuple[GridPos, float]]] # nhận vào một vị trí (x, y) và trả về danh sách các vị trí lân cận cùng với chi phí di chuyển đến chúng
HeuristicFn = Callable[[GridPos, GridPos], float]

@dataclass
class SearchResult:
    """Kết quả chuẩn của một lần chạy thuật toán tìm kiếm."""

    algorithm: str # tên thuật toán
    path: list[GridPos] # đường đi từ start đến goal
    cost: float # tổng chi phí của đường đi (tổng chi phí từng bước đi)
    expanded_nodes: int # số node đã được mở rộng (được lấy ra khỏi queue và xét)
    generated_nodes: int # số node đã được tạo ra (được thêm vào queue hoặc stack, kể cả những node đã được mở rộng)
    runtime_ms: float # thời gian chạy thuật toán (tính bằng mili giây)

    @property
    def found(self) -> bool: # kiểm tra xem có tìm thấy đường đi không
        return len(self.path) > 0

    @property
    def success(self) -> bool: # kiểm tra xem có tìm thấy đường đi không (tương tự found)
        return self.found

def reconstruct_path(parent, goal):
    """Dựng lại đường đi từ bảng `parent`: goal -> ... -> start rồi đảo ngược."""

    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()
    return path

def calculate_path_cost(path, get_neighbors):
    """Tính tổng chi phí thật của một path dựa trên chi phí từng cạnh."""

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
