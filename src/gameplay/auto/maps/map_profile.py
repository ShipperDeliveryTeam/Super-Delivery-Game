from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AutoMapProfile:
    map_id: int
    name: str
    difficulty: str

    tmx_path: Path
    image_path: Path

    order_count: int
    capacity: int
    deadline_seconds: float
    traffic_delay_seconds: float

    allow_diagonal: bool
    has_roundabout: bool
    has_hidden_block: bool
    has_random_traffic: bool

    description: str