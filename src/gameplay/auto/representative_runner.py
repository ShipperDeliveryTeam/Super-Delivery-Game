from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.gameplay.auto.benchmark_runner import (
    run_adversarial_benchmark_algorithm,
    run_complex_search_benchmark_algorithm,
    run_csp_benchmark_algorithm,
    run_local_search_benchmark_algorithm,
    run_pathfinding_benchmark_algorithm,
)
from src.gameplay.auto.models import RunResult


OUTPUT_PATH = Path("data") / "representative_comparison.csv"


@dataclass(frozen=True)
class RepresentativeAlgorithm:
    group_id: int
    group_name: str
    algorithm: str
    reason: str


REPRESENTATIVES = [
    RepresentativeAlgorithm(
        group_id=1,
        group_name="Tìm kiếm không có thông tin",
        algorithm="UCS",
        reason="Tối ưu chi phí đường đi tốt hơn BFS/DFS khi map có trọng số.",
    ),
    RepresentativeAlgorithm(
        group_id=2,
        group_name="Tìm kiếm có thông tin",
        algorithm="ASTAR",
        reason="Cân bằng tốt giữa chi phí tối ưu và số node mở rộng.",
    ),
    RepresentativeAlgorithm(
        group_id=3,
        group_name="Tìm kiếm cục bộ",
        algorithm="LOCAL_BEAM",
        reason="Có khả năng thoát cực trị cục bộ nhờ chấp nhận nghiệm xấu có kiểm soát.",
    ),
    RepresentativeAlgorithm(
        group_id=4,
        group_name="Môi trường phức tạp",
        algorithm="AND_OR_SEARCH",
        reason="Phù hợp môi trường bất định vì xét các trường hợp rủi ro.",
    ),
    RepresentativeAlgorithm(
        group_id=5,
        group_name="Tìm kiếm ràng buộc",
        algorithm="FORWARD_CHECKING",
        reason="Lọc nhánh sớm, hiệu quả hơn backtracking thuần.",
    ),
    RepresentativeAlgorithm(
        group_id=6,
        group_name="Tìm kiếm đối kháng",
        algorithm="ALPHA_BETA",
        reason="Cho kết quả như Minimax nhưng duyệt ít node hơn nhờ cắt tỉa.",
    ),
]


CSV_FIELDS = [
    "map_id",
    "group_id",
    "group_name",
    "algorithm",
    "total_score",
    "total_distance",
    "total_orders",
    "completed_orders",
    "expanded_nodes",
    "runtime_ms",
    "reason",
]


def run_representative_on_map(
    map_id: int,
    representative: RepresentativeAlgorithm,
) -> RunResult:
    group_id = representative.group_id
    algorithm = representative.algorithm

    if group_id in (1, 2):
        return run_pathfinding_benchmark_algorithm(
            map_id=map_id,
            group_id=group_id,
            algorithm=algorithm,
        )

    if group_id == 3:
        return run_local_search_benchmark_algorithm(
            map_id=map_id,
            group_id=group_id,
            algorithm=algorithm,
        )

    if group_id == 4:
        return run_complex_search_benchmark_algorithm(
            map_id=map_id,
            group_id=group_id,
            algorithm=algorithm,
        )

    if group_id == 5:
        return run_csp_benchmark_algorithm(
            map_id=map_id,
            group_id=group_id,
            algorithm=algorithm,
        )

    if group_id == 6:
        return run_adversarial_benchmark_algorithm(
            map_id=map_id,
            group_id=group_id,
            algorithm=algorithm,
        )

    raise ValueError(f"Unsupported representative group: {group_id}")


def run_all_representatives() -> list[tuple[RepresentativeAlgorithm, RunResult]]:
    rows: list[tuple[RepresentativeAlgorithm, RunResult]] = []

    for map_id in (1, 2, 3):
        for representative in REPRESENTATIVES:
            result = run_representative_on_map(
                map_id=map_id,
                representative=representative,
            )

            rows.append((representative, result))

    return rows


def write_representative_csv(
    rows: list[tuple[RepresentativeAlgorithm, RunResult]],
    output_path: Path = OUTPUT_PATH,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for representative, result in rows:
            writer.writerow(
                {
                    "map_id": result.map_id,
                    "group_id": representative.group_id,
                    "group_name": representative.group_name,
                    "algorithm": representative.algorithm,
                    "total_score": round(result.total_score, 4),
                    "total_distance": round(result.total_distance, 4),
                    "total_orders": result.total_orders,
                    "completed_orders": result.completed_orders,
                    "expanded_nodes": result.expanded_nodes,
                    "runtime_ms": round(result.runtime_ms, 4),
                    "reason": representative.reason,
                }
            )


def print_representative_summary(
    rows: list[tuple[RepresentativeAlgorithm, RunResult]],
) -> None:
    current_map_id: int | None = None

    for representative, result in rows:
        if current_map_id != result.map_id:
            current_map_id = result.map_id
            print(f"Map {current_map_id} - Representative Algorithms")

        print(
            f"- Group {representative.group_id} | {representative.algorithm}: "
            f"score={round(result.total_score, 2)}, "
            f"distance={round(result.total_distance, 2)}, "
            f"completed={result.completed_orders}/{result.total_orders or result.completed_orders}, "
            f"expanded={result.expanded_nodes}, "
            f"runtime_ms={round(result.runtime_ms, 4)}"
        )

        if representative.group_id == 6:
            print("  Note: Group 6 dùng utility đối kháng, không so trực tiếp distance với nhóm 1-5.")

        print(f"  Reason: {representative.reason}")

    print("-" * 100)


if __name__ == "__main__":
    representative_rows = run_all_representatives()
    print_representative_summary(representative_rows)
    write_representative_csv(representative_rows)

    print(f"Saved representative comparison to: {OUTPUT_PATH}")
