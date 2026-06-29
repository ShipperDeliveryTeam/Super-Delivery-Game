from __future__ import annotations

from src.gameplay.auto.planner import build_plan_for_map


ALGORITHMS = [
    "BFS",
    "DFS",
    "UCS",
    "GREEDY",
    "ASTAR",
    "IDA_STAR",
]


def test_planner_on_map(map_id: int) -> None:
    print(f"Map {map_id}")

    for algorithm in ALGORITHMS:
        result = build_plan_for_map(
            map_id=map_id,
            algorithm=algorithm,
        )

        status = "OK" if result.success else "FAILED"

        print(
            f"- {algorithm}: {status}, "
            f"completed={result.completed_orders}/{result.total_orders}, "
            f"total_cost={round(result.total_cost, 2)}, "
            f"total_steps={result.total_steps}, "
            f"expanded={result.expanded_nodes}, "
            f"generated={result.generated_nodes}, "
            f"runtime_ms={round(result.runtime_ms, 4)}"
        )

    print("-" * 70)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        test_planner_on_map(current_map_id)
