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


class GameFlowMixin:
    def _finish_game(self, winner_name: str) -> None:
        if self.result_logged:
            return

        self.winner_name = winner_name
        self.state = GameState.WIN if winner_name == "Player" else GameState.GAME_OVER
        self._log_result()
        self.result_logged = True

    def _log_result(self) -> None:
        player_money = self.player.money if self.player else 0
        player_orders = self.player.orders if self.player else 0

        record = GameStatsRecord(
            timestamp=StatsLogger.now_text(),
            map_id=self.settings.selected_map_id,
            map_source=self.map_source,
            winner=self.winner_name,
            player_win=(self.winner_name == "Player"),
            elapsed_time=round(self.elapsed_time, 2),
            target_revenue=self.settings.target_revenue,
            player_money=player_money,
            player_orders=player_orders,
            player_algorithm=self.settings.selected_algorithm,
            player_expanded_nodes=self.player_path_expanded,
        )

        for index, npc in enumerate(self.npc_shippers, start=1):
            setattr(record, f"npc_{index}_money", npc.money)
            setattr(record, f"npc_{index}_orders", npc.orders)
            setattr(record, f"npc_{index}_algorithm", getattr(npc, "algorithm", ""))
            setattr(record, f"npc_{index}_expanded_nodes", self.npc_expanded.get(npc.name, 0))

        self.stats_logger.write_record(record)

    def _reset_game(self) -> None:
        self.elapsed_time = 0.0
        self.result_logged = False
        self.winner_name = ""
        self.auto_player_enabled = False
        self.move_dir = (0, 0)
        self._player_last_trap_penalty_pos = None
        self.delivery_confirmation_open = False
        self.delivery_checkbox_checked = False
        self._delivery_prompt_dismissed_pos = None
        self.delivered_house_numbers = []
        self._next_player_order_id = 0
        self.order_scroll_offset = 0

        self._create_shipper_objects()

        self.player_task = None
        self.player_tasks = []
        self.available_player_tasks = []
        self.npc_tasks = {}
        self.npc_paths = {}
        self.npc_expanded = {}
        self.npc_wait_until = {}
        self.npc_wait_action = {}

        if self.player:
            self.player.money = 0
            self.player.orders = 0
            self.player.set_grid_pos(self._nearest_walkable(self.player_spawn))

        for npc in self.npc_shippers:
            npc.money = 0
            npc.orders = 0

        if self.simulation_mode:
            self.player_path_hint = []
            self.player_path_expanded = 0
        else:
            self._generate_player_order_offers()
