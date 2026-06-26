from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AutoMapConfig:
    map_id: int
    difficulty: str
    capacity: int
    order_count: int
    deadline_seconds: float
    traffic_delay_seconds: float
    description: str


AUTO_MAP_CONFIGS = {
    1: AutoMapConfig(
        map_id=1,
        difficulty="EASY",
        capacity=1,
        order_count=6,
        deadline_seconds=240.0,
        traffic_delay_seconds=2.0,
        description="Map 1 dễ: thành phố sáng, đường lưới rõ, ít bất định.",
    ),
    2: AutoMapConfig(
        map_id=2,
        difficulty="MEDIUM",
        capacity=2,
        order_count=6,
        deadline_seconds=200.0,
        traffic_delay_seconds=3.0,
        description="Map 2 trung bình: map tuyết, cầu, sông, vòng xuyến, chi phí di chuyển cao hơn.",
    ),
    3: AutoMapConfig(
        map_id=3,
        difficulty="HARD",
        capacity=3,
        order_count=6,
        deadline_seconds=160.0,
        traffic_delay_seconds=3.0,
        description="Map 3 khó: mùa thu, nhiều đường chéo, nhiều giao lộ và nhiều nhánh lựa chọn.",
    ),
}


def get_auto_map_config(map_id: int) -> AutoMapConfig:
    return AUTO_MAP_CONFIGS.get(map_id, AUTO_MAP_CONFIGS[1])