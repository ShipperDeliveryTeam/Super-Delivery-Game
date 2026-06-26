from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


GridPos = tuple[int, int]


class AutoModeType(str, Enum):
    BENCHMARK = "BENCHMARK"
    COMPETITION = "COMPETITION"


class OrderStatus(str, Enum):
    WAITING = "waiting"
    PICKED = "picked"
    DELIVERED = "delivered"
    LOCKED = "locked"


@dataclass
class AutoOrder:
    id: str
    store_pos: GridPos
    customer_pos: GridPos
    reward: int
    deadline: float
    status: OrderStatus = OrderStatus.WAITING
    holder_name: Optional[str] = None
    picked_at: Optional[float] = None
    delivered_at: Optional[float] = None

    def clone(self) -> "AutoOrder":
        return AutoOrder(
            id=self.id,
            store_pos=self.store_pos,
            customer_pos=self.customer_pos,
            reward=self.reward,
            deadline=self.deadline,
            status=OrderStatus.WAITING,
            holder_name=None,
            picked_at=None,
            delivered_at=None,
        )

    @property
    def target_pos(self) -> GridPos:
        if self.status == OrderStatus.PICKED:
            return self.customer_pos
        return self.store_pos


@dataclass
class AlgorithmStats:
    expanded_nodes: int = 0
    generated_nodes: int = 0
    runtime_ms: float = 0.0
    memory_kb: float = 0.0
    replan_count: int = 0


@dataclass
class AutoShipperState:
    name: str
    algorithm: str
    current_pos: GridPos
    carried_orders: list[str] = field(default_factory=list)
    completed_orders: list[str] = field(default_factory=list)
    current_path: list[GridPos] = field(default_factory=list)
    score: float = 0.0
    total_distance: float = 0.0
    finish_time: float = 0.0
    trap_hits: int = 0
    is_finished: bool = False
    stats: AlgorithmStats = field(default_factory=AlgorithmStats)


@dataclass
class ExperimentConfig:
    map_id: int
    mode: AutoModeType
    algorithm_group: int
    selected_algorithms: list[str]
    start_position: GridPos
    capacity: int
    random_seed: int = 42


@dataclass
class RunResult:
    map_id: int
    mode: AutoModeType
    algorithm_group: int
    algorithm: str
    shipper_name: str
    completed_orders: int
    on_time_orders: int
    late_orders: int
    total_score: float
    total_distance: float
    finish_time: float
    expanded_nodes: int
    runtime_ms: float
    memory_kb: float
    replan_count: int
    trap_hits: int
    rank: int = 0