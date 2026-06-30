from __future__ import annotations

import random
from dataclasses import dataclass

from src.ai.pathfinding.grid_search import bfs_grid_path, dijkstra_grid_path
from src.gameplay.auto.maps.graph_adapter import AutoMapGraph
from src.gameplay.auto.maps.tmx_loader import AutoMapData, GridPos
from src.gameplay.auto.models import AutoOrder


TRAP_COUNT_BY_MAP = {
    1: 3,
    2: 3,
    3: 3,
}


@dataclass(frozen=True)
class HiddenTrapSetup:
    traps: tuple[GridPos, ...]
    possible_traps: tuple[GridPos, ...]


def trap_count_for_map(map_id: int) -> int:
    return TRAP_COUNT_BY_MAP.get(map_id, 3)


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


def _shortest_visual_path(map_data: AutoMapData, start: GridPos, goal: GridPos) -> list[GridPos]:
    graph = AutoMapGraph(map_data)
    return bfs_grid_path(start, goal, graph.get_neighbors)


def _cost_aware_path(map_data: AutoMapData, start: GridPos, goal: GridPos, traps: set[GridPos]) -> list[GridPos]:
    graph = AutoMapGraph(map_data, trap_cells=traps)
    path, _ = dijkstra_grid_path(start, goal, graph.get_neighbors)
    return path


def _manhattan(a: GridPos, b: GridPos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _pick_spread_cells(candidates: list[GridPos], fallback_cells: list[GridPos], count: int) -> tuple[GridPos, ...]:
    pool: list[GridPos] = []
    seen = set()

    for pos in candidates + fallback_cells:
        if pos in seen:
            continue

        seen.add(pos)
        pool.append(pos)

    if len(pool) <= count:
        return tuple(pool)

    selected: list[GridPos] = []
    preferred_indexes = [
        round(index * (len(candidates) - 1) / max(1, count - 1))
        for index in range(count)
    ] if candidates else []

    for preferred_index in preferred_indexes:
        best_pos = None
        best_score = -1

        for offset in range(len(pool)):
            for candidate_index in (preferred_index - offset, preferred_index + offset):
                if not 0 <= candidate_index < len(pool):
                    continue

                pos = pool[candidate_index]
                if pos in selected:
                    continue

                distance_to_selected = min((_manhattan(pos, item) for item in selected), default=999)
                if distance_to_selected < 6:
                    continue

                score = distance_to_selected - offset
                if score > best_score:
                    best_score = score
                    best_pos = pos

            if best_pos is not None:
                break

        if best_pos is not None:
            selected.append(best_pos)

    for pos in pool:
        if len(selected) >= count:
            break
        if pos in selected:
            continue
        if min((_manhattan(pos, item) for item in selected), default=999) < 4:
            continue
        selected.append(pos)

    for pos in pool:
        if len(selected) >= count:
            break
        if pos not in selected:
            selected.append(pos)

    return tuple(selected[:count])


def build_hidden_traps(map_data: AutoMapData, orders: list[AutoOrder]) -> tuple[GridPos, ...]:
    count = trap_count_for_map(map_data.map_id)
    rng = random.Random(map_data.map_id * 500 + 17)
    map_traps = tuple(
        obj.grid_pos
        for obj in map_data.traffic_traps + map_data.block_traps
    )

    if map_traps:
        return map_traps[:count]

    blocked = {map_data.start_position}
    for order in orders:
        blocked.add(order.store_pos)
        blocked.add(order.customer_pos)

    candidates: list[GridPos] = []
    seen = set()
    current = map_data.start_position

    for order in orders:
        for goal in (order.store_pos, order.customer_pos):
            path = _shortest_visual_path(map_data, current, goal)
            if len(path) > 8:
                for pos in path[3:-3]:
                    if pos in blocked or pos in seen:
                        continue

                    detour = _cost_aware_path(map_data, current, goal, {pos})
                    if not detour or pos in detour:
                        continue

                    seen.add(pos)
                    candidates.append(pos)
            current = goal

    fallback_cells = list(build_possible_trap_cells(map_data, orders))
    rng.shuffle(fallback_cells)
    fallback_cells = [pos for pos in fallback_cells if pos not in seen]

    return _pick_spread_cells(candidates, fallback_cells, count)



def build_trap_setup(map_data: AutoMapData, orders: list[AutoOrder], algorithm: str) -> HiddenTrapSetup:
    traps = build_hidden_traps(map_data, orders)
    possible_traps = build_possible_trap_cells(map_data, orders)

    return HiddenTrapSetup(
        traps=traps,
        possible_traps=possible_traps,
    )
