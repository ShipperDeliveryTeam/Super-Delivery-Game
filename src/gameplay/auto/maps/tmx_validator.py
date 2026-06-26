from __future__ import annotations

import csv
import io
import xml.etree.ElementTree as ET
from pathlib import Path

from src.gameplay.auto.maps.registry import get_all_auto_map_profiles


REQUIRED_LAYERS = {"Road_AI", "Collision"}
REQUIRED_OBJECT_GROUP = "Objects"

EXPECTED_PICKUP_COUNT = 6
EXPECTED_DELIVERY_COUNT = 6
EXPECTED_PLAYER_COUNT = 1
EXPECTED_NPC_COUNT = 3


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

    for row_index, row in enumerate(rows):
        if len(row) != width:
            raise ValueError(
                f"Layer '{layer.get('name')}' row {row_index} expected {width} columns, got {len(row)}."
            )

    return rows


def _object_grid_pos(obj: ET.Element, tile_width: int, tile_height: int) -> tuple[int, int]:
    x = float(obj.get("x", "0"))
    y = float(obj.get("y", "0"))

    return int(x // tile_width), int(y // tile_height)


def validate_tmx_file(tmx_path: Path) -> list[str]:
    errors: list[str] = []

    if not tmx_path.exists():
        return [f"Missing TMX file: {tmx_path}"]

    try:
        tree = ET.parse(tmx_path)
        root = tree.getroot()
    except ET.ParseError as exc:
        return [f"XML parse error in {tmx_path}: {exc}"]

    width = int(root.get("width", "0"))
    height = int(root.get("height", "0"))
    tile_width = int(root.get("tilewidth", "32"))
    tile_height = int(root.get("tileheight", "32"))

    layer_by_name = {
        layer.get("name"): layer
        for layer in root.findall("layer")
    }

    for required_layer in REQUIRED_LAYERS:
        if required_layer not in layer_by_name:
            errors.append(f"{tmx_path.name}: missing layer '{required_layer}'.")

    object_group = None
    for group in root.findall("objectgroup"):
        if group.get("name") == REQUIRED_OBJECT_GROUP:
            object_group = group
            break

    if object_group is None:
        errors.append(f"{tmx_path.name}: missing object group '{REQUIRED_OBJECT_GROUP}'.")

    # Kiểm tra đường dẫn tileset không trỏ ra máy cá nhân.
    for tileset in root.findall("tileset"):
        source = tileset.get("source", "")
        normalized = source.replace("\\", "/").lower()

        if "c:/" in normalized or "downloads" in normalized or "tiled/map" in normalized:
            errors.append(
                f"{tmx_path.name}: tileset source should be local, got '{source}'."
            )

    # Kiểm tra image layer không trỏ ra máy cá nhân.
    for image in root.findall(".//image"):
        source = image.get("source", "")
        normalized = source.replace("\\", "/").lower()

        if "c:/" in normalized or "downloads" in normalized:
            errors.append(
                f"{tmx_path.name}: image source should be relative project path, got '{source}'."
            )

    if "Road_AI" not in layer_by_name or "Collision" not in layer_by_name or object_group is None:
        return errors

    try:
        road_grid = _parse_csv_layer(layer_by_name["Road_AI"], width, height)
        collision_grid = _parse_csv_layer(layer_by_name["Collision"], width, height)
    except ValueError as exc:
        errors.append(f"{tmx_path.name}: {exc}")
        return errors

    objects = list(object_group.findall("object"))

    pickup_points = [obj for obj in objects if obj.get("type") == "PickupPoint"]
    delivery_points = [obj for obj in objects if obj.get("type") == "DeliveryPoint"]
    players = [obj for obj in objects if obj.get("type") == "Player"]
    npcs = [obj for obj in objects if obj.get("type") == "NPC"]

    if len(pickup_points) != EXPECTED_PICKUP_COUNT:
        errors.append(
            f"{tmx_path.name}: expected {EXPECTED_PICKUP_COUNT} PickupPoint, got {len(pickup_points)}."
        )

    if len(delivery_points) != EXPECTED_DELIVERY_COUNT:
        errors.append(
            f"{tmx_path.name}: expected {EXPECTED_DELIVERY_COUNT} DeliveryPoint, got {len(delivery_points)}."
        )

    if len(players) < EXPECTED_PLAYER_COUNT:
        errors.append(
            f"{tmx_path.name}: expected at least {EXPECTED_PLAYER_COUNT} Player spawn, got {len(players)}."
        )

    if len(npcs) < EXPECTED_NPC_COUNT:
        errors.append(
            f"{tmx_path.name}: expected at least {EXPECTED_NPC_COUNT} NPC spawn, got {len(npcs)}."
        )

    object_names = [obj.get("name", "") for obj in objects if obj.get("name")]
    duplicated_names = sorted(
        name for name in set(object_names) if object_names.count(name) > 1
    )

    if duplicated_names:
        errors.append(
            f"{tmx_path.name}: duplicated object names: {', '.join(duplicated_names)}."
        )

    important_objects = pickup_points + delivery_points + players + npcs

    for obj in important_objects:
        obj_name = obj.get("name", "(unnamed)")
        obj_type = obj.get("type", "(no type)")
        grid_x, grid_y = _object_grid_pos(obj, tile_width, tile_height)

        if not (0 <= grid_x < width and 0 <= grid_y < height):
            errors.append(
                f"{tmx_path.name}: {obj_type} '{obj_name}' is out of map bounds at ({grid_x}, {grid_y})."
            )
            continue

        if road_grid[grid_y][grid_x] == 0:
            errors.append(
                f"{tmx_path.name}: {obj_type} '{obj_name}' is not on Road_AI at grid ({grid_x}, {grid_y})."
            )

        # Trong file của bạn, GID 2 là collision hard-block. GID 1 có thể là road/cost marker nên chưa xem là lỗi.
        if collision_grid[grid_y][grid_x] == 2:
            errors.append(
                f"{tmx_path.name}: {obj_type} '{obj_name}' is on hard Collision at grid ({grid_x}, {grid_y})."
            )

    return errors


def validate_all_auto_tmx() -> list[str]:
    errors: list[str] = []

    for profile in get_all_auto_map_profiles():
        errors.extend(validate_tmx_file(profile.tmx_path))

    return errors


if __name__ == "__main__":
    result = validate_all_auto_tmx()

    if not result:
        print("OK: All Auto TMX files are valid.")
    else:
        print("Auto TMX validation errors:")
        for error in result:
            print(f"- {error}")