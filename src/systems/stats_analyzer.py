import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List


class StatsAnalyzer:
    def __init__(self, stats_path: str | Path = "stats.csv"):
        self.stats_path = Path(stats_path)

    def load_rows(self) -> List[Dict[str, str]]:
        if not self.stats_path.exists():
            return []

        with self.stats_path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    def summarize_by_algorithm(self) -> List[Dict[str, Any]]:
        rows = self.load_rows()
        grouped = defaultdict(list)

        for row in rows:
            algorithm = row.get("player_algorithm", "UNKNOWN") or "UNKNOWN"
            grouped[algorithm].append(row)

        summary = []

        for algorithm, items in grouped.items():
            elapsed_values = [self._to_float(row.get("elapsed_time")) for row in items]
            money_values = [self._to_float(row.get("player_money")) for row in items]
            order_values = [self._to_float(row.get("player_orders")) for row in items]
            expanded_values = [self._to_float(row.get("player_expanded_nodes")) for row in items]
            win_values = [1 if str(row.get("player_win", "")).lower() == "true" else 0 for row in items]

            summary.append({
                "algorithm": algorithm,
                "runs": len(items),
                "win_rate": round(mean(win_values) * 100, 2) if win_values else 0,
                "avg_elapsed_time": round(mean(elapsed_values), 2) if elapsed_values else 0,
                "avg_player_money": round(mean(money_values), 2) if money_values else 0,
                "avg_player_orders": round(mean(order_values), 2) if order_values else 0,
                "avg_expanded_nodes": round(mean(expanded_values), 2) if expanded_values else 0,
            })

        summary.sort(key=lambda item: item["algorithm"])
        return summary

    def save_summary_csv(self, output_path: str | Path = "assets/images/algorithm_summary.csv") -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        summary = self.summarize_by_algorithm()

        fieldnames = [
            "algorithm",
            "runs",
            "win_rate",
            "avg_elapsed_time",
            "avg_player_money",
            "avg_player_orders",
            "avg_expanded_nodes",
        ]

        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary)

        return output_path

    def generate_charts(self, output_dir: str | Path = "assets/images") -> list[Path]:
        try:
            import matplotlib.pyplot as plt
        except ImportError as exc:
            raise ImportError("Thiếu matplotlib. Cài bằng lệnh: pip install matplotlib") from exc

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        summary = self.summarize_by_algorithm()

        if not summary:
            return []

        algorithms = [item["algorithm"] for item in summary]

        chart_specs = [
            ("completion_time.png", "Average Completion Time", "Seconds", [item["avg_elapsed_time"] for item in summary]),
            ("expanded_nodes.png", "Average Expanded Nodes", "Nodes", [item["avg_expanded_nodes"] for item in summary]),
            ("collected_coins.png", "Average Money Collected", "Money", [item["avg_player_money"] for item in summary]),
            ("orders_completed.png", "Average Orders Completed", "Orders", [item["avg_player_orders"] for item in summary]),
            ("win_rate.png", "Player Win Rate", "Win Rate (%)", [item["win_rate"] for item in summary]),
        ]

        created_paths = []

        for filename, title, ylabel, values in chart_specs:
            fig = plt.figure(figsize=(9, 5))
            ax = fig.add_subplot(111)

            ax.bar(algorithms, values)
            ax.set_title(title)
            ax.set_xlabel("Algorithm")
            ax.set_ylabel(ylabel)
            ax.tick_params(axis="x", rotation=20)
            ax.grid(axis="y", alpha=0.25)

            fig.tight_layout()

            path = output_dir / filename
            fig.savefig(path, dpi=150)
            plt.close(fig)

            created_paths.append(path)

        return created_paths

    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0
