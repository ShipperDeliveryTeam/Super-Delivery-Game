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
from src.ui.left_information_card import LeftInformationCardMixin
from src.ui.left_active_delivery_card import LeftActiveDeliveryCardMixin
from src.ui.left_order_card import LeftOrderCardMixin


class HudMixin(LeftInformationCardMixin, LeftActiveDeliveryCardMixin, LeftOrderCardMixin):
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

        self._draw_delivery_dashboard()
        return

    def _draw_delivery_dashboard(self) -> None:
        self._game_sound_rect = pygame.Rect(SCREEN_WIDTH - 150, 14, 58, 58)
        self._game_pause_rect = pygame.Rect(SCREEN_WIDTH - 80, 14, 58, 58)
        self._draw_round_game_button(self._game_sound_rect, "♪" if getattr(self.settings, 'sound_enabled', True) else "×")
        self._draw_round_game_button(self._game_pause_rect, "PAUSE")

        if self._has_letterbox_side_rails():
            self._order_card_rects = []
            if getattr(self, "delivery_confirmation_open", False):
                self._draw_delivery_confirmation()
            return

        panel = pygame.Rect(14, 14, 340, SCREEN_HEIGHT - 28)
        self._draw_left_side_panel(panel)

        if getattr(self, "delivery_confirmation_open", False):
            self._draw_delivery_confirmation()

        if getattr(self, "delivered_house_numbers", []):
            self._draw_delivered_houses_panel()

    def _draw_left_side_panel(self, panel: pygame.Rect) -> None:
        self._draw_game_panel(panel, (6, 18, 34), (229, 168, 58), 248)
        inner = panel.inflate(-12, -12)
        pygame.draw.rect(self.screen, (4, 13, 26), inner, border_radius=10)
        pygame.draw.rect(self.screen, (42, 92, 125), inner, width=1, border_radius=10)
        pygame.draw.line(self.screen, (255, 209, 88), (panel.right - 5, panel.y + 18), (panel.right - 5, panel.bottom - 18), 2)

        # 1. Logo
        logo_rect = pygame.Rect(panel.x + 18, panel.y + 12, panel.width - 36, 78)
        if not self._draw_cropped_ui_asset(getattr(self, "ui_logo", None), logo_rect, pygame.Rect(185, 260, 1180, 430)):
            self._draw_game_panel(logo_rect, (20, 67, 104), (255, 200, 76), 255)
            self._draw_text("SUPER DELIVERY", self.font_mid, (255, 222, 88), logo_rect.centerx, logo_rect.y + 25, center=True)

        # 2. Stats Grid (2x2)
        grid_rect = pygame.Rect(panel.x + 12, logo_rect.bottom + 6, panel.width - 24, 112)
        self._draw_stats_grid(grid_rect)

        # 3. ĐANG GIAO card
        status_rect = pygame.Rect(panel.x + 12, grid_rect.bottom + 6, panel.width - 24, 96)
        self._draw_compact_status_card(status_rect)

        # 4. Don hang header, list, scroll, and cargo slots
        orders_panel = pygame.Rect(panel.x + 2, status_rect.bottom + 2, panel.width - 4, panel.bottom - status_rect.bottom - 6)
        self._draw_left_orders_card(orders_panel)

    def _draw_trimmed_ui_asset(self, image, rect: pygame.Rect) -> bool:
        if image is None or rect.width <= 0 or rect.height <= 0:
            return False

        crop = image.get_bounding_rect(8)
        if crop.width <= 0 or crop.height <= 0:
            crop = image.get_rect()

        return self._draw_cropped_ui_asset(image, rect, crop)

    def _draw_cropped_ui_asset(self, image, rect: pygame.Rect, crop: pygame.Rect | None = None) -> bool:
        if image is None or rect.width <= 0 or rect.height <= 0:
            return False

        source_rect = crop or image.get_rect()
        source_rect = source_rect.clip(image.get_rect())
        if source_rect.width <= 0 or source_rect.height <= 0:
            return False

        cache = getattr(self, "_ui_asset_cache", None)
        if cache is None:
            cache = {}
            self._ui_asset_cache = cache

        key = (id(image), source_rect.x, source_rect.y, source_rect.width, source_rect.height, rect.width, rect.height)
        scaled = cache.get(key)
        if scaled is None:
            source = image.subsurface(source_rect).copy()
            scaled = pygame.transform.smoothscale(source, (rect.width, rect.height))
            cache[key] = scaled

        self.screen.blit(scaled, rect)
        return True

    def _has_letterbox_side_rails(self) -> bool:
        display = pygame.display.get_surface()
        if display is None:
            return False

        win_w, win_h = display.get_size()
        scale = min(win_w / SCREEN_WIDTH, win_h / SCREEN_HEIGHT)
        rail_w = win_w - int(SCREEN_WIDTH * scale)
        return bool(
            rail_w >= 220
            and self.state == GameState.PLAYING
            and not getattr(self, "simulation_mode", False)
        )

    def _use_left_gameplay_rail(self) -> bool:
        return self._has_letterbox_side_rails()

    def _draw_letterbox_gameplay_ui(self, display: pygame.Surface, map_rect: pygame.Rect) -> None:
        if not self._has_letterbox_side_rails():
            self._letterbox_order_card_rects = []
            return

        original_screen = self.screen
        self.screen = display
        self._letterbox_order_card_rects = []

        left = pygame.Rect(0, map_rect.y, map_rect.x, map_rect.height)
        self._draw_left_play_panel(left)
        self.screen = original_screen

    def _draw_left_play_panel(self, rail: pygame.Rect) -> None:
        if rail.width <= 0:
            return

        # Use the exact same layout as the main delivery dashboard
        self._draw_left_side_panel(rail)

    def _draw_side_rail_backdrop(self, rail: pygame.Rect, title: str) -> None:
        if rail.width <= 0:
            return

        pygame.draw.rect(self.screen, (3, 17, 30), rail)
        glow = pygame.Surface(rail.size, pygame.SRCALPHA)
        for y in range(0, rail.height, 12):
            alpha = max(0, 24 - y // 18)
            pygame.draw.line(glow, (51, 134, 172, alpha), (0, y), (rail.width, y + 52), 1)
        self.screen.blit(glow, rail.topleft)

        edge_color = (236, 178, 58)
        if rail.x == 0:
            pygame.draw.line(self.screen, edge_color, (rail.right - 1, rail.y), (rail.right - 1, rail.bottom), 2)
        else:
            pygame.draw.line(self.screen, edge_color, (rail.x, rail.y), (rail.x, rail.bottom), 2)

        header = pygame.Rect(rail.x + 8, rail.y + 10, max(1, rail.width - 16), 38)
        self._draw_game_panel(header, (13, 60, 95), (236, 178, 58), 248)
        self._draw_text(title, self.font_tiny, (255, 224, 91), header.centerx, header.y + 10, center=True)

    def _draw_dashboard_chip(self, rect: pygame.Rect, label: str, value: str, accent) -> None:
        self._draw_game_panel(rect, (8, 42, 75), accent, 244)
        pygame.draw.circle(self.screen, accent, (rect.x + 34, rect.centery), 20)
        pygame.draw.circle(self.screen, (255, 245, 194), (rect.x + 34, rect.centery), 12, width=3)
        self._draw_text(label, self.font_tiny, (194, 215, 232), rect.x + 64, rect.y + 10)
        self._draw_text(value, self.font_mid, (255, 255, 255), rect.x + 64, rect.y + 30)

    def _draw_round_game_button(self, rect: pygame.Rect, label: str) -> None:
        hovered = rect.collidepoint(self._world_mouse_pos())
        pygame.draw.circle(self.screen, (236, 180, 61), rect.center, rect.width // 2)
        pygame.draw.circle(self.screen, (15, 66, 105) if not hovered else (27, 94, 143), rect.center, rect.width // 2 - 5)
        if label == "PAUSE":
            pygame.draw.rect(self.screen, (255, 255, 255), (rect.centerx - 10, rect.centery - 14, 7, 28), border_radius=2)
            pygame.draw.rect(self.screen, (255, 255, 255), (rect.centerx + 4, rect.centery - 14, 7, 28), border_radius=2)
        else:
            self._draw_text(label, self.font_mid, (255, 255, 255), rect.centerx, rect.centery - 13, center=True)

    def _draw_game_panel(self, rect: pygame.Rect, color, border, alpha: int = 240) -> None:
        shadow = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 100), shadow.get_rect(), border_radius=14)
        self.screen.blit(shadow, (rect.x + 4, rect.y + 5))
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (*color, alpha), surface.get_rect(), border_radius=12)
        pygame.draw.rect(surface, (*border, 255), surface.get_rect(), width=3, border_radius=12)
        pygame.draw.rect(surface, (255, 255, 255, 70), surface.get_rect().inflate(-8, -8), width=1, border_radius=9)
        self.screen.blit(surface, rect)

    def _handle_gameplay_mouse_click(self, pos: tuple[int, int]) -> None:
        if self.state != GameState.PLAYING:
            return

        if getattr(self, "delivery_confirmation_open", False):
            if self._delivery_checkbox_rect and self._delivery_checkbox_rect.collidepoint(pos):
                self.delivery_checkbox_checked = not self.delivery_checkbox_checked
                return

            if self._delivery_confirm_rect and self._delivery_confirm_rect.collidepoint(pos):
                self._confirm_player_delivery()
                return

            if self._delivery_cancel_rect and self._delivery_cancel_rect.collidepoint(pos):
                self.delivery_confirmation_open = False
                self.delivery_checkbox_checked = False
                self._delivery_prompt_dismissed_pos = self.player.grid_pos if self.player else None
                return

            return

        if self._game_sound_rect and self._game_sound_rect.collidepoint(pos):
            self.settings.toggle_sound()
            return

        if self._game_pause_rect and self._game_pause_rect.collidepoint(pos):
            self.state = GameState.PAUSED
            return

        action_rect = getattr(self, "_delivery_action_rect", None)
        if action_rect and action_rect.collidepoint(pos):
            task = getattr(self, "player_task", None)
            if (
                task
                and getattr(task, "picked_up", False)
                and self.player
                and self.player.grid_pos == task.house_pos
            ):
                self.delivery_confirmation_open = True
                self.delivery_checkbox_checked = False
                self.player.stop()
                self.move_dir = (0, 0)
                return

        indices = list(getattr(self, "_order_card_indices", []))
        for visible_index, rect in enumerate(getattr(self, "_order_card_rects", [])):
            if rect.collidepoint(pos):
                index = indices[visible_index] if visible_index < len(indices) else visible_index
                self._select_player_order(index)
                return

        for index, rect in enumerate(getattr(self, "_offer_marker_rects", [])):
            if rect.collidepoint(pos):
                self._select_player_order(index)
                return

    def _draw_panel(self, rect: pygame.Rect, alpha: int = 150, border: bool = True) -> None:
        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        panel.fill((10, 14, 22, alpha))
        self.screen.blit(panel, (rect.x, rect.y))

        if border:
            pygame.draw.rect(self.screen, (255, 255, 255), rect, width=1, border_radius=6)
