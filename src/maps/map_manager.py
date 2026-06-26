from __future__ import annotations

import random
from pathlib import Path
from typing import List, Optional, Tuple

# pyrefly: ignore [missing-import]
import pygame

from src.core.constants import (
    BACKGROUND_COLOR,
    GRID_LINE_COLOR,
    TEXT_COLOR,
    PLAYER_COLOR,
    NPC_COLORS,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TILE_SIZE,
    GRID_COLS,
    GRID_ROWS,
    GAME_TITLE,
)
from src.core.game_state import GameState
from src.ai.game_pathfinder import GamePathfinder
from src.gameplay.delivery_task import DeliveryTask
from src.gameplay.order_generator import OrderGenerator
from src.gameplay.roundabout_geometry import build_roundabout_curve, curve_point
from src.maps.matrix_loader import MatrixLoader
from src.maps.tmx_loader import TmxMapLoader
from src.systems.stats_logger import StatsLogger, GameStatsRecord
from src.systems.asset_paths import (
    get_map_image_path,
    get_player_sprite_paths,
    get_npc_sprite_paths,
    get_icon_path,
    get_ui_asset_path,
    MAPS_DIR,
)
from src.systems.sprite_loader import SpriteLoader
from src.entities.directional_shipper import DirectionalShipper


