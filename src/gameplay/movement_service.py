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
from src.systems.stats_logger import StatsLogger, GameStatsRecord
from src.systems.asset_paths import get_ui_asset_path
from src.entities.directional_shipper import DirectionalShipper


class MovementServiceMixin:
    def _update_smooth_entities(self, dt: float) -> None:
        if self.player:
            self.player.update_smooth(dt)

            if self.state == GameState.PLAYING:
                self._handle_player_task_at_current_pos()

        for npc in self.npc_shippers:
            npc.update_smooth(dt)

    def _movement_base_pos(self, shipper) -> Tuple[int, int]:
        if getattr(shipper, "is_moving", False):
            return tuple(getattr(shipper, "target_grid_pos", shipper.grid_pos))

        return tuple(shipper.grid_pos)

    def _try_move_shipper_delta(self, shipper, dx: int, dy: int, allow_queue: bool = True) -> bool:
        dx = int(dx)
        dy = int(dy)

        allow_diagonal = self._allow_diagonal_movement()

        if allow_diagonal:
            if max(abs(dx), abs(dy)) != 1 or (dx == 0 and dy == 0):
                return False
        elif abs(dx) + abs(dy) != 1:
            return False

        if not allow_queue and getattr(shipper, "is_moving", False):
            return False

        base_x, base_y = self._movement_base_pos(shipper)
        next_pos = (
            max(0, min(self.map_cols - 1, base_x + dx)),
            max(0, min(self.map_rows - 1, base_y + dy)),
        )

        if next_pos == (base_x, base_y):
            return True

        if not self.pathfinder.can_step((base_x, base_y), next_pos):
            return False

        shipper.allow_diagonal = allow_diagonal
        return bool(shipper.move_grid(dx, dy, self.map_cols, self.map_rows, min_y=0, allow_diagonal=allow_diagonal))
