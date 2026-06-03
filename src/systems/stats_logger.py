import csv
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class GameStatsRecord:
    timestamp: str
    map_id: int
    map_source: str
    winner: str
    player_win: bool
    elapsed_time: float
    target_revenue: int

    player_money: int
    player_orders: int
    player_algorithm: str
    player_expanded_nodes: int

    npc_1_money: int = 0
    npc_1_orders: int = 0
    npc_1_algorithm: str = ""
    npc_1_expanded_nodes: int = 0

    npc_2_money: int = 0
    npc_2_orders: int = 0
    npc_2_algorithm: str = ""
    npc_2_expanded_nodes: int = 0

    npc_3_money: int = 0
    npc_3_orders: int = 0
    npc_3_algorithm: str = ""
    npc_3_expanded_nodes: int = 0

    npc_4_money: int = 0
    npc_4_orders: int = 0
    npc_4_algorithm: str = ""
    npc_4_expanded_nodes: int = 0


class StatsLogger:
    def __init__(self, path: str | Path = "stats.csv"):
        self.path = Path(path)

    def write_record(self, record: GameStatsRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        row = asdict(record)
        file_exists = self.path.exists()

        with self.path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))

            if not file_exists:
                writer.writeheader()

            writer.writerow(row)

    @staticmethod
    def now_text() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