class MapManagerMixin:
    def _asset_maps_dir(self) -> Path:
        return Path(MAPS_DIR)

    def _tmx_path(self, map_id: int) -> Path:
        from src.systems.asset_paths import PROJECT_ROOT
        
        candidates = [
            PROJECT_ROOT / "maps" / f"map{map_id}" / f"map{map_id}.tmx",
            PROJECT_ROOT / "maps" / f"map_{map_id}.tmx",
            self._asset_maps_dir() / f"map_{map_id}.tmx",
            self._asset_maps_dir() / f"map{map_id}.tmx",
        ]
        
        for c in candidates:
            if c.exists():
                return c
                
        return self._asset_maps_dir() / f"map_{map_id}.tmx"

    def _matrix_path(self, map_id: int) -> Path:
        return self._asset_maps_dir() / f"map_{map_id}_matrix.csv"

    def _allow_diagonal_movement(self) -> bool:
        return self.settings.selected_map_id in (2, 3)

    def _roundabout_center(self) -> tuple[float, float] | None:
        return (23.5, 16.0) if self.settings.selected_map_id == 2 else None

    def _roundabout_ring(self) -> tuple[Tuple[int, int], ...]:
        if self.settings.selected_map_id != 2:
            return ()

        return (
            (22, 14),
            (23, 14),
            (24, 14),
            (25, 15),
            (25, 16),
            (25, 17),
            (24, 18),
            (23, 18),
            (22, 18),
            (21, 17),
            (21, 16),
            (21, 15),
        )

    def _roundabout_connections(self) -> tuple[tuple[Tuple[int, int], Tuple[int, int]], ...]:
        if self.settings.selected_map_id != 2:
            return ()

        return (
            ((23, 13), (23, 14)),  # Cổng phía trên
            ((23, 18), (23, 19)),  # Cổng phía dưới

            ((20, 16), (21, 16)),  # Nhánh chéo tây-bắc
            ((20, 18), (21, 17)),  # Nhánh chéo tây-nam

            ((25, 16), (26, 16)),  # Cổng đông-bắc; (26,16) thuộc đường chéo ngoài vòng
            ((25, 17), (26, 18)),  # Nhánh chéo đông-nam
        )

    def _load_map_for_selected_map(self) -> None:
        map_id = self.settings.selected_map_id
        tmx_path = self._tmx_path(map_id)

        if tmx_path.exists():
            try:
                data = self.tmx_loader.load(tmx_path)

                self.grid_matrix = data.grid
                self.map_cols = data.width
                self.map_rows = data.height
                self.map_image = data.surface

                if data.pixel_width != SCREEN_WIDTH or data.pixel_height != SCREEN_HEIGHT:
                    self.map_image = pygame.transform.smoothscale(data.surface, (SCREEN_WIDTH, SCREEN_HEIGHT))

                # Nếu TMX không render được image layer thì ép load PNG map.
                if not self._surface_has_visible_pixels(self.map_image):
                    print("[WARN] TMX surface trống, fallback sang ảnh PNG map.")
                    self._load_png_map_background()

                self.store_positions = data.store_positions
                self.store_names = dict(data.store_names)
                self.store_rewards = dict(data.store_rewards)
                self.store_ids = dict(data.store_ids)
                self.house_positions = data.house_positions
                self.trap_positions = set(data.trap_positions)
                self.player_spawn = data.player_spawn or (3, 3)
                self.npc_spawns = data.npc_spawns or []

                self.blocked_positions = self.tmx_loader.blocked_positions(self.grid_matrix)
                self.pathfinder = GamePathfinder(
                    self.map_cols,
                    self.map_rows,
                    self.blocked_positions,
                    allow_diagonal=self._allow_diagonal_movement(),
                    roundabout_ring=self._roundabout_ring(),
                    roundabout_connections=self._roundabout_connections(),
                )
                self.map_source = f"TMX: {tmx_path.name}"
                self._ensure_minimum_positions()
                return

            except Exception as exc:
                print(f"[WARN] Không load được TMX {tmx_path}: {exc}")
                print("[WARN] Fallback sang CSV matrix.")

        self._load_csv_matrix_fallback(map_id)

    def _load_csv_matrix_fallback(self, map_id: int) -> None:
        matrix_path = self._matrix_path(map_id)
        self.grid_matrix = self.matrix_loader.load_csv(matrix_path)

        if not matrix_path.exists():
            self.matrix_loader.save_csv(matrix_path, self.grid_matrix)

        self.map_cols = GRID_COLS
        self.map_rows = GRID_ROWS
        self.blocked_positions = self.matrix_loader.blocked_positions(self.grid_matrix)
        self.store_positions = self.matrix_loader.extract_positions(self.grid_matrix, MatrixLoader.STORE)
        self.store_names = {}
        self.store_rewards = {}
        self.house_positions = self.matrix_loader.extract_positions(self.grid_matrix, MatrixLoader.HOUSE)
        self.trap_positions = set(self.matrix_loader.extract_positions(self.grid_matrix, MatrixLoader.TRAP))
        self.player_spawn = (3, 3)
        self.npc_spawns = []

        safe = set(self.store_positions + self.house_positions) | self.trap_positions
        self.blocked_positions -= safe
        self.pathfinder = GamePathfinder(
            self.map_cols,
            self.map_rows,
            self.blocked_positions,
            allow_diagonal=self._allow_diagonal_movement(),
            roundabout_ring=self._roundabout_ring(),
            roundabout_connections=self._roundabout_connections(),
        )
        self.map_source = f"CSV: {matrix_path.name}"
        self._load_png_map_background()
        self._ensure_minimum_positions()

    def _surface_has_visible_pixels(self, surface: pygame.Surface | None) -> bool:
        """
        Kiểm tra TMX surface có pixel thật không.
        Nếu surface trống/transparent thì fallback sang ảnh PNG map.
        """
        if surface is None:
            return False

        try:
            rect = surface.get_bounding_rect()
            return rect.width > 0 and rect.height > 0
        except Exception:
            return False

    def _load_png_map_background(self) -> None:
        """
        Load ảnh nền thật của map từ PNG.
        Hàm này dùng để fallback khi TMX không render được image layer.
        """
        map_path = get_map_image_path(self.settings.selected_map_id)

        if map_path:
            print(f"[MAP] Load background image: {map_path}")
            self.map_image = self.sprite_loader.load_image(
                map_path,
                size=(SCREEN_WIDTH, SCREEN_HEIGHT),
                fallback_color=BACKGROUND_COLOR,
                fallback_text="MAP",
            )
        else:
            print(f"[WARN] Không tìm thấy ảnh nền map {self.settings.selected_map_id}.")
            print("[WARN] Hãy đặt ảnh vào một trong các đường dẫn:")
            print(f"       assets/images/map/map{self.settings.selected_map_id}.png")
            print(f"       assets/images/map/map_{self.settings.selected_map_id}.png")
            print(f"       assets/maps/map_{self.settings.selected_map_id}.png")

    def _ensure_minimum_positions(self) -> None:
        if not self.store_positions:
            self.store_positions = [
                self._nearest_walkable((6, 5)),
                self._nearest_walkable((18, 10)),
                self._nearest_walkable((31, 16)),
                self._nearest_walkable((40, 22)),
            ]

        if not self.house_positions:
            self.house_positions = [
                self._nearest_walkable((10, 22)),
                self._nearest_walkable((22, 27)),
                self._nearest_walkable((36, 27)),
                self._nearest_walkable((44, 10)),
            ]

        self.player_spawn = self._nearest_walkable(self.player_spawn)

    def _grid_to_screen(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        x, y = pos
        cell_w = SCREEN_WIDTH / max(1, self.map_cols)
        cell_h = SCREEN_HEIGHT / max(1, self.map_rows)
        return int(x * cell_w), int(y * cell_h)

    def _cell_size_screen(self) -> Tuple[int, int]:
        return int(SCREEN_WIDTH / max(1, self.map_cols)), int(SCREEN_HEIGHT / max(1, self.map_rows))

    def _nearest_walkable(self, start: Tuple[int, int]) -> Tuple[int, int]:
        if self.pathfinder.is_walkable(start):
            return start

        sx, sy = start

        for radius in range(1, max(self.map_cols, self.map_rows)):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    pos = (sx + dx, sy + dy)

                    if self.pathfinder.is_walkable(pos):
                        return pos

        return (0, 0)
