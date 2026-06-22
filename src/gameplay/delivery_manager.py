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


class DeliveryManagerMixin:
    def _new_task(self, holder_name: Optional[str] = None) -> DeliveryTask:
        fallback_task = None

        for _ in range(40):
            task = self.order_generator.create_order(
                stores=self.store_positions,
                houses=self.house_positions,
                pathfinder=self.pathfinder,
                holder_name=holder_name,
            )

            if fallback_task is None:
                fallback_task = task

            if self._task_is_reachable(task, holder_name):
                return task

        reachable_task = self._first_reachable_task(holder_name)
        return reachable_task or fallback_task

    def _holder_grid_pos(self, holder_name: Optional[str]) -> Tuple[int, int] | None:
        if holder_name == "Player" and self.player:
            return self._movement_base_pos(self.player)

        for npc in self.npc_shippers:
            if npc.name == holder_name:
                return self._movement_base_pos(npc)

        return None

    def _task_is_reachable(self, task: DeliveryTask, holder_name: Optional[str]) -> bool:
        start = self._holder_grid_pos(holder_name)

        if start is not None:
            to_store = self.pathfinder.find_path(start, task.store_pos, "ASTAR")

            if not to_store.success:
                return False

        to_house = self.pathfinder.find_path(task.store_pos, task.house_pos, "ASTAR")
        return bool(to_house.success)

    def _first_reachable_task(self, holder_name: Optional[str]) -> DeliveryTask | None:
        start = self._holder_grid_pos(holder_name)

        for store in self.store_positions:
            if start is not None and not self.pathfinder.find_path(start, store, "ASTAR").success:
                continue

            for house in self.house_positions:
                result = self.pathfinder.find_path(store, house, "ASTAR")

                if result.success:
                    self.order_generator.last_result = None
                    return DeliveryTask(
                        store_pos=store,
                        house_pos=house,
                        reward=90,
                        holder_name=holder_name,
                    )

        return None
