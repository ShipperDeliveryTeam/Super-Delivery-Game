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


class HudMixin:
    def _draw_simulation_hud(self) -> None:
        top_bar = pygame.Rect(0, 0, SCREEN_WIDTH, 34)
        self._draw_panel(top_bar, alpha=115, border=False)
        text = f"SIMULATION | Map {self.settings.selected_map_id} | Time {self.elapsed_time:05.1f}s | ESC Pause | P Path | G Grid"
        self._draw_text(text, self.font_tiny, (255, 255, 255), 10, 9)

        board_w = 385
        row_h = 27
        board_h = 42 + len(self.npc_shippers) * row_h
        board = pygame.Rect(SCREEN_WIDTH - board_w - 12, 48, board_w, board_h)
        self._draw_panel(board, alpha=135, border=True)
        self._draw_text("ALGORITHM GROUPS", self.font_small, (255, 230, 110), board.x + 12, board.y + 10)

        colors = [(255, 80, 80), (60, 235, 125), (255, 180, 55), (165, 125, 255)]
        y = board.y + 38
        for i, npc in enumerate(self.npc_shippers):
            color = colors[i % len(colors)]
            pygame.draw.circle(self.screen, color, (board.x + 18, y + 8), 6)
            task = self.npc_tasks.get(npc.name)
            target = task.target_pos if task else "-"
            label = f"{npc.name}: {getattr(npc, 'algorithm', '')} -> {target}"
            self._draw_text(label, self.font_tiny, (245, 245, 245), board.x + 34, y)
            y += row_h

    def _draw_hud_clean(self) -> None:
        """
        HUD mới:
        - Mặc định gọn, không che nhiều map.
        - H để đổi chế độ:
          hud_mode = 1: gọn
          hud_mode = 2: đầy đủ
          hud_mode = 0: ẩn
        """
        hud_mode = getattr(self, "hud_mode", 1)

        if hud_mode == 0:
            return

        money = self.player.money if self.player else 0
        orders = self.player.orders if self.player else 0
        mode = "AUTO" if self.auto_player_enabled else "MANUAL"

        task_short = "No task"
        task_detail = []

        if self.player_task:
            status = "STORE" if not self.player_task.picked_up else "HOUSE"
            target = self.player_task.target_pos
            local_cost = getattr(self.order_generator.last_result, "cost", 0)

            task_short = (
                f"Task: {status} {target} | "
                f"${self.player_task.reward} | "
                f"LS {local_cost} | "
                f"Nodes {self.player_path_expanded}"
            )

            task_detail = [
                f"Status: {'GO TO STORE' if not self.player_task.picked_up else 'DELIVER TO HOUSE'}",
                f"Target grid: {target}",
                f"Store -> House: {self.player_task.store_pos} -> {self.player_task.house_pos}",
                f"Local Search cost: {local_cost}",
                f"Reward: ${self.player_task.reward}",
                f"Expanded nodes: {self.player_path_expanded}",
            ]

        # =========================
        # MODE 1: HUD gọn mặc định
        # =========================
        if hud_mode == 1:
            top_bar = pygame.Rect(0, 0, SCREEN_WIDTH, 32)
            self._draw_panel(top_bar, alpha=105, border=False)

            top_text = (
                f"Time {self.elapsed_time:05.1f}s | "
                f"Money ${money}/{self.settings.target_revenue} | "
                f"Orders {orders} | "
                f"AI {self.settings.selected_algorithm} | "
                f"{mode} | "
                f"{task_short}"
            )

            self._draw_text(top_text, self.font_tiny, (255, 255, 255), 10, 8)

            bottom_bar = pygame.Rect(0, SCREEN_HEIGHT - 24, SCREEN_WIDTH, 24)
            self._draw_panel(bottom_bar, alpha=85, border=False)

            help_text = "H HUD | WASD Move | SPACE Auto | F1 BFS | F2 A* | F3 Beam | F4 Partial | F5 Q-Learning | P Path | G Grid | ESC Pause"
            self._draw_text(help_text, self.font_tiny, (255, 255, 255), 10, SCREEN_HEIGHT - 20)

            return

        # =========================
        # MODE 2: HUD đầy đủ nhưng đẩy xuống dưới
        # =========================
        top_bar = pygame.Rect(0, 0, SCREEN_WIDTH, 34)
        self._draw_panel(top_bar, alpha=120, border=False)

        top_text = (
            f"Time {self.elapsed_time:05.1f}s | "
            f"Money ${money}/{self.settings.target_revenue} | "
            f"Orders {orders} | "
            f"AI {self.settings.selected_algorithm} | "
            f"Mode {mode} | "
            f"Map {self.settings.selected_map_id}"
        )
        self._draw_text(top_text, self.font_tiny, (255, 255, 255), 10, 9)

        # Mission panel xuống góc dưới trái để không che đường trên
        mission_box = pygame.Rect(12, SCREEN_HEIGHT - 190, 430, 148)
        self._draw_panel(mission_box, alpha=125, border=True)
        self._draw_text("PLAYER MISSION", self.font_small, (255, 230, 110), 24, mission_box.y + 10)

        y = mission_box.y + 38
        for line in task_detail if task_detail else ["No active task"]:
            self._draw_text(line, self.font_tiny, (245, 245, 245), 24, y)
            y += 19

        # NPC panel xuống góc dưới phải
        board_w = 405
        board_h = 148
        board = pygame.Rect(SCREEN_WIDTH - board_w - 12, SCREEN_HEIGHT - 190, board_w, board_h)
        self._draw_panel(board, alpha=125, border=True)
        self._draw_text("NPC SCOREBOARD", self.font_small, (255, 230, 110), board.x + 12, board.y + 10)

        y = board.y + 38
        for npc in self.npc_shippers:
            task = self.npc_tasks.get(npc.name)
            action = ""

            if task:
                action = "Pickup" if not task.picked_up else "Deliver"

            line = f"{npc.name}: ${npc.money:03d} | {npc.algorithm:<10} | {action:<7} | Nodes {self.npc_expanded.get(npc.name, 0)}"
            self._draw_text(line, self.font_tiny, (245, 245, 245), board.x + 12, y)
            y += 24

        help_bar = pygame.Rect(0, SCREEN_HEIGHT - 28, SCREEN_WIDTH, 28)
        self._draw_panel(help_bar, alpha=95, border=False)
        help_text = "H HUD | WASD move | SPACE auto-player | F1-F5 algorithms | P path | G grid | ESC pause"
        self._draw_text(help_text, self.font_tiny, (255, 255, 255), 10, SCREEN_HEIGHT - 22)

    def _draw_panel(self, rect: pygame.Rect, alpha: int = 150, border: bool = True) -> None:
        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        panel.fill((10, 14, 22, alpha))
        self.screen.blit(panel, (rect.x, rect.y))

        if border:
            pygame.draw.rect(self.screen, (255, 255, 255), rect, width=1, border_radius=6)
