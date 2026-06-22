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


class ResultScreenMixin:
    def _draw_result(self, title: str, subtitle: str) -> None:
        self.screen.fill((22, 29, 39))
        self._draw_text(title, self.font_big, (255, 230, 120), SCREEN_WIDTH // 2, 180, center=True)
        self._draw_text(subtitle, self.font_mid, (255, 255, 255), SCREEN_WIDTH // 2, 245, center=True)

        money = self.player.money if self.player else 0
        orders = self.player.orders if self.player else 0

        box = pygame.Rect(SCREEN_WIDTH // 2 - 300, 300, 600, 220)
        self._draw_panel(box, alpha=170, border=True)

        lines = [
            f"Winner: {self.winner_name}",
            f"Time: {self.elapsed_time:.1f}s",
            f"Player money: ${money}/{self.settings.target_revenue}",
            f"Player orders: {orders}",
            "Result saved to stats.csv",
            "ENTER: Play again | ESC: Back to menu",
        ]

        y = 325

        for line in lines:
            self._draw_text(line, self.font_small, (245, 245, 245), SCREEN_WIDTH // 2, y, center=True)
            y += 32
