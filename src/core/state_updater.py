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


class StateUpdaterMixin:
    def _update(self, dt: float) -> None:
        if self.state == GameState.MENU:
            self.menu_cloud_offset = (getattr(self, "menu_cloud_offset", 0.0) + dt * 28) % (SCREEN_WIDTH + 360)
            return

        if self.state not in (GameState.PLAYING, GameState.SIMULATION):
            return

        self._update_smooth_entities(dt)
        self.elapsed_time += dt

        if self.state == GameState.PLAYING and not self.auto_player_enabled:
            self._poll_keyboard_movement()

        self.move_timer += dt

        if self.state == GameState.PLAYING and self.move_timer >= 0.065:
            self.move_timer = 0.0

            if self.auto_player_enabled:
                self._move_player_auto()
            else:
                self._move_player(allow_queue=True)

        self.npc_timer += dt

        if self.npc_timer >= 0.065:
            self.npc_timer = 0.0
            self._update_npcs()

        self.order_timer += dt

        if self.state == GameState.PLAYING and self.order_timer >= 0.8:
            self.order_timer = 0.0
            self._refresh_player_path_hint()

        if self.state == GameState.SIMULATION:
            return

        if self.player and self.player.money >= self.settings.target_revenue:
            self._finish_game("Player")
            return

        for npc in self.npc_shippers:
            if npc.money >= self.settings.target_revenue:
                self._finish_game(npc.name)
                return
