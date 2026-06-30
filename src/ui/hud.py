from __future__ import annotations

# pyrefly: ignore [missing-import]
import pygame

from src.core.constants import SCREEN_HEIGHT, SCREEN_WIDTH
from src.core.game_state import GameState
from src.ui.left_information_card import LeftInformationCardMixin
from src.ui.left_active_delivery_card import LeftActiveDeliveryCardMixin
from src.ui.left_order_card import LeftOrderCardMixin


class HudMixin(LeftInformationCardMixin, LeftActiveDeliveryCardMixin, LeftOrderCardMixin):
    def _draw_simulation_hud(self) -> None:
        if getattr(self, "auto_visual_enabled", False):
            self._draw_auto_visual_play_controls()
            return

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

    def _draw_auto_visual_play_controls(self) -> None:
        self._game_sound_rect = pygame.Rect(SCREEN_WIDTH - 150, 14, 58, 58)
        self._game_pause_rect = pygame.Rect(SCREEN_WIDTH - 80, 14, 58, 58)
        sound_img = self.ui_sound_on if getattr(self.settings, "sound_enabled", True) else self.ui_sound_off
        self._draw_round_game_button(self._game_sound_rect, "ON", sound_img)
        self._draw_round_game_button(self._game_pause_rect, "PAUSE", getattr(self, "ui_pause_button", None))

    def _draw_auto_visual_hud(self) -> None:
        from src.gameplay.auto.algorithm_groups import get_group_name

        top_bar = pygame.Rect(0, 0, SCREEN_WIDTH, 30)
        self._draw_panel(top_bar, alpha=110, border=False)

        group_id = int(getattr(self, "auto_visual_group_id", 1))
        group_name = get_group_name(group_id)
        selected_adversarial = str(
            getattr(
                self,
                "auto_visual_adversarial_algorithm",
                getattr(self.settings, "selected_adversarial_algorithm", "ALPHA_BETA"),
            )
        ).upper()
        status = "DONE" if getattr(self, "auto_visual_finished", False) else "RUNNING"
        error = getattr(self, "auto_visual_error", "")
        if error:
            status = "ERROR"

        text = (
            f"AUTO MODE | LEVEL G{group_id} | MAP {self.settings.selected_map_id:02d} | "
            f"{status} | ESC Pause | P Path | G Grid"
        )
        self._draw_text(text, self.font_tiny, (255, 255, 255), 12, 7)

        # Group select buttons. Click G1..G6 to restart visual demo for that group.
        # Vẽ thành panel lớn, rõ chữ, không bị lẫn vào nền map.
        self.auto_visual_group_button_rects = {}
        selector_panel = pygame.Rect(-2000, -2000, 1, 1)
        self._draw_panel(selector_panel, alpha=185, border=True)
        self._draw_text(
            "CHỌN NHÓM:",
            self.font_tiny_bold,
            (255, 235, 130),
            selector_panel.x + 14,
            selector_panel.y + 10,
        )
        self._draw_text(
            "Click G1..G6 để đổi nhóm thuật toán",
            self.font_tiny,
            (220, 240, 255),
            selector_panel.x + 14,
            selector_panel.y + 35,
        )

        button_w = 86
        button_h = 38
        gap = 8
        start_x = selector_panel.x + 150
        y_button = selector_panel.y + 12

        for current_group_id in range(1, 7):
            rect = pygame.Rect(
                start_x + (current_group_id - 1) * (button_w + gap),
                y_button,
                button_w,
                button_h,
            )
            self.auto_visual_group_button_rects[current_group_id] = rect

            active = current_group_id == group_id
            bg = (255, 204, 70) if active else (25, 58, 92)
            border = (255, 245, 170) if active else (100, 170, 220)
            text_color = (18, 36, 58) if active else (235, 245, 255)

            pygame.draw.rect(self.screen, bg, rect, border_radius=10)
            pygame.draw.rect(self.screen, border, rect, width=3 if active else 2, border_radius=10)
            self._draw_text(
                f"G{current_group_id}",
                self.font_small,
                text_color,
                rect.centerx,
                rect.y + 7,
                center=True,
            )

        plans = list(getattr(self, "auto_visual_plans", []))
        colors = [
            (255, 80, 80),
            (60, 235, 125),
            (255, 180, 55),
        ]
        shippers_by_algorithm = {
            getattr(npc, "algorithm", ""): npc
            for npc in getattr(self, "npc_shippers", [])
        }

        side = pygame.Rect(14, 44, 328, 290)
        self._draw_game_panel(side, (6, 18, 34), (229, 168, 58), 232)
        self._draw_fitted_text("AUTO VISUAL", self.font_small_bold, (255, 224, 91), pygame.Rect(side.x + 16, side.y + 14, side.width - 32, 24), center=True)
        self._draw_fitted_text(f"LEVEL G{group_id}", self.font_mid, (255, 255, 255), pygame.Rect(side.x + 18, side.y + 48, 130, 34), center=True)
        self._draw_fitted_text(group_name, self.font_tiny_bold, (218, 238, 250), pygame.Rect(side.x + 152, side.y + 54, side.width - 170, 24), center=True)

        minutes = int(getattr(self, "elapsed_time", 0.0)) // 60
        seconds = int(getattr(self, "elapsed_time", 0.0)) % 60
        npc_count_text = f"{len(plans):02d}"
        chips = [
            ("MAP", f"{self.settings.selected_map_id:02d}", (75, 166, 237)),
            ("TIME", f"{minutes:02d}:{seconds:02d}", (255, 180, 55)),
            ("NPC", npc_count_text, (60, 235, 125)),
        ]
        for index, (label, value, accent) in enumerate(chips):
            chip = pygame.Rect(side.x + 18 + index * 98, side.y + 92, 86, 54)
            self._draw_dashboard_chip(chip, label, value, accent)

        matchup_text = f"2 NPC - {selected_adversarial} vs GREEDY" if group_id == 6 else "3 NPC - 3 thuat toan"
        self._draw_fitted_text(matchup_text, self.font_tiny_bold, (255, 224, 91), pygame.Rect(side.x + 18, side.y + 160, side.width - 36, 22), center=True)
        legend_y = side.y + 190
        for index, plan in enumerate(plans[:3]):
            npc = shippers_by_algorithm.get(plan.algorithm)
            color = getattr(npc, "auto_visual_color", colors[index % len(colors)]) if npc else colors[index % len(colors)]
            row = pygame.Rect(side.x + 18, legend_y + index * 30, side.width - 36, 24)
            pygame.draw.rect(self.screen, (8, 35, 55, 185), row, border_radius=7)
            pygame.draw.circle(self.screen, color, (row.x + 14, row.centery), 7)
            pygame.draw.circle(self.screen, (255, 255, 255), (row.x + 14, row.centery), 7, 1)
            self._draw_fitted_text(plan.algorithm, self.font_tiny_bold, color, pygame.Rect(row.x + 30, row.y + 2, row.width - 36, 20))

        board_w = 460
        row_h = 68 if group_id in (4, 5) else 48
        selector_h = 42 if group_id == 6 else 0
        board_h = 62 + selector_h + max(1, len(plans)) * row_h + 8
        board = pygame.Rect(SCREEN_WIDTH - board_w - 16, 54, board_w, board_h)
        self._draw_panel(board, alpha=150, border=True)

        self._draw_text(
            f"LEVEL G{group_id}: {group_name}",
            self.font_small,
            (255, 230, 110),
            board.x + 16,
            board.y + 12,
        )
        pygame.draw.rect(self.screen, (10, 14, 22), pygame.Rect(board.x + 12, board.y + 32, board.width - 24, 22))
        board_hint = f"Nhom 6: {selected_adversarial} dau voi AI GREEDY" if group_id == 6 else "Chon level o man hinh chinh - moi level chay 3 NPC"
        self._draw_text(
            board_hint,
            self.font_tiny,
            (185, 220, 245),
            board.x + 16,
            board.y + 36,
        )

        self.auto_visual_adversarial_button_rects = {}

        if error:
            self._draw_text(error[:70], self.font_tiny, (255, 120, 120), board.x + 16, board.y + 60)
            return

        y = board.y + 64
        if group_id == 6:
            algorithms = ("MINIMAX", "ALPHA_BETA", "EXPECTIMAX")
            button_y = board.y + 58
            button_w = 132
            gap = 8
            start_x = board.x + 16

            for index, algorithm in enumerate(algorithms):
                rect = pygame.Rect(start_x + index * (button_w + gap), button_y, button_w, 30)
                self.auto_visual_adversarial_button_rects[algorithm] = rect
                active = algorithm == selected_adversarial
                bg = (255, 204, 70) if active else (16, 48, 78)
                border = (255, 245, 170) if active else (88, 145, 190)
                text_color = (18, 36, 58) if active else (235, 245, 255)
                pygame.draw.rect(self.screen, bg, rect, border_radius=7)
                pygame.draw.rect(self.screen, border, rect, width=2, border_radius=7)
                self._draw_fitted_text(algorithm, self.font_tiny_bold, text_color, rect.inflate(-8, -6), center=True)

            y = button_y + 42

        for index, plan in enumerate(plans):
            npc = shippers_by_algorithm.get(plan.algorithm)
            color = (
                getattr(npc, "auto_visual_color", colors[index % len(colors)])
                if npc
                else colors[index % len(colors)]
            )
            done = bool(npc and self.auto_visual_completed.get(npc.name, False))
            failed = bool(npc and getattr(npc, "auto_visual_failed", False))
            current_pos = npc.grid_pos if npc else "-"
            if failed:
                progress = "FAILED"
            elif done:
                progress = "DONE"
            else:
                progress = str(current_pos)
            trap_hits = int(getattr(npc, "auto_visual_trap_hits", 0)) if npc else 0

            pygame.draw.circle(self.screen, color, (board.x + 22, y + 13), 7)
            label = (
                f"{index + 1}. {plan.algorithm}: "
                f"cost={round(plan.total_cost, 1)} | "
                f"expanded={plan.expanded_nodes} | "
                f"trap={trap_hits} | "
                f"time={plan.runtime_ms:.2f}ms | {progress}"
            )
            self._draw_fitted_text(
                label,
                self.font_tiny,
                (245, 245, 245),
                pygame.Rect(board.x + 40, y - 1, board.width - 56, 18),
            )

            note = plan.note or plan.group_name
            self._draw_text(note[:70], self.font_tiny, (180, 210, 235), board.x + 40, y + 19)

            if group_id == 4:
                belief_parts = []
                max_show = 6 if plan.algorithm == "AND_OR_SEARCH" else 2
                for belief_index, traps in enumerate(getattr(plan, "belief_states", ())[:max_show]):
                    name = "Case" if plan.algorithm == "AND_OR_SEARCH" else "Kha nang"
                    belief_parts.append(f"{name} {belief_index + 1}: {len(traps)} bay")
                known_count = len(getattr(plan, "known_traps", ()))
                if known_count:
                    belief_parts.append(f"biet truoc: {known_count}")
                if belief_parts:
                    self._draw_text(
                        " | ".join(belief_parts)[:76],
                        self.font_tiny,
                        (255, 215, 120),
                        board.x + 40,
                        y + 38,
                    )

            if group_id == 5:
                order_sequence = []
                for action in getattr(plan, "actions", ()):
                    if action.startswith("P_"):
                        order_sequence.append(action[2:])
                if order_sequence:
                    csp_line = "Thu tu: " + " -> ".join(order_sequence)
                    self._draw_text(
                        csp_line[:76],
                        self.font_tiny,
                        (255, 215, 120),
                        board.x + 40,
                        y + 38,
                    )

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
        sound_img = self.ui_sound_on if getattr(self.settings, "sound_enabled", True) else self.ui_sound_off
        self._draw_round_game_button(self._game_sound_rect, "ON", sound_img)
        self._draw_round_game_button(self._game_pause_rect, "PAUSE", getattr(self, "ui_pause_button", None))

        if self._has_letterbox_side_rails():
            self._order_card_rects = []
            if getattr(self, "delivery_confirmation_open", False):
                self._draw_delivery_confirmation()
            return

        panel = pygame.Rect(14, 14, 340, SCREEN_HEIGHT - 28)
        self._draw_left_side_panel(panel)
        self._draw_delivery_timeout_notice()

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

    def _draw_delivery_timeout_notice(self) -> None:
        if float(getattr(self, "delivery_timeout_notice_until", 0.0)) <= float(getattr(self, "elapsed_time", 0.0)):
            return

        message = str(getattr(self, "last_delivery_timeout_message", ""))
        if not message:
            return

        rect = pygame.Rect(SCREEN_WIDTH // 2 - 210, 86, 420, 48)
        self._draw_game_panel(rect, (118, 37, 34), (255, 198, 82), 246)
        self._draw_fitted_text(message, self.font_small_bold, (255, 245, 218), rect.inflate(-24, -12), center=True)

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

    def _draw_round_game_button(self, rect: pygame.Rect, label: str, image=None) -> None:
        hovered = rect.collidepoint(self._world_mouse_pos())

        draw_rect = rect.copy()
        if hovered:
            draw_rect.inflate_ip(5, 5)

        if image:
            scaled = pygame.transform.smoothscale(image, draw_rect.size)
            self.screen.blit(scaled, draw_rect)
            return

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
            self._toggle_sound()
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
