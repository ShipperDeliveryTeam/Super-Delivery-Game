from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from collections import deque
import csv
import io
import xml.etree.ElementTree as ET

import pygame


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GridPos = tuple[int, int]


@dataclass
class TmxMapData:
    # New names
    grid_width: int
    grid_height: int
    tile_width: int
    tile_height: int
    pixel_width: int
    pixel_height: int

    surface: pygame.Surface | None = None

    # Compatible with old game_manager.py
    grid: list[list[int]] = field(default_factory=list)
    width: int = 48
    height: int = 32

    store_positions: list[GridPos] = field(default_factory=list)
    house_positions: list[GridPos] = field(default_factory=list)
    player_spawn: GridPos | None = None
    npc_spawns: list[GridPos] = field(default_factory=list)
    trap_positions: list[GridPos] = field(default_factory=list)

    raw_store_positions: list[GridPos] = field(default_factory=list)
    raw_house_positions: list[GridPos] = field(default_factory=list)

    store_rewards: dict[GridPos, int] = field(default_factory=dict)
    store_names: dict[GridPos, str] = field(default_factory=dict)


class TmxMapLoader:
    """
    TMX loader tương thích với game_manager.py hiện tại.

    Quy ước output grid:
    - 0 = Road / walkable
    - 1 = Blocked
    - 2 = Store target, walkable
    - 3 = House target, walkable
    - 4 = Trap, walkable nhưng phạt
    """

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
        self.default_cols = int(default_cols)
        self.default_rows = int(default_rows)
        self.default_tile_size = int(default_tile_size)

    def load(self, path: str | Path) -> TmxMapData:
        tmx_path = Path(path)

        if not tmx_path.is_absolute():
            tmx_path = PROJECT_ROOT / tmx_path

        if not tmx_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file TMX: {path}")

        tree = ET.parse(tmx_path)
        root = tree.getroot()

        grid_width = int(root.attrib.get("width", self.default_cols))
        grid_height = int(root.attrib.get("height", self.default_rows))
        tile_width = int(root.attrib.get("tilewidth", self.default_tile_size))
        tile_height = int(root.attrib.get("tileheight", self.default_tile_size))
        pixel_width = grid_width * tile_width
        pixel_height = grid_height * tile_height

        road_grid: list[list[int]] | None = None
        collision_grid: list[list[int]] | None = None

        for layer in root.findall("layer"):
            layer_name = layer.attrib.get("name", "").lower()
            values = self._parse_csv_layer(layer, grid_width, grid_height)

            if not values:
                continue

            if "road" in layer_name or "walkable" in layer_name or "ai" in layer_name:
                # Trong TMX của bạn: Road_AI = 1 là đường đi, 0 là không đi
                road_grid = [[1 if cell != 0 else 0 for cell in row] for row in values]

            elif "collision" in layer_name or "block" in layer_name:
                # Trong TMX của bạn: Collision = 2 là block, 0 là passable, 1 là trap/slow
                collision_grid = values

        if road_grid is None:
            if collision_grid:
                road_grid = [[1 if cell == 0 else 0 for cell in row] for row in collision_grid]
            else:
                road_grid = [[1 for _ in range(grid_width)] for _ in range(grid_height)]

        if collision_grid is None:
            collision_grid = [[0 for _ in range(grid_width)] for _ in range(grid_height)]

        # Build compatible grid for game_manager/pathfinder
        grid: list[list[int]] = []

        for y in range(grid_height):
            row = []

            for x in range(grid_width):
                is_road = road_grid[y][x] == 1
                is_block = collision_grid[y][x] == 2
                is_trap = collision_grid[y][x] == 1

                if is_road and not is_block:
                    row.append(self.TRAP if is_trap else self.ROAD)
                else:
                    row.append(self.BLOCK)

            grid.append(row)

        surface = self._load_background_surface(root, tmx_path, pixel_width, pixel_height)

        data = TmxMapData(
            grid_width=grid_width,
            grid_height=grid_height,
            width=grid_width,
            height=grid_height,
            tile_width=tile_width,
            tile_height=tile_height,
            pixel_width=pixel_width,
            pixel_height=pixel_height,
            surface=surface,
            grid=grid,
        )

        self._parse_objects(root, data)

        if data.player_spawn is None:
            data.player_spawn = self._nearest_walkable((0, 0), data.grid)

        if not data.npc_spawns:
            data.npc_spawns = [
                self._nearest_walkable((8, 8), data.grid),
                self._nearest_walkable((14, 10), data.grid),
                self._nearest_walkable((20, 12), data.grid),
            ]

        print(
            f"[TMX] Loaded {tmx_path.name}: "
            f"stores={len(data.store_positions)}, "
            f"houses={len(data.house_positions)}, "
            f"npc={len(data.npc_spawns)}, "
            f"player={data.player_spawn}"
        )

        return data

    def blocked_positions(self, grid: list[list[int]]) -> set[GridPos]:
        blocked: set[GridPos] = set()

        for y, row in enumerate(grid):
            for x, code in enumerate(row):
                if code not in self.WALKABLE:
                    blocked.add((x, y))

        return blocked

    def _parse_csv_layer(self, layer: ET.Element, width: int, height: int) -> list[list[int]]:
        data = layer.find("data")

        if data is None:
            return []

        text = (data.text or "").strip()

        if not text:
            return []

        reader = csv.reader(io.StringIO(text))
        nums: list[int] = []

        for row in reader:
            for item in row:
                item = item.strip()

                if item:
                    nums.append(int(item))

        expected = width * height

        if len(nums) < expected:
            nums += [0] * (expected - len(nums))
        elif len(nums) > expected:
            nums = nums[:expected]

        return [nums[y * width:(y + 1) * width] for y in range(height)]

    def _load_background_surface(
        self,
        root: ET.Element,
        tmx_path: Path,
        width: int,
        height: int,
    ) -> pygame.Surface | None:
        image_path = None

        for image_layer in root.findall("imagelayer"):
            image = image_layer.find("image")

            if image is None:
                continue

            source = image.attrib.get("source", "")

            if not source:
                continue

            candidate = (tmx_path.parent / source).resolve()

            if candidate.exists():
                image_path = candidate
                break

        if image_path is None:
            stem = tmx_path.stem
            map_id = "".join(ch for ch in stem if ch.isdigit())
            guesses = [
                PROJECT_ROOT / "assets" / "images" / "map" / f"{stem}.png",
                PROJECT_ROOT / "assets" / "images" / "map" / f"{stem.replace('_', '')}.png",
                PROJECT_ROOT / "assets" / "images" / "map" / f"map_{map_id}.png" if map_id else None,
                PROJECT_ROOT / "assets" / "images" / f"{stem}.png",
                PROJECT_ROOT / "assets" / "maps" / f"{stem}.png",
                PROJECT_ROOT / "assets" / "images" / "map" / "map1.png",
            ]

            for guessed in guesses:
                if guessed is not None and guessed.exists():
                    image_path = guessed
                    break

        if image_path is None:
            return None

        try:
            surface = pygame.image.load(str(image_path))

            if pygame.display.get_surface():
                surface = surface.convert_alpha()
            else:
                surface = surface.convert()

            if surface.get_width() != width or surface.get_height() != height:
                surface = pygame.transform.smoothscale(surface, (width, height))

            return surface

        except Exception as exc:
            print(f"[WARN] Không load được ảnh nền TMX: {image_path} | {exc}")
            return None

    def _parse_objects(self, root: ET.Element, data: TmxMapData) -> None:
        for group in root.findall("objectgroup"):
            for obj in group.findall("object"):
                name = obj.attrib.get("name", "").strip()
                obj_type = obj.attrib.get("type", "").strip()
                lower = f"{name} {obj_type}".lower()

                if not name and not obj_type:
                    continue

                try:
                    x = int(float(obj.attrib.get("x", "0")) // data.tile_width)
                    y = int(float(obj.attrib.get("y", "0")) // data.tile_height)
                except Exception:
                    continue

                if not self._inside((x, y), data.width, data.height):
                    continue

                raw_pos = self._clamp_grid((x, y), data.width, data.height)
                props = self._object_properties(obj)

                if "pickup" in lower or "store" in lower or "shop" in lower:
                    road_pos = self._nearest_walkable(raw_pos, data.grid)
                    data.raw_store_positions.append(raw_pos)
                    data.store_positions.append(road_pos)
                    data.store_rewards[road_pos] = int(props.get("base_reward", props.get("reward", 50)))
                    data.store_names[road_pos] = str(props.get("shop_name", name or "Store"))

                elif "delivery" in lower or "house" in lower or "customer" in lower:
                    road_pos = self._nearest_walkable(raw_pos, data.grid)
                    data.raw_house_positions.append(raw_pos)
                    data.house_positions.append(road_pos)

                elif "player" in lower:
                    data.player_spawn = self._nearest_walkable(raw_pos, data.grid)

                elif "npc" in lower:
                    data.npc_spawns.append(self._nearest_walkable(raw_pos, data.grid))

                elif "trap" in lower or "hole" in lower:
                    road_pos = self._nearest_walkable(raw_pos, data.grid)
                    data.trap_positions.append(road_pos)
                    x2, y2 = road_pos
                    data.grid[y2][x2] = self.TRAP

        # Xóa trùng nhưng giữ thứ tự
        data.store_positions = self._unique(data.store_positions)
        data.house_positions = self._unique(data.house_positions)
        data.npc_spawns = self._unique(data.npc_spawns)
        data.trap_positions = self._unique(data.trap_positions)

        # Mark store/house target as walkable special codes
        for x, y in data.store_positions:
            data.grid[y][x] = self.STORE

        for x, y in data.house_positions:
            data.grid[y][x] = self.HOUSE

        for x, y in data.trap_positions:
            data.grid[y][x] = self.TRAP

    def _object_properties(self, obj: ET.Element) -> dict[str, object]:
        props: dict[str, object] = {}
        properties = obj.find("properties")

        if properties is None:
            return props

        for prop in properties.findall("property"):
            name = prop.attrib.get("name")

            if not name:
                continue

            value: object = prop.attrib.get("value", "")

            if prop.attrib.get("type") == "int":
                try:
                    value = int(value)
                except Exception:
                    pass

            props[name] = value

        return props

    def _nearest_walkable(self, start: GridPos, grid: list[list[int]]) -> GridPos:
        height = len(grid)

        if height == 0:
            return start

        width = len(grid[0])
        start = self._clamp_grid(start, width, height)

        if grid[start[1]][start[0]] in self.WALKABLE:
            return start

        q = deque([start])
        visited = {start}

        while q:
            x, y = q.popleft()
            
            if abs(x - start[0]) + abs(y - start[1]) > 25:
                continue

            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if not (0 <= nx < width and 0 <= ny < height):
                    continue

                if (nx, ny) in visited:
                    continue

                if grid[ny][nx] in self.WALKABLE:
                    return (nx, ny)

                visited.add((nx, ny))
                q.append((nx, ny))

        return start

    def _clamp_grid(self, pos: GridPos, width: int, height: int) -> GridPos:
        x, y = pos
        return (max(0, min(width - 1, x)), max(0, min(height - 1, y)))

    def _inside(self, pos: GridPos, width: int, height: int) -> bool:
        x, y = pos
        return 0 <= x < width and 0 <= y < height

    def _unique(self, items: list[GridPos]) -> list[GridPos]:
        seen = set()
        output = []

        for item in items:
            if item not in seen:
                seen.add(item)
                output.append(item)

        return output
