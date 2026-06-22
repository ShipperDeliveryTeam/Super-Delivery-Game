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
from src.systems.stats_logger import StatsLogger, GameStatsRecord
from src.systems.asset_paths import get_ui_asset_path
from src.entities.directional_shipper import DirectionalShipper


class MenuMixin:
    def _load_map_preview_image(self, map_id: int, size: tuple[int, int]):
        """
        Load ảnh preview map cho menu chọn map.
        Ưu tiên các file:
        - assets/images/map_1_preview.png
        - assets/images/map1_preview.png
        - assets/images/map/map1.png
        - assets/maps/map_1.png
        """
        candidates = [
            Path("assets") / "images" / f"map_{map_id}_preview.png",
            Path("assets") / "images" / f"map{map_id}_preview.png",
            Path("assets") / "images" / "map" / f"map{map_id}.png",
            Path("assets") / "images" / "map" / f"map_{map_id}.png",
            Path("assets") / "maps" / f"map_{map_id}.png",
            Path("assets") / "maps" / f"map{map_id}.png",
        ]

        for path in candidates:
            if path.exists():
                try:
                    image = pygame.image.load(str(path)).convert_alpha()
                    return pygame.transform.smoothscale(image, size)
                except Exception:
                    pass

        return None

    def _draw_blue_sky_overlay(self) -> None:
        """
        Làm nền menu sáng hơn theo tông trời xanh.
        Nếu có Phongnen.png thì phủ lớp xanh lên trên để bớt tối.
        """
        sky = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        for y in range(SCREEN_HEIGHT):
            ratio = y / max(1, SCREEN_HEIGHT)
            r = int(45 + ratio * 25)
            g = int(165 + ratio * 25)
            b = int(245 - ratio * 20)
            pygame.draw.line(sky, (r, g, b, 120), (0, y), (SCREEN_WIDTH, y))

        self.screen.blit(sky, (0, 0))

    def _draw_moving_clouds(self) -> None:
        """
        Mây chuyển động nhẹ trong menu.
        Không cần file ảnh riêng.
        """
        offset = getattr(self, "menu_cloud_offset", 0.0)

        cloud_specs = [
            (120, 190, 1.00, 0),
            (510, 145, 0.85, 95),
            (880, 205, 1.15, 185),
            (1280, 155, 0.95, 270),
            (1520, 235, 0.75, 340),
        ]

        for base_x, y, scale, extra in cloud_specs:
            x = int((base_x + extra - offset) % (SCREEN_WIDTH + 360)) - 180
            self._draw_cloud(x, y, scale)

    def _draw_cloud(self, x: int, y: int, scale: float = 1.0) -> None:
        color = (245, 252, 255, 205)
        shadow = (180, 220, 245, 95)

        parts = [
            (0, 22, 58, 32),
            (44, 4, 68, 48),
            (102, 18, 80, 38),
            (162, 30, 60, 26),
        ]

        for px, py, w, h in parts:
            rect = pygame.Rect(
                x + int(px * scale),
                y + int(py * scale) + 5,
                int(w * scale),
                int(h * scale),
            )
            pygame.draw.ellipse(self.screen, shadow, rect)

        for px, py, w, h in parts:
            rect = pygame.Rect(
                x + int(px * scale),
                y + int(py * scale),
                int(w * scale),
                int(h * scale),
            )
            pygame.draw.ellipse(self.screen, color, rect)

    def _draw_map_selector(self) -> None:
        """
        Vẽ khu chọn map giống màn hình mẫu:
        MAP < 01 >
        [preview map]
        DIFFICULTY: EASY / MEDIUM / HARD
        """
        panel = pygame.Rect(SCREEN_WIDTH - 610, 245, 500, 320)
        self._draw_panel(panel, alpha=95, border=False)

        title_y = panel.y + 18
        self._draw_text("MAP", self.font_mid, (255, 255, 255), panel.x + 145, title_y, center=True)

        self.map_prev_button_rect = pygame.Rect(panel.x + 210, panel.y + 4, 54, 54)
        self.map_next_button_rect = pygame.Rect(panel.x + 362, panel.y + 4, 54, 54)

        self._draw_text_button(self.map_prev_button_rect, "‹", (65, 180, 85))
        self._draw_text_button(self.map_next_button_rect, "›", (65, 180, 85))

        map_num_text = f"{self.settings.selected_map_id:02d}"
        self._draw_text(map_num_text, self.font_mid, (255, 255, 255), panel.x + 316, title_y, center=True)

        preview_w = 430
        preview_h = 180
        self.map_preview_rect = pygame.Rect(panel.x + 35, panel.y + 72, preview_w, preview_h)

        preview = self._load_map_preview_image(self.settings.selected_map_id, (preview_w, preview_h))

        if preview:
            self.screen.blit(preview, self.map_preview_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), self.map_preview_rect, width=4, border_radius=8)
        else:
            pygame.draw.rect(self.screen, (35, 45, 55), self.map_preview_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), self.map_preview_rect, width=4, border_radius=8)
            self._draw_text(
                f"MAP {self.settings.selected_map_id} PREVIEW",
                self.font_small,
                (255, 255, 255),
                self.map_preview_rect.centerx,
                self.map_preview_rect.centery,
                center=True,
            )

        difficulty = self._get_map_difficulty_text(self.settings.selected_map_id)
        self._draw_text("DIFFICULTY:", self.font_mid, (255, 255, 255), panel.x + 190, panel.y + 285, center=True)
        self._draw_text(difficulty, self.font_mid, (80, 255, 90), panel.x + 335, panel.y + 285, center=True)

    def _get_map_difficulty_text(self, map_id: int) -> str:
        if map_id == 1:
            return "EASY"
        if map_id == 2:
            return "MEDIUM"
        return "HARD"

    def _change_menu_map(self, delta: int) -> None:
        new_map = self.settings.selected_map_id + delta

        if new_map < 1:
            new_map = 3
        elif new_map > 3:
            new_map = 1

        self.settings.set_map(new_map)
        self._load_map_for_selected_map()
        self._reset_game()
        self.state = GameState.MENU

    def _draw_menu_top_buttons(self) -> None:
        # Hạ nút xuống rõ ràng để không bị thanh cửa sổ Windows che.
        self.sound_button_rect = pygame.Rect(SCREEN_WIDTH - 105, 82, 64, 64)
        self.menu_button_rect = pygame.Rect(SCREEN_WIDTH - 185, 82, 64, 64)

        sound_img = self.ui_sound_on if self.settings.sound_enabled else self.ui_sound_off
        sound_text = "ON" if self.settings.sound_enabled else "OFF"

        self._draw_small_round_button(
            self.menu_button_rect,
            self.ui_menu_button,
            "☰",
            (90, 130, 230),
        )

        self._draw_small_round_button(
            self.sound_button_rect,
            sound_img,
            sound_text,
            (65, 190, 95) if self.settings.sound_enabled else (180, 70, 70),
        )

    def _draw_menu_dropdown(self) -> None:
        if not self.menu_panel_open:
            return

        panel = pygame.Rect(SCREEN_WIDTH - 330, 98, 300, 245)
        self._draw_panel(panel, alpha=180, border=True)

        self._draw_text("MENU", self.font_mid, (255, 230, 110), panel.centerx, panel.y + 25, center=True)

        self.rules_button_rect = pygame.Rect(panel.x + 35, panel.y + 65, 230, 45)
        self.window_button_rect = pygame.Rect(panel.x + 35, panel.y + 122, 230, 45)
        self.exit_button_rect = pygame.Rect(panel.x + 35, panel.y + 179, 230, 45)

        self._draw_text_button(self.rules_button_rect, "1. Game Rules", (55, 120, 220))
        self._draw_text_button(self.window_button_rect, "2. Window Settings", (75, 145, 95))
        self._draw_text_button(self.exit_button_rect, "3. Exit Game", (180, 70, 70))

    def _handle_mouse_click(self, pos: tuple[int, int]) -> None:
        if self.state != GameState.MENU:
            return

        if self.rules_popup_open:
            if self.close_popup_rect and self.close_popup_rect.collidepoint(pos):
                self.rules_popup_open = False
            return

        if self.window_popup_open:
            if self.windowed_button_rect and self.windowed_button_rect.collidepoint(pos):
                self._set_fullscreen_mode(False)
            elif self.fullscreen_button_rect and self.fullscreen_button_rect.collidepoint(pos):
                self._set_fullscreen_mode(True)
            elif self.close_popup_rect and self.close_popup_rect.collidepoint(pos):
                self.window_popup_open = False
            return

        if self.sound_button_rect and self.sound_button_rect.collidepoint(pos):
            self.settings.toggle_sound()
            return

        if self.menu_button_rect and self.menu_button_rect.collidepoint(pos):
            self.menu_panel_open = not self.menu_panel_open
            return

        if hasattr(self, "map_prev_button_rect") and self.map_prev_button_rect and self.map_prev_button_rect.collidepoint(pos):
            self._change_menu_map(-1)
            return

        if hasattr(self, "map_next_button_rect") and self.map_next_button_rect and self.map_next_button_rect.collidepoint(pos):
            self._change_menu_map(1)
            return

        if self.menu_panel_open:
            if self.rules_button_rect and self.rules_button_rect.collidepoint(pos):
                self.rules_popup_open = True
                self.menu_panel_open = False
                return

            if self.window_button_rect and self.window_button_rect.collidepoint(pos):
                self.window_popup_open = True
                self.menu_panel_open = False
                return

            if self.exit_button_rect and self.exit_button_rect.collidepoint(pos):
                self.running = False
                return

        if self.simulation_button_rect and self.simulation_button_rect.collidepoint(pos):
            self._start_simulation_mode()
            return

        if self.play_button_rect and self.play_button_rect.collidepoint(pos):
            self._start_play_mode()
            return
