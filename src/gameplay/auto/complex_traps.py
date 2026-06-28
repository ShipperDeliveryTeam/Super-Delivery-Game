from __future__ import annotations

import random
from dataclasses import dataclass

from src.gameplay.auto.maps.tmx_loader import AutoMapData, GridPos
from src.gameplay.auto.models import AutoOrder


TRAP_COUNT_BY_MAP = {
    1: 6,
    2: 6,
    3: 8,
}


@dataclass(frozen=True)
class HiddenTrapSetup:
    traps: tuple[GridPos, ...]
    possible_traps: tuple[GridPos, ...]


def trap_count_for_map(map_id: int) -> int:
    return TRAP_COUNT_BY_MAP.get(map_id, 6)


def build_possible_trap_cells(map_data: AutoMapData, orders: list[AutoOrder]) -> tuple[GridPos, ...]:
    blocked = {map_data.start_position}
    for order in orders:
        blocked.add(order.store_pos)
        blocked.add(order.customer_pos)

    cells: list[GridPos] = []
    for y in range(map_data.height):
        for x in range(map_data.width):
            pos = (x, y)
            if pos in blocked:
                continue
            if map_data.is_walkable(pos):
                cells.append(pos)

    return tuple(cells)


def build_hidden_traps(map_data: AutoMapData, orders: list[AutoOrder]) -> tuple[GridPos, ...]:
    count = trap_count_for_map(map_data.map_id)
    rng = random.Random(map_data.map_id * 500 + 17)

    cells = list(build_possible_trap_cells(map_data, orders))
    rng.shuffle(cells)
    return tuple(cells[:count])


def build_trap_setup(map_data: AutoMapData, orders: list[AutoOrder], algorithm: str) -> HiddenTrapSetup:
    traps = build_hidden_traps(map_data, orders)
    possible_traps = build_possible_trap_cells(map_data, orders)

    return HiddenTrapSetup(
        traps=traps,
        possible_traps=possible_traps,
    )
