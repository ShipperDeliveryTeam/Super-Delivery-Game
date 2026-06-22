from __future__ import annotations

import random
from pathlib import Path
from typing import List, Optional, Tuple

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


class AssetManagerMixin:
    def _load_ui_image(self, filename: str, size: tuple[int, int] | None = None):
        try:
            path = get_ui_asset_path(filename)

            if not path:
                return None

            image = pygame.image.load(str(path)).convert_alpha()

            if size is not None:
                image = pygame.transform.smoothscale(image, size)

            return image

        except Exception as exc:
            print(f"[WARN] Không load được UI image {filename}: {exc}")
            return None

    def _load_assets(self) -> None:
        self.ui_background = self._load_ui_image("phongnen.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.ui_logo = self._load_ui_image("logo.png", (860, 300))
        right_path = get_player_sprite_paths().get("right")
        self.ui_shipper = None
        if right_path and right_path.exists():
            try:
                self.ui_shipper = pygame.image.load(str(right_path)).convert_alpha()
            except Exception:
                pass

        self.ui_play_button = self.sprite_loader.load_image(
            get_icon_path("play"),
            size=(310, 115),
            fallback_color=(55, 200, 70),
            fallback_text="PLAY",
        )
        self.ui_simulation_button = self._load_simulation_button_image()
        self.ui_sound_on = self.sprite_loader.load_image(
            get_icon_path("sound_on"),
            size=(58, 58),
            fallback_color=(65, 190, 95),
            fallback_text="ON",
        )
        self.ui_sound_off = self.sprite_loader.load_image(
            get_icon_path("sound_off"),
            size=(58, 58),
            fallback_color=(180, 70, 70),
            fallback_text="OFF",
        )
        self.ui_menu_button = self.sprite_loader.load_image(
            get_icon_path("menu"),
            size=(58, 58),
            fallback_color=(90, 130, 230),
            fallback_text="☰",
        )
        self.icons["store"] = self.sprite_loader.load_image(
            get_icon_path("store"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(240, 170, 60),
            fallback_text="S",
        )

        self.icons["house"] = self.sprite_loader.load_image(
            get_icon_path("house"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(80, 180, 100),
            fallback_text="H",
        )

        self.icons["money"] = self.sprite_loader.load_image(
            get_icon_path("money"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(240, 210, 70),
            fallback_text="$",
        )

        # Load location icons
        self.icons["location_player"] = self.sprite_loader.load_image(
            get_icon_path("location_shipper"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(55, 120, 220),
            fallback_text="LOC",
        )
        self.icons["location_npc1"] = self.sprite_loader.load_image(
            get_icon_path("location_npc1"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(220, 55, 55),
            fallback_text="LOC1",
        )
        self.icons["location_npc2"] = self.sprite_loader.load_image(
            get_icon_path("location_npc2"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(55, 220, 55),
            fallback_text="LOC2",
        )
        self.icons["location_npc3"] = self.sprite_loader.load_image(
            get_icon_path("location_npc3"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(220, 220, 55),
            fallback_text="LOC3",
        )

    def _load_simulation_button_image(self):
        path = get_icon_path("simulation")

        if not path:
            return self.sprite_loader.load_image(
                None,
                size=(310, 115),
                fallback_color=(55, 120, 220),
                fallback_text="SIM",
            )

        try:
            image = pygame.image.load(str(path)).convert_alpha()
            width, height = image.get_size()

            # Old exports were full-screen canvases. Current button art is already
            # a wide button, so only crop near-square/full-canvas images.
            if width >= 1000 and height >= 700 and width / max(1, height) < 2.2:
                crop = pygame.Rect(
                    int(width * 0.07),
                    int(height * 0.31),
                    int(width * 0.86),
                    int(height * 0.36),
                )
                image = image.subsurface(crop).copy()

            return image

        except Exception as exc:
            print(f"[WARN] Khong load duoc simulation button: {path} | {exc}")
            return self.sprite_loader.load_image(
                None,
                size=(310, 115),
                fallback_color=(55, 120, 220),
                fallback_text="SIM",
            )
