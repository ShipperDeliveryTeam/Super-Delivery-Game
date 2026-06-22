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
from src.systems.asset_paths import get_npc_sprite_paths, get_player_sprite_paths
from src.entities.directional_shipper import DirectionalShipper


class GameplayControllerMixin:
    def _create_shipper_objects(self) -> None:
        player_sprites = self.sprite_loader.load_directional_set(
            get_player_sprite_paths(),
            size=(TILE_SIZE, TILE_SIZE),
            fallback_color=PLAYER_COLOR,
            label="P",
        )

        self.player = DirectionalShipper("Player", self.player_spawn, player_sprites, TILE_SIZE)
        self.player.allow_diagonal = self._allow_diagonal_movement()
        self.player.configure_roundabout(
            self._roundabout_center(),
            self._roundabout_ring(),
            self._roundabout_connections(),
        )

        self.npc_shippers = []
        default_positions = [(8, 8), (14, 10), (20, 12)]
        algorithms = ["BFS", "ASTAR", "Q_LEARNING"]

        for i in range(3):
            npc_sprites = self.sprite_loader.load_directional_set(
                get_npc_sprite_paths(i + 1),
                size=(TILE_SIZE, TILE_SIZE),
                fallback_color=NPC_COLORS[i % len(NPC_COLORS)],
                label=str(i + 1),
            )

            raw_pos = self.npc_spawns[i] if i < len(self.npc_spawns) else default_positions[i]
            pos = self._nearest_walkable(raw_pos)

            npc = DirectionalShipper(f"NPC {i + 1}", pos, npc_sprites, TILE_SIZE)
            npc.algorithm = algorithms[i]
            npc.allow_diagonal = self._allow_diagonal_movement()
            npc.configure_roundabout(
                self._roundabout_center(),
                self._roundabout_ring(),
                self._roundabout_connections(),
            )
            self.npc_shippers.append(npc)
