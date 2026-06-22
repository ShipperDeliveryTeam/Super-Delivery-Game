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


class PopupMixin:
    def _set_fullscreen_mode(self, enabled: bool) -> None:
        self.fullscreen_enabled = bool(enabled)

        if self.fullscreen_enabled:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.settings.get_window_size())

    def _draw_rules_popup(self) -> None:
        if not self.rules_popup_open:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        self.screen.blit(overlay, (0, 0))

        box = pygame.Rect(SCREEN_WIDTH // 2 - 420, SCREEN_HEIGHT // 2 - 275, 840, 550)
        self._draw_panel(box, alpha=225, border=True)

        self._draw_text("GAME RULES", self.font_big, (255, 230, 110), box.centerx, box.y + 48, center=True)

        rules = [
            "1. You are the main shipper in the city.",
            "2. Customers use Local Search to choose a store.",
            "3. Go to the Store to pick up the order, then deliver it to the House.",
            "4. Four NPC shippers compete against you using AI algorithms.",
            "5. NPCs use BFS, A*, Beam Search, and Q-Learning.",
            "6. Press SPACE to let Auto Player follow the selected algorithm.",
            "7. The first shipper to reach the target money wins.",
            "8. Results are saved to stats.csv for the report.",
        ]

        y = box.y + 115
        for line in rules:
            self._draw_text(line, self.font_small, (245, 245, 245), box.x + 55, y)
            y += 42

        self.close_popup_rect = pygame.Rect(box.centerx - 90, box.bottom - 75, 180, 48)
        self._draw_text_button(self.close_popup_rect, "Close", (70, 125, 220))

    def _draw_window_popup(self) -> None:
        if not self.window_popup_open:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        self.screen.blit(overlay, (0, 0))

        box = pygame.Rect(SCREEN_WIDTH // 2 - 360, SCREEN_HEIGHT // 2 - 210, 720, 420)
        self._draw_panel(box, alpha=225, border=True)

        self._draw_text("WINDOW SETTINGS", self.font_big, (255, 230, 110), box.centerx, box.y + 55, center=True)

        status = "Fullscreen" if self.fullscreen_enabled else "Windowed"
        self._draw_text(f"Current mode: {status}", self.font_mid, (245, 245, 245), box.centerx, box.y + 125, center=True)

        self.windowed_button_rect = pygame.Rect(box.centerx - 260, box.y + 190, 220, 60)
        self.fullscreen_button_rect = pygame.Rect(box.centerx + 40, box.y + 190, 220, 60)
        self.close_popup_rect = pygame.Rect(box.centerx - 90, box.bottom - 80, 180, 48)

        self._draw_text_button(self.windowed_button_rect, "Windowed", (75, 145, 95))
        self._draw_text_button(self.fullscreen_button_rect, "Fullscreen", (55, 120, 220))
        self._draw_text_button(self.close_popup_rect, "Close", (180, 90, 70))
