from __future__ import annotations

import csv
from pathlib import Path

from src.gameplay.auto.benchmark_runner import run_benchmark_group
from src.gameplay.auto.models import RunResult


DEFAULT_OUTPUT_PATH = Path("data") / "auto_benchmark_results.csv"


CSV_FIELDS = [
    "map_id",
    "mode",
    "algorithm_group",
    "algorithm",
    "shipper_name",
    "rank",
    "completed_orders",
    "on_time_orders",
    "late_orders",
    "total_score",
    "total_distance",
    "finish_time",
    "expanded_nodes",
    "runtime_ms",
    "memory_kb",
    "replan_count",
    "trap_hits",
]


def run_result_to_row(result: RunResult) -> dict[str, object]:
    return {
        "map_id": result.map_id,
        "mode": result.mode.value if hasattr(result.mode, "value") else str(result.mode),
        "algorithm_group": result.algorithm_group,
        "algorithm": result.algorithm,
        "shipper_name": result.shipper_name,
        "rank": result.rank,
        "completed_orders": result.completed_orders,
        "on_time_orders": result.on_time_orders,
        "late_orders": result.late_orders,
        "total_score": round(result.total_score, 4),
        "total_distance": round(result.total_distance, 4),
        "finish_time": round(result.finish_time, 4),
        "expanded_nodes": result.expanded_nodes,
        "runtime_ms": round(result.runtime_ms, 4),
        "memory_kb": round(result.memory_kb, 4),
        "replan_count": result.replan_count,
        "trap_hits": result.trap_hits,
    }


def write_results_to_csv(
    results: list[RunResult],
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for result in results:
            writer.writerow(run_result_to_row(result))


def run_basic_pathfinding_benchmark() -> list[RunResult]:
    """
    Chạy benchmark cho nhóm 1 và nhóm 2 trên cả 3 map.

    Nhóm 1:
    - BFS
    - DFS
    - UCS

    Nhóm 2:
    - Greedy
    - A*
    - IDA*
    """
    all_results: list[RunResult] = []

    for map_id in (1, 2, 3):
        for group_id in (1, 2, 3, 4, 5, 6):
            group_results = run_benchmark_group(
                map_id=map_id,
                group_id=group_id,
            )

            all_results.extend(group_results)

    return all_results


def save_basic_pathfinding_benchmark(
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> None:
    results = run_basic_pathfinding_benchmark()
    write_results_to_csv(results, output_path)

    print(f"Saved {len(results)} benchmark rows to: {output_path}")


if __name__ == "__main__":
    save_basic_pathfinding_benchmark()