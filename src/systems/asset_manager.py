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
    IMAGES_DIR,
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
        self.ui_logo = self._load_ui_image("logo.png")
        self.ui_information_card = self._load_ui_image("information_card.png")
        self.ui_delivery_active_card = self._load_ui_image("delivery_active_card.png")
        self.ui_delivery_confirm_popup = self._load_ui_image("delivery_confirm_popup.png")
        self.ui_order_card = self._load_ui_image("order_card.png")
        self.ui_shop_order_card = self._load_ui_image("shop_order_card.png")
        self.shop_card_images = self._load_shop_card_images()
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

        self.icons["box"] = self.sprite_loader.load_image(
            get_icon_path("box"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(200, 150, 80),
            fallback_text="B",
        )

        self.icons["clock"] = self.sprite_loader.load_image(
            get_icon_path("clock"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(100, 200, 255),
            fallback_text="T",
        )

        self.icons["star"] = self.sprite_loader.load_image(
            get_icon_path("star"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(255, 215, 0),
            fallback_text="*",
        )
        self.icons["trap"] = self.sprite_loader.load_image(
            get_icon_path("trap"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(220, 60, 60),
            fallback_text="!",
        )

        self.icons["receive"] = self.sprite_loader.load_image(
            get_icon_path("receive"),
            size=(96, 40),
            fallback_color=(47, 163, 67),
            fallback_text="NHAN",
        )
        self.icons["received"] = self.sprite_loader.load_image(
            get_icon_path("received"),
            size=(96, 40),
            fallback_color=(94, 103, 108),
            fallback_text="DA NHAN",
        )
        self.icons["rob"] = self.sprite_loader.load_image(
            get_icon_path("rob"),
            size=(96, 40),
            fallback_color=(170, 55, 45),
            fallback_text="ROB",
        )

        # Load location icons
        self.icons["location_player"] = self.sprite_loader.load_image(
            get_icon_path("location_shipper"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(55, 120, 220),
            fallback_text="LOC",
        )
        self.icons["location_shop"] = self.sprite_loader.load_image(
            get_icon_path("location_shop"),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=(255, 177, 47),
            fallback_text="SHOP",
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

    def _load_shop_card_images(self) -> dict[int, dict[str, pygame.Surface]]:
        output: dict[int, dict[str, pygame.Surface]] = {}

        try:
            folders = [
                (1, IMAGES_DIR / "shop_map1"),
                (2, IMAGES_DIR / "shop_map2"),
                (3, IMAGES_DIR / "shop_map3"),
            ]

            for map_id, folder in folders:
                if not folder.exists():
                    continue

                map_images: dict[str, pygame.Surface] = {}
                for path in folder.glob("*.png"):
                    key = path.stem.replace("_store", "").replace("_shop", "").replace("_", "").lower()
                    map_images[key] = pygame.image.load(str(path)).convert_alpha()

                output[map_id] = map_images

        except Exception as exc:
            print(f"[WARN] Khong load duoc shop card images: {exc}")

        return output
