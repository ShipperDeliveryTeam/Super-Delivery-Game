from __future__ import annotations

"""Local Beam Search.

Thay vì chỉ giữ một đường như hill climbing, beam search giữ `beam_width`
đường tốt nhất ở mỗi vòng. Cách này giảm nguy cơ kẹt ở một nhánh xấu.
"""

from dataclasses import dataclass
from time import perf_counter
from typing import Callable


GridPos = tuple[int, int]
NeighborFn = Callable[[GridPos], list[GridPos]]
HeuristicFn = Callable[[GridPos], float]


@dataclass
class LocalPathResult:
    """Kết quả chuẩn cho các thuật toán tìm kiếm cục bộ."""

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
    """Mở rộng nhiều path song song và chỉ giữ lại các path có heuristic tốt nhất."""

    started_at = perf_counter()
    # beam là danh sách các path đang được giữ lại để mở rộng ở vòng sau.
    beam = [[start]]
    expanded = 0
    generated = 0

    def path_score(item):
        """Điểm của path được tính bằng heuristic tại node cuối path."""
        return heuristic(item[-1])

    for _ in range(max_steps):
        candidates: list[list[GridPos]] = []

        for path in beam:
            current = path[-1]
            expanded += 1

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
                generated += 1
                candidates.append(path + [neighbor])

        if not candidates:
            break

        # Chỉ giữ lại beam_width ứng viên tốt nhất, bỏ các nhánh kém hơn.
        candidates.sort(key=path_score)
        beam = candidates[:beam_width]

    if beam:
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
