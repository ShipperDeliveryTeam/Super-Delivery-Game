from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable


GridPos = tuple[int, int]
NeighborFn = Callable[[GridPos], list[GridPos]]
HeuristicFn = Callable[[GridPos], float]


@dataclass
class LocalPathResult:
    algorithm: str
    path: list[GridPos]
    found: bool
    expanded_nodes: int
    generated_nodes: int
    runtime_ms: float


def local_beam_search(
    start: GridPos,
    goal: GridPos,
    get_neighbors: NeighborFn,
    heuristic: HeuristicFn,
    beam_width: int = 5,
    max_steps: int = 1000,
) -> LocalPathResult:
    started_at = perf_counter()
    beam = [[start]]
    expanded = 0
    generated = 0

    def path_score(item):
        return heuristic(item[-1])

    for _ in range(max_steps):
        candidates: list[list[GridPos]] = [] #Danh sách các node được sinh ra từ 
                                             #các node trong beam hiện tại.

        for path in beam:
            current = path[-1] # Lấy node cuối cùng trong path hiện tại để mở rộng.
            expanded += 1  # Đếm số lượng node được xét

            if current == goal:
                return LocalPathResult(
                    algorithm="LOCAL_BEAM",
                    path=path,
                    found=True,
                    expanded_nodes=expanded,
                    generated_nodes=generated,
                    runtime_ms=(perf_counter() - started_at) * 1000,
                )

            for neighbor in get_neighbors(current):
                generated += 1 # Số node sinh ra
                candidates.append(path + [neighbor]) # Thêm neighbor vào path hiện tại 
                                                     #và thêm vào danh sách candidates.

        if not candidates:
            break

        candidates.sort(key=path_score) # Sắp xếp theo hàm path_score
                                        #Sắp xếp theo giá trị của node cuối
        beam = candidates[:beam_width]

    if beam: # Nếu có đường thì chọn đường tốt nhất trong beam
             # Nếu không thì trả về đường chỉ có start.
        best_path = min(beam, key=path_score)
    else:
        best_path = [start]

    return LocalPathResult(
        algorithm="LOCAL_BEAM",
        path=best_path,
        found=best_path[-1] == goal,
        expanded_nodes=expanded,
        generated_nodes=generated,
        runtime_ms=(perf_counter() - started_at) * 1000,
    )
