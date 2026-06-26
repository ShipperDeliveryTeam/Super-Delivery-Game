from __future__ import annotations

import csv
import io
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.gameplay.auto.maps.registry import get_auto_map_profile


GridPos = tuple[int, int]


@dataclass(frozen=True)
class TmxObject:
    id: int
    name: str
    type: str
    x: float
    y: float
    width: float
    height: float
    grid_pos: GridPos
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class AutoMapData:
    map_id: int
    name: str
    difficulty: str
    width: int
    height: int
    tile_width: int
    tile_height: int

    road_grid: list[list[int]]
    collision_grid: list[list[int]]

    pickup_points: list[TmxObject]
    delivery_points: list[TmxObject]
    player_spawns: list[TmxObject]
    npc_spawns: list[TmxObject]
    traffic_traps: list[TmxObject]
    block_traps: list[TmxObject]

    tmx_path: Path

    def in_bounds(self, pos: GridPos) -> bool:
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, pos: GridPos) -> bool:
        if not self.in_bounds(pos):
            return False

        x, y = pos

        # Road_AI = 0 nghĩa là không phải đường AI đi được.
        if self.road_grid[y][x] == 0:
            return False

        # Collision = 2 xem là hard block.
        if self.collision_grid[y][x] == 2:
            return False

        return True

    def movement_cost(self, pos: GridPos) -> float:
        if not self.is_walkable(pos):
            return float("inf")

        x, y = pos
        road_value = self.road_grid[y][x]

        # Road_AI = 1: đường thường.
        # Road_AI = 2, 3, 4...: có thể xem là đường cost cao hơn.
        return max(1, road_value)

    def pixel_to_grid(self, x: float, y: float) -> GridPos:
        return int(x // self.tile_width), int(y // self.tile_height)

    def nearest_walkable(self, pos: GridPos) -> GridPos:
        """
        Trả về ô walkable gần nhất.

        Một số TMX có thể thiếu Player spawn hoặc spawn nằm lệch khỏi Road_AI.
        Hàm này giúp Auto-Mode không rơi về (0, 0) không đi được.
        """
        if self.is_walkable(pos):
            return pos

        start_x, start_y = pos
        max_radius = max(self.width, self.height)

        for radius in range(1, max_radius + 1):
            candidates: list[GridPos] = []

            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if max(abs(dx), abs(dy)) != radius:
                        continue

                    candidate = (start_x + dx, start_y + dy)
                    if self.is_walkable(candidate):
                        candidates.append(candidate)

            if candidates:
                return min(
                    candidates,
                    key=lambda item: abs(item[0] - start_x) + abs(item[1] - start_y),
                )

        for y in range(self.height):
            for x in range(self.width):
                if self.is_walkable((x, y)):
                    return (x, y)

        return pos

    @property
    def start_position(self) -> GridPos:
        if self.player_spawns:
            return self.nearest_walkable(self.player_spawns[0].grid_pos)

        if self.npc_spawns:
            return self.nearest_walkable(self.npc_spawns[0].grid_pos)

        if self.pickup_points:
            return self.nearest_walkable(self.pickup_points[0].grid_pos)

        return self.nearest_walkable((0, 0))


def _parse_csv_layer(layer: ET.Element, width: int, height: int) -> list[list[int]]:
    data = layer.find("data")

    if data is None or data.text is None:
        raise ValueError(f"Layer '{layer.get('name')}' has no CSV data.")

    rows: list[list[int]] = []
    reader = csv.reader(io.StringIO(data.text.strip()))

    for row in reader:
        cleaned = [cell.strip() for cell in row if cell.strip() != ""]
        if cleaned:
            rows.append([int(value) for value in cleaned])

    if len(rows) != height:
        raise ValueError(
            f"Layer '{layer.get('name')}' expected {height} rows, got {len(rows)}."
        )

    for index, row in enumerate(rows):
        if len(row) != width:
            raise ValueError(
                f"Layer '{layer.get('name')}' row {index} expected {width} columns, got {len(row)}."
            )

    return rows


def _parse_properties(obj: ET.Element) -> dict[str, Any]:
    result: dict[str, Any] = {}

    properties = obj.find("properties")
    if properties is None:
        return result

    for prop in properties.findall("property"):
        name = prop.get("name")
        if not name:
            continue

        value_type = prop.get("type", "string")
        raw_value = prop.get("value", "")

        if value_type == "int":
            result[name] = int(raw_value)
        elif value_type == "float":
            result[name] = float(raw_value)
        elif value_type == "bool":
            result[name] = raw_value.lower() == "true"
        else:
            result[name] = raw_value

    return result


def _parse_objects(
    object_group: ET.Element,
    tile_width: int,
    tile_height: int,
) -> list[TmxObject]:
    objects: list[TmxObject] = []

    for obj in object_group.findall("object"):
        x = float(obj.get("x", "0"))
        y = float(obj.get("y", "0"))
        width = float(obj.get("width", "0"))
        height = float(obj.get("height", "0"))

        grid_pos = int(x // tile_width), int(y // tile_height)

        objects.append(
            TmxObject(
                id=int(obj.get("id", "0")),
                name=obj.get("name", ""),
                type=obj.get("type", ""),
                x=x,
                y=y,
                width=width,
                height=height,
                grid_pos=grid_pos,
                properties=_parse_properties(obj),
            )
        )

    return objects


def load_auto_map(map_id: int) -> AutoMapData:
    profile = get_auto_map_profile(map_id)

    tree = ET.parse(profile.tmx_path)
    root = tree.getroot()

    width = int(root.get("width", "0"))
    height = int(root.get("height", "0"))
    tile_width = int(root.get("tilewidth", "32"))
    tile_height = int(root.get("tileheight", "32"))

    layer_by_name = {
        layer.get("name"): layer
        for layer in root.findall("layer")
    }

    if "Road_AI" not in layer_by_name:
        raise ValueError(f"{profile.tmx_path.name}: missing Road_AI layer.")

    if "Collision" not in layer_by_name:
        raise ValueError(f"{profile.tmx_path.name}: missing Collision layer.")

    road_grid = _parse_csv_layer(layer_by_name["Road_AI"], width, height)
    collision_grid = _parse_csv_layer(layer_by_name["Collision"], width, height)

    object_group = None
    for group in root.findall("objectgroup"):
        if group.get("name") == "Objects":
            object_group = group
            break

    if object_group is None:
        raise ValueError(f"{profile.tmx_path.name}: missing Objects group.")

    objects = _parse_objects(object_group, tile_width, tile_height)

    pickup_points = [obj for obj in objects if obj.type == "PickupPoint"]
    delivery_points = [obj for obj in objects if obj.type == "DeliveryPoint"]
    player_spawns = [obj for obj in objects if obj.type == "Player"]
    npc_spawns = [obj for obj in objects if obj.type == "NPC"]
    traffic_traps = [obj for obj in objects if obj.type == "TrafficTrap"]
    block_traps = [obj for obj in objects if obj.type == "BlockTrap"]

    return AutoMapData(
        map_id=profile.map_id,
        name=profile.name,
        difficulty=profile.difficulty,
        width=width,
        height=height,
        tile_width=tile_width,
        tile_height=tile_height,
        road_grid=road_grid,
        collision_grid=collision_grid,
        pickup_points=pickup_points,
        delivery_points=delivery_points,
        player_spawns=player_spawns,
        npc_spawns=npc_spawns,
        traffic_traps=traffic_traps,
        block_traps=block_traps,
        tmx_path=profile.tmx_path,
    )


def print_auto_map_summary(map_id: int) -> None:
    map_data = load_auto_map(map_id)

    walkable_count = 0

    for y in range(map_data.height):
        for x in range(map_data.width):
            if map_data.is_walkable((x, y)):
                walkable_count += 1

    print(f"Map {map_data.map_id}: {map_data.name}")
    print(f"Difficulty: {map_data.difficulty}")
    print(f"Size: {map_data.width} x {map_data.height}")
    print(f"Start: {map_data.start_position}")
    print(f"Walkable cells: {walkable_count}")
    print(f"PickupPoint: {len(map_data.pickup_points)}")
    print(f"DeliveryPoint: {len(map_data.delivery_points)}")
    print(f"Player spawns: {len(map_data.player_spawns)}")
    print(f"NPC spawns: {len(map_data.npc_spawns)}")
    print(f"TrafficTrap: {len(map_data.traffic_traps)}")
    print(f"BlockTrap: {len(map_data.block_traps)}")
    print("-" * 40)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        print_auto_map_summary(current_map_id)