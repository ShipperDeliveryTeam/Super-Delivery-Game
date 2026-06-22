from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.systems.stats_analyzer import StatsAnalyzer


def main():
    analyzer = StatsAnalyzer(PROJECT_ROOT / "stats.csv")
    rows = analyzer.load_rows()

    if not rows:
        print("[WARN] Chưa có stats.csv hoặc stats.csv chưa có dữ liệu.")
        print("Hãy chơi game đến khi thắng/thua ít nhất 1 lần để tạo dữ liệu.")
        return

    summary_path = analyzer.save_summary_csv(
        PROJECT_ROOT / "assets" / "images" / "algorithm_summary.csv"
    )
    print(f"[OK] Saved summary: {summary_path}")

    try:
        chart_paths = analyzer.generate_charts(PROJECT_ROOT / "assets" / "images")
    except ImportError as exc:
        print(f"[ERROR] {exc}")
        print("Cài thư viện bằng lệnh:")
        print("pip install matplotlib")
        return

    for path in chart_paths:
        print(f"[OK] Saved chart: {path}")


if __name__ == "__main__":
    main()
