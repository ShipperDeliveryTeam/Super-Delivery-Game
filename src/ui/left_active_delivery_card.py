from __future__ import annotations

from typing import Tuple

# pyrefly: ignore [missing-import]
import pygame

from src.core.constants import SCREEN_WIDTH


class LeftActiveDeliveryCardMixin:
    def _draw_compact_status_card(self, rect: pygame.Rect) -> None:
        self._delivery_action_rect = None
        has_asset = self._draw_trimmed_ui_asset(getattr(self, "ui_delivery_active_card", None), rect)
        if not has_asset:
            pygame.draw.rect(self.screen, (236, 226, 203), rect, border_radius=10)
            pygame.draw.rect(self.screen, (238, 203, 114), rect, width=3, border_radius=10)
            pygame.draw.rect(self.screen, (255, 255, 255), rect.inflate(-6, -6), width=1, border_radius=8)

        task = self.player_task if getattr(self.player_task, "picked_up", False) else None
        preview = task

        header = pygame.Rect(rect.x, rect.y, rect.width, 32)
        if not has_asset:
            pygame.draw.rect(self.screen, (26, 78, 110), header, border_top_left_radius=8, border_top_right_radius=8)
            pygame.draw.line(self.screen, (255, 200, 76), (header.x, header.bottom), (header.right, header.bottom), 2)
            title = "DANG GIAO" if task else "DON DANG CHON"
            self._draw_fitted_text(title, self.font_tiny, (255, 230, 119), header, center=True)

        if not preview:
            return

        house = self._house_number(preview.house_pos)
        status = "TOI NHA" if getattr(preview, "picked_up", False) else "LAY HANG"
        remaining = self._delivery_display_seconds(preview)
        time_text = self._format_seconds(remaining)
        time_color = (
            (220, 55, 40)
            if getattr(preview, "picked_up", False) and remaining <= 15
            else (255, 213, 74)
        )

        if has_asset:
            gold = (255, 213, 74)
            font = getattr(self, "font_small_bold", getattr(self, "font_mid", None))
            house_val_rect = pygame.Rect(rect.x + int(rect.width * 0.49) - 20, rect.y + int(rect.height * 0.22) - 5, int(rect.width * 0.45), int(rect.height * 0.26))
            time_val_rect = pygame.Rect(rect.x + int(rect.width * 0.49) - 20, rect.y + int(rect.height * 0.42) - 5, int(rect.width * 0.45), int(rect.height * 0.22))
            coin_val_rect = pygame.Rect(rect.x + int(rect.width * 0.49) - 20, rect.y + int(rect.height * 0.55) - 5, int(rect.width * 0.45), int(rect.height * 0.22))
            self._delivery_action_rect = pygame.Rect(
                rect.x + int(rect.width * 0.06),
                rect.y + int(rect.height * 0.73),
                int(rect.width * 0.88),
                int(rect.height * 0.20),
            )
            self._draw_fitted_text(f"Nha {house:02d}", font, gold, house_val_rect, center=True)
            self._draw_fitted_text(time_text, font, time_color, time_val_rect, center=True)
            self._draw_fitted_text(f"{preview.reward} xu", font, gold, coin_val_rect, center=True)
            return

        self._draw_status_row(rect.x + 14, rect.y + 44, "SHOP", self._store_display_name(preview.store_pos))
        self._draw_status_row(rect.x + 160, rect.y + 44, "TG", time_text)
        self._draw_status_row(rect.x + 14, rect.y + 70, "NHA", f"{house:02d}")
        self._draw_status_row(rect.x + 160, rect.y + 70, "XU", str(preview.reward))

        status_box = pygame.Rect(rect.x + 14, rect.bottom - 32, rect.width - 28, 24)
        self._delivery_action_rect = status_box
        pygame.draw.rect(self.screen, (47, 163, 67), status_box, border_radius=8)
        pygame.draw.rect(self.screen, (235, 255, 220), status_box, width=1, border_radius=8)
        self._draw_fitted_text(status, self.font_tiny, (255, 255, 255), status_box, center=True)

    def _draw_side_status_card(self, rail: pygame.Rect) -> None:
        card = pygame.Rect(rail.x + 10, rail.y + 58, max(90, rail.width - 20), 204)
        self._draw_game_panel(card, (234, 222, 187), (225, 166, 62), 248)

        task = self.player_task
        selected_index = getattr(self, "selected_player_order_index", -1)
        offers = list(getattr(self, "available_player_tasks", []))
        preview = task or (offers[selected_index] if 0 <= selected_index < len(offers) else None)

        title = "DANG GIAO" if task else "DON CHON"
        header = pygame.Rect(card.x + 8, card.y + 8, card.width - 16, 30)
        pygame.draw.rect(self.screen, (24, 78, 108), header, border_radius=8)
        self._draw_fitted_text(title, self.font_tiny, (255, 230, 119), header, center=True)

        if preview:
            house = self._house_number(preview.house_pos)
            status = "TOI NHA" if getattr(preview, "picked_up", False) else "LAY HANG"
            remaining = self._delivery_display_seconds(preview)
            time_text = self._format_seconds(remaining)
            self._draw_status_row(card.x + 13, card.y + 52, "SHOP", self._store_display_name(preview.store_pos))
            self._draw_status_row(card.x + 160, card.y + 52, "TG", time_text)
            self._draw_status_row(card.x + 13, card.y + 84, "NHA", f"{house:02d}")
            self._draw_status_row(card.x + 160, card.y + 84, "XU", str(preview.reward))

            status_box = pygame.Rect(card.x + 12, card.bottom - 42, card.width - 24, 28)
            pygame.draw.rect(self.screen, (40, 153, 69), status_box, border_radius=8)
            pygame.draw.rect(self.screen, (235, 255, 220), status_box, width=2, border_radius=8)
            self._draw_fitted_text(status, self.font_tiny, (255, 255, 255), status_box, center=True)

        delivered = list(getattr(self, "delivered_house_numbers", []))[-7:]
        history = pygame.Rect(rail.x + 10, card.bottom + 14, max(90, rail.width - 20), 66 + len(delivered) * 29)
        self._draw_game_panel(history, (18, 49, 72), (82, 151, 188), 242)
        self._draw_fitted_text("DA GIAO", self.font_tiny, (255, 224, 91), pygame.Rect(history.x + 10, history.y + 12, history.width - 20, 22), center=True)

        if delivered:
            for index, number in enumerate(delivered):
                y = history.y + 48 + index * 29
                check = pygame.Rect(history.x + 12, y, 20, 20)
                pygame.draw.rect(self.screen, (57, 178, 64), check, border_radius=5)
                self._draw_check_mark(check)
                self._draw_fitted_text(f"Nha {number:02d}", self.font_tiny, (230, 241, 246), pygame.Rect(check.right + 8, y + 1, history.right - check.right - 20, 18))
        else:
            self._draw_fitted_text("0 nha", self.font_tiny, (193, 213, 226), pygame.Rect(history.x + 10, history.y + 43, history.width - 20, 22), center=True)

    def _draw_status_row(self, x: int, y: int, label: str, value: str) -> None:
        label_rect = pygame.Rect(x, y, 44, 20)
        pygame.draw.rect(self.screen, (34, 89, 118), label_rect, border_radius=6)
        self._draw_fitted_text(label, self.font_tiny, (230, 243, 250), label_rect, center=True)
        self._draw_fitted_text(value, self.font_tiny, (45, 53, 46), pygame.Rect(x + 51, y + 1, 72, 20))

    def _draw_fitted_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: Tuple[int, int, int],
        rect: pygame.Rect,
        center: bool = False,
        y_offset: int = 0,
    ) -> None:
        text = str(text)
        max_width = max(1, rect.width)

        if font.size(text)[0] > max_width:
            suffix = "..."
            while text and font.size(text + suffix)[0] > max_width:
                text = text[:-1]
            text = (text + suffix) if text else suffix

        surface = font.render(text, True, color)
        text_rect = surface.get_rect()

        if center:
            text_rect.center = rect.center
            text_rect.y += y_offset
        else:
            text_rect.topleft = (rect.x, rect.y + y_offset)

        self.screen.blit(surface, text_rect)

    def _draw_delivery_confirmation(self) -> None:
        task = self.player_task

        if task is None:
            return

        panel = pygame.Rect(SCREEN_WIDTH - 560, 250, 520, 347)
        has_asset = self._draw_trimmed_ui_asset(getattr(self, "ui_delivery_confirm_popup", None), panel)
        if not has_asset:
            self._draw_game_panel(panel, (233, 218, 173), (115, 70, 27), 250)
            header = pygame.Rect(panel.x + 8, panel.y + 8, panel.width - 16, 55)
            self._draw_game_panel(header, (45, 111, 54), (238, 190, 66), 255)
            self._draw_text("XAC NHAN GIAO HANG", self.font_small, (255, 248, 205), header.centerx, header.y + 17, center=True)

        house = self._house_number(task.house_pos)
        checked = getattr(self, "delivery_checkbox_checked", False)

        if has_asset:
            order_value = pygame.Rect(panel.x + int(panel.width * 0.4), panel.y + int(panel.height * 0.38), int(panel.width * 0.34), 28)
            house_value = pygame.Rect(panel.x + int(panel.width * 0.4), panel.y + int(panel.height * 0.55), int(panel.width * 0.34), 28)
            self._draw_fitted_text(f"#{task.order_id}", self.font_mid, (55, 39, 23), order_value, center=True)
            self._draw_fitted_text(f"Nha {house:02d}", self.font_mid, (55, 39, 23), house_value, center=True)

            check = pygame.Rect(
                panel.x + int(panel.width * 0.132),
                panel.y + int(panel.height * 0.626),
                int(panel.width * 0.052),
                int(panel.height * 0.074),
            )
            self._delivery_checkbox_rect = pygame.Rect(check.x - 8, check.y - 8, check.width + 170, check.height + 16)
            self._delivery_confirm_rect = pygame.Rect(
                panel.x + int(panel.width * 0.17),
                panel.y + int(panel.height * 0.772),
                int(panel.width * 0.31),
                int(panel.height * 0.085),
            )
            self._delivery_cancel_rect = pygame.Rect(
                panel.x + int(panel.width * 0.59),
                panel.y + int(panel.height * 0.772),
                int(panel.width * 0.28),
                int(panel.height * 0.085),
            )
        else:
            self._draw_text(f"Don #{task.order_id}", self.font_mid, (55, 39, 23), panel.x + 28, panel.y + 84)
            self._draw_text(f"Nha {house:02d}", self.font_small, (92, 69, 38), panel.x + 28, panel.y + 122)
            self._delivery_checkbox_rect = pygame.Rect(panel.x + 24, panel.y + 168, panel.width - 48, 58)
            pygame.draw.rect(self.screen, (245, 241, 220), self._delivery_checkbox_rect, border_radius=9)
            pygame.draw.rect(self.screen, (45, 105, 168), self._delivery_checkbox_rect, width=3, border_radius=9)
            check = pygame.Rect(self._delivery_checkbox_rect.x + 12, self._delivery_checkbox_rect.y + 10, 38, 38)
            pygame.draw.rect(self.screen, (55, 178, 61) if checked else (210, 210, 196), check, border_radius=6)
            pygame.draw.rect(self.screen, (34, 105, 45), check, width=2, border_radius=6)

        if checked:
            self._draw_check_mark(check)

        if not has_asset:
            self._draw_text("Da giao", self.font_small, (49, 49, 43), check.right + 14, self._delivery_checkbox_rect.y + 18)
            self._delivery_confirm_rect = pygame.Rect(panel.x + 24, panel.bottom - 76, 190, 50)
            self._delivery_cancel_rect = pygame.Rect(panel.x + 226, panel.bottom - 76, 110, 50)
            confirm_color = (46, 165, 54) if checked else (105, 123, 105)
            pygame.draw.rect(self.screen, confirm_color, self._delivery_confirm_rect, border_radius=10)
            pygame.draw.rect(self.screen, (241, 220, 102), self._delivery_confirm_rect, width=3, border_radius=10)
            pygame.draw.rect(self.screen, (139, 65, 37), self._delivery_cancel_rect, border_radius=10)
            pygame.draw.rect(self.screen, (235, 175, 91), self._delivery_cancel_rect, width=3, border_radius=10)
            self._draw_text("XAC NHAN", self.font_small, (255, 255, 255), self._delivery_confirm_rect.centerx, self._delivery_confirm_rect.y + 15, center=True)
            self._draw_text("HUY", self.font_small, (255, 255, 255), self._delivery_cancel_rect.centerx, self._delivery_cancel_rect.y + 15, center=True)


    def _draw_delivered_houses_panel(self) -> None:
        values = list(getattr(self, "delivered_house_numbers", []))[-5:]
        height = 58 + len(values) * 38
        panel = pygame.Rect(SCREEN_WIDTH - 330, 674, 310, height)
        self._draw_game_panel(panel, (232, 220, 185), (82, 112, 145), 246)
        self._draw_text("NHÀ ĐÃ GIAO", self.font_small, (20, 66, 102), panel.centerx, panel.y + 16, center=True)

        for index, number in enumerate(values):
            y = panel.y + 52 + index * 38
            pygame.draw.rect(self.screen, (57, 178, 64), (panel.x + 18, y, 28, 28), border_radius=5)
            self._draw_check_mark(pygame.Rect(panel.x + 18, y, 28, 28))
            self._draw_text(f"Nhà {number:02d}", self.font_tiny, (48, 50, 44), panel.x + 58, y + 5)


    def _draw_check_mark(self, rect: pygame.Rect) -> None:
        points = [
            (rect.x + int(rect.width * 0.22), rect.y + int(rect.height * 0.52)),
            (rect.x + int(rect.width * 0.43), rect.y + int(rect.height * 0.73)),
            (rect.x + int(rect.width * 0.80), rect.y + int(rect.height * 0.27)),
        ]
        pygame.draw.lines(self.screen, (255, 255, 255), False, points, max(3, rect.width // 8))


