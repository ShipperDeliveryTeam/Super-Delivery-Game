from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from src.gameplay.auto.config import get_auto_map_config


BENCHMARK_CSV = Path("data") / "auto_benchmark_results.csv"
REPRESENTATIVE_CSV = Path("data") / "representative_comparison.csv"
OUTPUT_MD = Path("data") / "AUTO_MODE_RESULTS_SUMMARY.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def to_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def to_int(value: str) -> int:
    try:
        return int(float(value))
    except ValueError:
        return 0


def total_orders_for_row(row: dict[str, str]) -> int:
    if row.get("total_orders"):
        return max(1, to_int(row["total_orders"]))

    map_id = to_int(row.get("map_id", "1")) or 1
    return get_auto_map_config(map_id).order_count


def completed_text(row: dict[str, str]) -> str:
    return f"{row['completed_orders']}/{total_orders_for_row(row)}"


def build_group_summary(rows: list[dict[str, str]]) -> str:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    for row in rows:
        grouped[(row["map_id"], row["algorithm_group"])].append(row)

    lines: list[str] = []
    lines.append("# Tổng kết kết quả Benchmark Auto-Mode")
    lines.append("")
    lines.append("## 1. Kết quả so sánh theo từng nhóm thuật toán")
    lines.append("")

    for (map_id, group_id), group_rows in sorted(
        grouped.items(),
        key=lambda item: (int(item[0][0]), int(item[0][1])),
    ):
        ranked = sorted(
            group_rows,
            key=lambda row: to_int(row["rank"]),
        )

        lines.append(f"### Map {map_id} - Nhóm {group_id}")
        lines.append("")
        lines.append("| Hạng | Thuật toán | Completed | Score | Distance/Cost | Expanded Nodes | Runtime ms |")
        lines.append("|---:|---|---:|---:|---:|---:|---:|")

        for row in ranked:
            lines.append(
                f"| {row['rank']} "
                f"| {row['algorithm']} "
                f"| {completed_text(row)} "
                f"| {round(to_float(row['total_score']), 2)} "
                f"| {round(to_float(row['total_distance']), 2)} "
                f"| {row['expanded_nodes']} "
                f"| {round(to_float(row['runtime_ms']), 4)} |"
            )

        best = ranked[0]
        lines.append("")
        lines.append(
            f"Nhận xét: Trên Map {map_id}, thuật toán đứng đầu nhóm {group_id} là "
            f"**{best['algorithm']}** với score = {round(to_float(best['total_score']), 2)}."
        )
        lines.append("")

    return "\n".join(lines)


def build_representative_summary(rows: list[dict[str, str]]) -> str:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in rows:
        grouped[row["map_id"]].append(row)

    lines: list[str] = []
    lines.append("## 2. So sánh 6 thuật toán đại diện")
    lines.append("")
    lines.append("Các thuật toán đại diện được chọn:")
    lines.append("")
    lines.append("- Nhóm 1: UCS")
    lines.append("- Nhóm 2: A*")
    lines.append("- Nhóm 3: Local Beam")
    lines.append("- Nhóm 4: AND-OR Search")
    lines.append("- Nhóm 5: Forward Checking")
    lines.append("- Nhóm 6: Alpha-Beta")
    lines.append("")

    for map_id, map_rows in sorted(grouped.items(), key=lambda item: int(item[0])):
        lines.append(f"### Map {map_id} - Thuật toán đại diện")
        lines.append("")
        lines.append("| Nhóm | Thuật toán | Score | Distance/Cost | Completed | Expanded Nodes | Runtime ms | Lý do chọn |")
        lines.append("|---:|---|---:|---:|---:|---:|---:|---|")

        sorted_rows = sorted(
            map_rows,
            key=lambda row: int(row["group_id"]),
        )

        for row in sorted_rows:
            lines.append(
                f"| {row['group_id']} "
                f"| {row['algorithm']} "
                f"| {round(to_float(row['total_score']), 2)} "
                f"| {round(to_float(row['total_distance']), 2)} "
                f"| {completed_text(row)} "
                f"| {row['expanded_nodes']} "
                f"| {round(to_float(row['runtime_ms']), 4)} "
                f"| {row['reason']} |"
            )

        lines.append("")

    lines.append("Lưu ý: Nhóm 6 là nhóm tìm kiếm đối kháng nên score thể hiện utility cạnh tranh, không nên so trực tiếp total_distance với các nhóm giao hàng tuần tự.")
    lines.append("")

    return "\n".join(lines)


def build_final_conclusion() -> str:
    return """
## 3. Kết luận chung

Từ kết quả thực nghiệm, có thể rút ra một số nhận xét chính:

- UCS ổn định hơn BFS và DFS trên bản đồ có trọng số vì luôn ưu tiên đường có tổng chi phí thấp.
- A* là thuật toán đại diện phù hợp cho nhóm tìm kiếm có thông tin vì cân bằng tốt giữa chi phí đường đi và số node mở rộng.
- IDA* có thể tìm được đường tốt nhưng dễ tốn thời gian khi chạy nhiều chặng trên bản đồ có cost phức tạp, điển hình là Map 2.
- Local Beam phù hợp cho bài toán tối ưu thứ tự nhận/giao vì có khả năng thoát khỏi cực trị cục bộ.
- AND-OR Search phù hợp với môi trường bất định vì xét đến trường hợp rủi ro hoặc worst-case.
- Forward Checking hiệu quả hơn Backtracking thuần vì có khả năng loại nhánh sớm khi vi phạm ràng buộc.
- Alpha-Beta cho kết quả tương đương Minimax nhưng mở rộng ít node hơn nhờ cơ chế cắt tỉa.

Nhìn chung, hệ thống Auto-Mode đã mô phỏng được đầy đủ 6 nhóm thuật toán AI trên cùng một bài toán giao hàng, cho phép so sánh theo các tiêu chí: số đơn hoàn thành, tổng chi phí, điểm số, số node mở rộng và thời gian chạy.
"""


def main() -> None:
    benchmark_rows = read_csv(BENCHMARK_CSV)
    representative_rows = read_csv(REPRESENTATIVE_CSV)

    content = "\n\n".join(
        [
            build_group_summary(benchmark_rows),
            build_representative_summary(representative_rows),
            build_final_conclusion(),
        ]
    )

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(content, encoding="utf-8")

    print(f"Saved report summary to: {OUTPUT_MD}")


if __name__ == "__main__":
    main()
