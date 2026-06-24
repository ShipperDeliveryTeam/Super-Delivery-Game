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


class DeliveryManagerMixin:
    PLAYER_OFFER_COUNT = 5
    PLAYER_CARGO_LIMIT = 3

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

    def _create_player_order_offer(self) -> DeliveryTask:
        task = self._new_task(None)
        self._next_player_order_id = getattr(self, "_next_player_order_id", 0) + 1
        task.order_id = f"A{self._next_player_order_id:02d}"
        task.created_at = float(getattr(self, "elapsed_time", 0.0))
        task.expires_in = 150.0 + (self._next_player_order_id % 3) * 30.0
        return task

    def _generate_player_order_offers(self, count: int | None = None) -> None:
        target_count = int(count or self.PLAYER_OFFER_COUNT)
        offers: list[DeliveryTask] = []
        used_routes: set[tuple[Tuple[int, int], Tuple[int, int]]] = set()

        for _ in range(target_count * 20):
            task = self._create_player_order_offer()
            route = (task.store_pos, task.house_pos)

            if route in used_routes:
                continue

            used_routes.add(route)
            offers.append(task)

            if len(offers) >= target_count:
                break

        self.available_player_tasks = offers
        self.selected_player_order_index = -1
        self.player_task = None

    def _replenish_player_order_offers(self) -> None:
        offers = list(getattr(self, "available_player_tasks", []))
        used_routes = {(task.store_pos, task.house_pos) for task in offers}

        for _ in range(self.PLAYER_OFFER_COUNT * 20):
            if len(offers) >= self.PLAYER_OFFER_COUNT:
                break

            task = self._create_player_order_offer()
            route = (task.store_pos, task.house_pos)

            if route in used_routes:
                continue

            used_routes.add(route)
            offers.append(task)

        self.available_player_tasks = offers

    def _select_player_order(self, index: int) -> bool:
        offers = getattr(self, "available_player_tasks", [])

        if not 0 <= int(index) < len(offers):
            return False

        task = offers[index]

        if getattr(task, "stolen_by", None):
            return False

        player_tasks = list(getattr(self, "player_tasks", []))

        self.selected_player_order_index = int(index)

        if task not in player_tasks:
            if len(player_tasks) >= self.PLAYER_CARGO_LIMIT:
                return False

            player_tasks.append(task)

        task.holder_name = "Player"
        self.player_tasks = player_tasks
        if getattr(task, "picked_up", False):
            self.player_task = task
        elif self.player_task is task:
            self.player_task = None
        self.delivery_confirmation_open = False
        self.delivery_checkbox_checked = False
        self._refresh_player_path_hint()
        return True

    def _drop_player_task(self, task: DeliveryTask) -> None:
        self.player_tasks = [
            item for item in getattr(self, "player_tasks", [])
            if item is not task
        ]

        if self.player_task is task:
            picked_tasks = [
                item for item in self.player_tasks
                if getattr(item, "picked_up", False) and not getattr(item, "delivered", False)
            ]
            self.player_task = picked_tasks[0] if picked_tasks else None
            self.selected_player_order_index = (
                self.available_player_tasks.index(self.player_task)
                if self.player_task in getattr(self, "available_player_tasks", [])
                else -1
            )

    def _house_number(self, pos: Tuple[int, int]) -> int:
        try:
            return self.house_positions.index(pos) + 1
        except ValueError:
            return 0

    def _store_display_name(self, pos: Tuple[int, int]) -> str:
        name = str(getattr(self, "store_names", {}).get(pos, "Cua hang"))
        return name.replace("_", " ").strip().upper()

    def _confirm_player_delivery(self) -> bool:
        task = getattr(self, "player_task", None)

        if (
            not task
            or not self.player
            or not getattr(self, "delivery_checkbox_checked", False)
            or self.player.grid_pos != task.house_pos
        ):
            return False

        if not task.try_deliver("Player", self.player.grid_pos):
            return False

        self.player.money += task.reward
        self.player.orders += 1
        house_number = self._house_number(task.house_pos)
        delivered = getattr(self, "delivered_house_numbers", [])

        if house_number and house_number not in delivered:
            delivered.append(house_number)

        self.delivered_house_numbers = delivered[-6:]
        self.available_player_tasks = [
            offer for offer in getattr(self, "available_player_tasks", [])
            if offer is not task
        ]
        self._drop_player_task(task)
        self.delivery_confirmation_open = False
        self.delivery_checkbox_checked = False
        self._delivery_prompt_dismissed_pos = None
        self._replenish_player_order_offers()

        return True
