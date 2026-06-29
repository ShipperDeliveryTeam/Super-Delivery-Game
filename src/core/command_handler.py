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
from src.core.event_handler import CommandType, GameCommand
from src.ai.game_pathfinder import GamePathfinder
from src.gameplay.delivery_task import DeliveryTask
from src.gameplay.order_generator import OrderGenerator
from src.gameplay.roundabout_geometry import build_roundabout_curve, curve_point
from src.systems.stats_logger import StatsLogger, GameStatsRecord
from src.systems.asset_paths import get_ui_asset_path
from src.entities.directional_shipper import DirectionalShipper


class CommandHandlerMixin:
    def _handle_commands(self) -> None:
        for command in self.event_handler.handle_events():
            self._execute_command(command)

    def _execute_command(self, command: GameCommand) -> None:
        ctype = command.type

        if ctype == CommandType.QUIT:
            self.running = False

        elif ctype == CommandType.MOUSE_CLICK:
            self._handle_mouse_click(command.value)

        elif ctype == CommandType.START_GAME:
            if self.state in (GameState.MENU, GameState.GAME_OVER, GameState.WIN):
                self._start_play_mode()
            elif self.state == GameState.PAUSED:
                self.state = GameState.SIMULATION if self.simulation_mode else GameState.PLAYING

        elif ctype == CommandType.PAUSE_GAME:
            if self.state in (GameState.PLAYING, GameState.SIMULATION):
                self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                self.state = GameState.SIMULATION if self.simulation_mode else GameState.PLAYING
            elif self.state in (GameState.WIN, GameState.GAME_OVER):
                self.state = GameState.MENU

        elif ctype == CommandType.SELECT_MAP and command.value is not None:
            self.settings.set_map(int(command.value))
            self._load_map_for_selected_map()
            self._reset_game()

        elif ctype == CommandType.SELECT_ALGORITHM and command.value is not None:
            self.settings.set_algorithm(str(command.value))

            if not self.simulation_mode:
                self._refresh_player_path_hint()

        elif ctype == CommandType.TOGGLE_GRID:
            self.settings.toggle_grid()

        elif ctype == CommandType.TOGGLE_PATH_HINT:
            self.settings.toggle_path_hint()

        elif ctype == CommandType.TOGGLE_SOUND:
            self.settings.toggle_sound()

        elif ctype == CommandType.TOGGLE_AUTO_PLAYER:
            self.auto_player_enabled = not self.auto_player_enabled
            self._refresh_player_path_hint()

        elif ctype == CommandType.TOGGLE_HUD:
            self.hud_mode = (self.hud_mode + 1) % 3

        elif ctype == CommandType.MOVE_UP:
            self._request_player_step(0, -1)

        elif ctype == CommandType.MOVE_DOWN:
            self._request_player_step(0, 1)

        elif ctype == CommandType.MOVE_LEFT:
            self._request_player_step(-1, 0)

        elif ctype == CommandType.MOVE_RIGHT:
            self._request_player_step(1, 0)

        elif ctype == CommandType.STOP_MOVE:
            self.move_dir = (0, 0)

        elif ctype == CommandType.DEBUG_WIN:
            self._finish_game("Player")

        elif ctype == CommandType.DEBUG_LOSE:
            self._finish_game("NPC DEBUG")

        elif ctype == CommandType.SCROLL:
            if hasattr(self, '_handle_scroll_event'):
                self._handle_scroll_event(command)
