from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import csv
import xml.etree.ElementTree as ET

import pygame

Grid = List[List[int]]
GridPos = Tuple[int, int]


@dataclass
class TmxMapData:
    path: Path
    width: int
    height: int
    tile_width: int
    tile_height: int
    pixel_width: int
    pixel_height: int
    grid: Grid
    surface: pygame.Surface
    store_positions: list[GridPos]
    house_positions: list[GridPos]
    trap_positions: list[GridPos]
    player_spawn: Optional[GridPos] = None
    npc_spawns: Optional[list[GridPos]] = None


class TmxMapLoader:
    ROAD = 0
    BLOCK = 1
    STORE = 2
    HOUSE = 3
    TRAP = 4
    WATER = 5
    BRIDGE = 6
    ROUNDABOUT = 7

    WALKABLE = {ROAD, STORE, HOUSE, TRAP, BRIDGE, ROUNDABOUT}

    def __init__(self, default_cols: int = 48, default_rows: int = 32, default_tile_size: int = 32):
        self.default_cols = default_cols
        self.default_rows = default_rows
        self.default_tile_size = default_tile_size

    def load(self, path: str | Path) -> TmxMapData:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy file TMX: {path}")

        tree = ET.parse(path)
        root = tree.getroot()

        width = int(root.attrib.get("width", self.default_cols))
        height = int(root.attrib.get("height", self.default_rows))
        tile_width = int(root.attrib.get("tilewidth", self.default_tile_size))
        tile_height = int(root.attrib.get("tileheight", self.default_tile_size))

        pixel_width = width * tile_width
        pixel_height = height * tile_height

        grid: Grid = [[self.BLOCK for _ in range(width)] for _ in range(height)]

        surface = pygame.Surface((pixel_width, pixel_height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))

        store_positions: list[GridPos] = []
        house_positions: list[GridPos] = []
        trap_positions: list[GridPos] = []
        npc_spawns: list[GridPos] = []
        player_spawn: Optional[GridPos] = None

        has_walkable_layer = False

        for image_layer in root.findall("imagelayer"):
            image_node = image_layer.find("image")

            if image_node is None:
                continue

            source = image_node.attrib.get("source", "")
            image_path = self._resolve_image_path(path, source)

            if image_path and image_path.exists():
                try:
                    img = pygame.image.load(str(image_path)).convert_alpha()
                    img = pygame.transform.smoothscale(img, (pixel_width, pixel_height))
                    surface.blit(img, (0, 0))
                except Exception as exc:
                    print(f"[WARN] Không load được image layer {source}: {exc}")
            else:
                print(f"[WARN] Không tìm thấy image layer source: {source}")

        for layer in root.findall("layer"):
            name = layer.attrib.get("name", "").lower().strip()
            w = int(layer.attrib.get("width", width))
            h = int(layer.attrib.get("height", height))
            data_node = layer.find("data")

            if data_node is None:
                continue

            encoding = data_node.attrib.get("encoding", "").lower()

            if encoding != "csv":
                print(f"[WARN] Layer {name} không phải CSV, bỏ qua.")
                continue

            values = self._parse_csv_values(data_node.text or "")
            matrix = self._values_to_matrix(values, w, h)

            if self._contains_any(name, ["ai_walkable", "walkable", "road", "duong"]):
                has_walkable_layer = True

                for y in range(min(height, h)):
                    for x in range(min(width, w)):
                        grid[y][x] = self.ROAD if matrix[y][x] != 0 else self.BLOCK

            elif self._contains_any(name, ["collision", "block", "blocked", "wall", "solid"]):
                for y in range(min(height, h)):
                    for x in range(min(width, w)):
                        if matrix[y][x] != 0:
                            grid[y][x] = self.BLOCK

            elif self._contains_any(name, ["water", "river", "song", "nuoc"]):
                for y in range(min(height, h)):
                    for x in range(min(width, w)):
                        if matrix[y][x] != 0:
                            grid[y][x] = self.WATER

            elif self._contains_any(name, ["trap", "hole", "pothole", "oga", "o_ga"]):
                for y in range(min(height, h)):
                    for x in range(min(width, w)):
                        if matrix[y][x] != 0:
                            grid[y][x] = self.TRAP
                            trap_positions.append((x, y))

        if not has_walkable_layer:
            for y in range(height):
                for x in range(width):
                    if grid[y][x] == self.BLOCK:
                        grid[y][x] = self.ROAD

        for object_group in root.findall("objectgroup"):
            group_name = object_group.attrib.get("name", "").lower().strip()

            for obj in object_group.findall("object"):
                obj_name = obj.attrib.get("name", "").lower().strip()
                obj_type = obj.attrib.get("type", "").lower().strip()
                combined = f"{group_name} {obj_name} {obj_type}"

                gx, gy = self._object_to_grid(obj, tile_width, tile_height, width, height)

                if self._contains_any(combined, ["player", "player_start", "player_spawn", "spawn_player"]):
                    player_spawn = (gx, gy)
                    grid[gy][gx] = self.ROAD

                elif self._contains_any(combined, ["npc", "npc_spawn", "shipper_spawn"]):
                    npc_spawns.append((gx, gy))
                    grid[gy][gx] = self.ROAD

                elif self._contains_any(combined, ["pickup", "pickuppoint", "pickup_point", "store", "shop", "restaurant", "cua_hang", "cuahang"]):
                    grid[gy][gx] = self.STORE
                    store_positions.append((gx, gy))

                elif self._contains_any(combined, ["delivery", "deliverypoint", "delivery_point", "customer", "house", "home", "nha", "khach"]):
                    grid[gy][gx] = self.HOUSE
                    house_positions.append((gx, gy))

                elif self._contains_any(combined, ["trap", "hole", "pothole", "o_ga", "oga"]):
                    grid[gy][gx] = self.TRAP
                    trap_positions.append((gx, gy))

                elif self._contains_any(combined, ["collision", "block", "blocked", "wall", "solid"]):
                    self._paint_object_rect(grid, obj, tile_width, tile_height, width, height, self.BLOCK)

                elif self._contains_any(combined, ["water", "river", "song", "nuoc"]):
                    self._paint_object_rect(grid, obj, tile_width, tile_height, width, height, self.WATER)

                elif self._contains_any(combined, ["road", "path", "walkable", "duong"]):
                    self._paint_object_rect(grid, obj, tile_width, tile_height, width, height, self.ROAD)

        store_positions = self._unique(store_positions)
        house_positions = self._unique(house_positions)
        trap_positions = self._unique(trap_positions)
        npc_spawns = self._unique(npc_spawns)

        for x, y in store_positions:
            grid[y][x] = self.STORE

        for x, y in house_positions:
            grid[y][x] = self.HOUSE

        for x, y in trap_positions:
            grid[y][x] = self.TRAP

        for x, y in npc_spawns:
            if grid[y][x] == self.BLOCK:
                grid[y][x] = self.ROAD

        if player_spawn:
            x, y = player_spawn

            if grid[y][x] == self.BLOCK:
                grid[y][x] = self.ROAD

        return TmxMapData(
            path=path,
            width=width,
            height=height,
            tile_width=tile_width,
            tile_height=tile_height,
            pixel_width=pixel_width,
            pixel_height=pixel_height,
            grid=grid,
            surface=surface,
            store_positions=store_positions,
            house_positions=house_positions,
            trap_positions=trap_positions,
            player_spawn=player_spawn,
            npc_spawns=npc_spawns,
        )

    def blocked_positions(self, grid: Grid) -> set[GridPos]:
        blocked = set()

        for y, row in enumerate(grid):
            for x, value in enumerate(row):
                if value not in self.WALKABLE:
                    blocked.add((x, y))

        return blocked

    def _resolve_image_path(self, tmx_path: Path, source: str) -> Optional[Path]:
        if not source:
            return None

        source = source.replace("\\", "/")
        project_root = Path.cwd()
        tmx_parent = tmx_path.parent.resolve()

        candidates: list[Path] = [
            (tmx_parent / source).resolve(),
            (project_root / source).resolve(),
        ]

        if "../assets/" in source:
            suffix = source.split("../assets/", 1)[1]
            candidates.append((project_root / "assets" / suffix).resolve())

        if "assets/" in source:
            suffix = source.split("assets/", 1)[1]
            candidates.append((project_root / "assets" / suffix).resolve())

        filename = Path(source).name

        candidates.extend([
            (project_root / "assets" / "images" / "map" / filename).resolve(),
            (project_root / "assets" / "images" / filename).resolve(),
            (project_root / "assets" / "maps" / filename).resolve(),
        ])

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return candidates[0] if candidates else None

    def _parse_csv_values(self, text: str) -> list[int]:
        values: list[int] = []

        for row in csv.reader(text.strip().splitlines()):
            for cell in row:
                cell = cell.strip()

                if not cell:
                    continue

                try:
                    values.append(int(cell))
                except ValueError:
                    values.append(0)

        return values

    def _values_to_matrix(self, values: list[int], width: int, height: int) -> Grid:
        matrix: Grid = []
        index = 0

        for _ in range(height):
            row = []

            for _ in range(width):
                row.append(values[index] if index < len(values) else 0)
                index += 1

            matrix.append(row)

        return matrix

    def _object_to_grid(self, obj, tile_width: int, tile_height: int, width: int, height: int) -> GridPos:
        gx = int(float(obj.attrib.get("x", 0)) // tile_width)
        gy = int(float(obj.attrib.get("y", 0)) // tile_height)

        gx = max(0, min(width - 1, gx))
        gy = max(0, min(height - 1, gy))

        return gx, gy

    def _paint_object_rect(self, grid: Grid, obj, tile_width: int, tile_height: int, width: int, height: int, code: int) -> None:
        x = float(obj.attrib.get("x", 0))
        y = float(obj.attrib.get("y", 0))
        w = float(obj.attrib.get("width", tile_width) or tile_width)
        h = float(obj.attrib.get("height", tile_height) or tile_height)

        x1 = max(0, int(x // tile_width))
        y1 = max(0, int(y // tile_height))
        x2 = min(width - 1, int((x + max(1, w) - 1) // tile_width))
        y2 = min(height - 1, int((y + max(1, h) - 1) // tile_height))

        for gy in range(y1, y2 + 1):
            for gx in range(x1, x2 + 1):
                grid[gy][gx] = code

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        text = text.lower().replace(" ", "_")
        return any(keyword.lower() in text for keyword in keywords)

    @staticmethod
    def _unique(items: list[GridPos]) -> list[GridPos]:
        result = []
        seen = set()

        for item in items:
            if item not in seen:
                result.append(item)
                seen.add(item)

        return result
