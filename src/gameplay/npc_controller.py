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


class NpcControllerMixin:
    def _update_npcs(self) -> None:
        for npc in self.npc_shippers:
            if npc.name not in self.npc_tasks or self.npc_tasks[npc.name].delivered:
                self.npc_tasks[npc.name] = self._new_task(npc.name)
                self.npc_paths[npc.name] = []

            task = self.npc_tasks[npc.name]
            task.assign_to(npc.name)

            if not self.npc_paths.get(npc.name):
                result = self.pathfinder.find_path(self._movement_base_pos(npc), task.target_pos, npc.algorithm)
                self.npc_paths[npc.name] = result.path[1:] if result.success and len(result.path) > 1 else []
                self.npc_expanded[npc.name] = result.expanded_nodes

            path = self.npc_paths.get(npc.name, [])

            if path and getattr(npc, "queued_grid_pos", None) is None:
                base_pos = self._movement_base_pos(npc)

                while path and path[0] == base_pos:
                    path.pop(0)

                if path:
                    next_pos = path[0]
                    dx = next_pos[0] - base_pos[0]
                    dy = next_pos[1] - base_pos[1]

                    if self._try_move_shipper_delta(npc, dx, dy):
                        path.pop(0)
                    else:
                        self.npc_paths[npc.name] = []

            picked = task.try_pickup(npc.name, npc.grid_pos)
            delivered = task.try_deliver(npc.name, npc.grid_pos)

            if picked:
                self.npc_paths[npc.name] = []

            if delivered:
                npc.money += task.reward
                npc.orders += 1
                self.npc_tasks[npc.name] = self._new_task(npc.name)
                self.npc_paths[npc.name] = []

            if npc.grid_pos in self.trap_positions:
                npc.money = max(0, npc.money - 10)
