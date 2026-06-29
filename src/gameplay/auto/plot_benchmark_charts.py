from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


REPRESENTATIVE_CSV = Path("data") / "representative_comparison.csv"
BENCHMARK_CSV = Path("data") / "auto_benchmark_results.csv"
OUTPUT_DIR = Path("data") / "charts"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV file: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def to_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def grouped_bar_chart(
    title: str,
    ylabel: str,
    output_path: Path,
    x_labels: list[str],
    series_data: dict[str, list[float]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    series_names = list(series_data.keys())
    x_positions = list(range(len(x_labels)))

    if not series_names:
        return

    bar_width = 0.8 / len(series_names)

    plt.figure(figsize=(14, 7))

    for index, series_name in enumerate(series_names):
        offset = (index - len(series_names) / 2) * bar_width + bar_width / 2
        values = series_data[series_name]
        positions = [x + offset for x in x_positions]

        plt.bar(
            positions,
            values,
            width=bar_width,
            label=series_name,
        )

    plt.title(title)
    plt.xlabel("Map")
    plt.ylabel(ylabel)
    plt.xticks(x_positions, x_labels)
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_representative_charts() -> None:
    rows = read_csv_rows(REPRESENTATIVE_CSV)

    map_ids = sorted({row["map_id"] for row in rows}, key=int)
    x_labels = [f"Map {map_id}" for map_id in map_ids]

    algorithms = [
        "UCS",
        "ASTAR",
        "LOCAL_BEAM",
        "AND_OR_SEARCH",
        "FORWARD_CHECKING",
        "ALPHA_BETA",
    ]

    def build_series(metric: str, skip_group_6: bool = False) -> dict[str, list[float]]:
        series: dict[str, list[float]] = {}

        for algorithm in algorithms:
            values: list[float] = []

            for map_id in map_ids:
                matched_row = None

                for row in rows:
                    if row["map_id"] == map_id and row["algorithm"] == algorithm:
                        matched_row = row
                        break

                if matched_row is None:
                    values.append(0.0)
                    continue

                if skip_group_6 and matched_row["group_id"] == "6":
                    values.append(0.0)
                    continue

                values.append(to_float(matched_row[metric]))

            series[algorithm] = values

        return series

    grouped_bar_chart(
        title="Representative Algorithms - Total Score by Map",
        ylabel="Total Score",
        output_path=OUTPUT_DIR / "representative_score_by_map.png",
        x_labels=x_labels,
        series_data=build_series("total_score"),
    )

    grouped_bar_chart(
        title="Representative Algorithms - Runtime by Map",
        ylabel="Runtime (ms)",
        output_path=OUTPUT_DIR / "representative_runtime_by_map.png",
        x_labels=x_labels,
        series_data=build_series("runtime_ms"),
    )

    grouped_bar_chart(
        title="Representative Algorithms - Expanded Nodes by Map",
        ylabel="Expanded Nodes",
        output_path=OUTPUT_DIR / "representative_expanded_nodes_by_map.png",
        x_labels=x_labels,
        series_data=build_series("expanded_nodes"),
    )

    # Group 6 là đối kháng nên total_distance = 0, không so distance trực tiếp.
    distance_series = build_series("total_distance", skip_group_6=True)
    distance_series.pop("ALPHA_BETA", None)

    grouped_bar_chart(
        title="Representative Algorithms - Distance by Map",
        ylabel="Total Distance / Cost",
        output_path=OUTPUT_DIR / "representative_distance_by_map.png",
        x_labels=x_labels,
        series_data=distance_series,
    )


def plot_group_score_charts() -> None:
    rows = read_csv_rows(BENCHMARK_CSV)

    grouped_rows: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    for row in rows:
        grouped_rows[(row["map_id"], row["algorithm_group"])].append(row)

    for (map_id, group_id), group_rows in sorted(
        grouped_rows.items(),
        key=lambda item: (int(item[0][0]), int(item[0][1])),
    ):
        algorithms = [row["algorithm"] for row in group_rows]
        scores = [to_float(row["total_score"]) for row in group_rows]
        runtimes = [to_float(row["runtime_ms"]) for row in group_rows]
        expanded_nodes = [to_float(row["expanded_nodes"]) for row in group_rows]

        plt.figure(figsize=(10, 6))
        plt.bar(algorithms, scores)
        plt.title(f"Map {map_id} - Group {group_id} Score Comparison")
        plt.xlabel("Algorithm")
        plt.ylabel("Total Score")
        plt.grid(axis="y", linestyle="--", alpha=0.4)
        plt.xticks(rotation=20)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"map_{map_id}_group_{group_id}_score.png", dpi=200)
        plt.close()

        plt.figure(figsize=(10, 6))
        plt.bar(algorithms, runtimes)
        plt.title(f"Map {map_id} - Group {group_id} Runtime Comparison")
        plt.xlabel("Algorithm")
        plt.ylabel("Runtime (ms)")
        plt.grid(axis="y", linestyle="--", alpha=0.4)
        plt.xticks(rotation=20)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"map_{map_id}_group_{group_id}_runtime.png", dpi=200)
        plt.close()

        plt.figure(figsize=(10, 6))
        plt.bar(algorithms, expanded_nodes)
        plt.title(f"Map {map_id} - Group {group_id} Expanded Nodes Comparison")
        plt.xlabel("Algorithm")
        plt.ylabel("Expanded Nodes")
        plt.grid(axis="y", linestyle="--", alpha=0.4)
        plt.xticks(rotation=20)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"map_{map_id}_group_{group_id}_expanded_nodes.png", dpi=200)
        plt.close()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    plot_representative_charts()
    plot_group_score_charts()

    print(f"Saved charts to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()