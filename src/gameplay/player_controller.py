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


class PlayerControllerMixin:
    def _request_player_step(self, dx: int, dy: int) -> None:
        if self.state != GameState.PLAYING or self.auto_player_enabled:
            return

        if self._allow_diagonal_movement():
            self._poll_keyboard_movement()
            return

        self.move_dir = (int(dx), int(dy))
        self._move_player(allow_queue=True)

    def _poll_keyboard_movement(self) -> None:
        keys = pygame.key.get_pressed()

        dx, dy = 0, 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1

        if not self._allow_diagonal_movement() and dx != 0:
            dy = 0

        self.move_dir = (dx, dy)

        if self.player and (dx != 0 or dy != 0):
            self.player.set_direction_from_delta(dx, dy)

    def _move_player_auto(self) -> None:
        if not self.player:
            return

        if self.player_task is None or self.player_task.delivered:
            self.player_task = self._new_task("Player")

        base_pos = self._movement_base_pos(self.player)

        if (
            not self.player_path_hint
            or self.player_path_hint[-1] != self.player_task.target_pos
            or base_pos not in self.player_path_hint[:2]
        ):
            self._refresh_player_path_hint()

        while self.player_path_hint and self.player_path_hint[0] == base_pos:
            self.player_path_hint.pop(0)

        if not self.player_path_hint:
            self._refresh_player_path_hint()

        if not self.player_path_hint:
            return

        next_pos = self.player_path_hint[0]
        dx = next_pos[0] - base_pos[0]
        dy = next_pos[1] - base_pos[1]

        if not self.pathfinder.can_step(base_pos, next_pos):
            self._refresh_player_path_hint()
            return

        old_dir = self.move_dir
        self.move_dir = (dx, dy)
        self._move_player()
        self.move_dir = old_dir

        if self.player_path_hint and self.player_path_hint[0] == next_pos:
            self.player_path_hint.pop(0)

    def _handle_player_task_at_current_pos(self) -> None:
        if not self.player:
            return

        if self.player_task is None or self.player_task.delivered:
            self.player_task = self._new_task("Player")

        self.player_task.assign_to("Player")

        picked = self.player_task.try_pickup("Player", self.player.grid_pos)
        delivered = self.player_task.try_deliver("Player", self.player.grid_pos)

        if picked:
            self._refresh_player_path_hint()

        if delivered:
            self.player.money += self.player_task.reward
            self.player.orders += 1
            self.player_task = self._new_task("Player")
            self._refresh_player_path_hint()

        if self.player.grid_pos in self.trap_positions:
            if self._player_last_trap_penalty_pos == self.player.grid_pos:
                return

            self.player.money = max(0, self.player.money - 15)
            self._player_last_trap_penalty_pos = self.player.grid_pos
        else:
            self._player_last_trap_penalty_pos = None

    def _move_player(self, allow_queue: bool = True) -> None:
        if not self.player:
            return

        dx, dy = self.move_dir

        if dx == 0 and dy == 0:
            return

        if not self._try_move_shipper_delta(self.player, dx, dy, allow_queue=allow_queue):
            return

        self._handle_player_task_at_current_pos()

    def _refresh_player_path_hint(self) -> None:
        if not self.player:
            return

        if self.player_task is None or self.player_task.delivered:
            self.player_task = self._new_task("Player")

        result = self.pathfinder.find_path(
            self._movement_base_pos(self.player),
            self.player_task.target_pos,
            self.settings.selected_algorithm,
        )

        self.player_path_hint = result.path
        self.player_path_expanded = result.expanded_nodes
