from __future__ import annotations

# pyrefly: ignore [missing-import]
import pygame

from src.core.game_state import GameState


class LeftOrderCardMixin:
    def _draw_left_orders_card(self, orders_panel: pygame.Rect) -> None:
        self._orders_panel_rect = orders_panel
        has_orders_asset = self._draw_trimmed_ui_asset(getattr(self, "ui_order_card", None), orders_panel)
        if not has_orders_asset:
            self._draw_game_panel(orders_panel, (13, 60, 95), (236, 178, 58), 248)
            self._draw_fitted_text("DON HANG", self.font_tiny, (255, 224, 91), pygame.Rect(orders_panel.x + 12, orders_panel.y + 10, orders_panel.width - 24, 30), center=True)

        self._order_card_rects = []
        self._order_card_indices = []
        offers = list(getattr(self, "available_player_tasks", []))
        card_x = orders_panel.x + 30
        card_y = orders_panel.y + int(orders_panel.height * 0.15)
        card_w = orders_panel.width - 64
        cargo_rect = pygame.Rect(orders_panel.x + 24, orders_panel.bottom - 64, orders_panel.width - 48, 54)
        available_h = max(0, cargo_rect.y - card_y - 10)

        visible_count = min(2, len(offers)) if offers else 0
        max_scroll = max(0, len(offers) - visible_count)
        scroll_offset = max(0, min(int(getattr(self, "order_scroll_offset", 0)), max_scroll))
        self.order_scroll_offset = scroll_offset
        card_h = 118
        if visible_count > 0:
            card_h = min(132, max(116, (available_h - max(0, visible_count - 1) * 12) // visible_count))

        for row, task in enumerate(offers[scroll_offset:scroll_offset + visible_count]):
            index = scroll_offset + row
            rect = pygame.Rect(card_x, card_y + row * (card_h + 12), card_w, card_h)
            self._order_card_rects.append(rect)
            self._order_card_indices.append(index)
            self._draw_side_order_card(rect, task, index)

        if len(offers) > visible_count > 0:
            track = pygame.Rect(orders_panel.right - 18, card_y, 6, available_h)
            pygame.draw.rect(self.screen, (7, 24, 39), track, border_radius=3)
            pygame.draw.rect(self.screen, (74, 130, 164), track, width=1, border_radius=3)
            thumb_h = max(26, int(track.height * visible_count / len(offers)))
            thumb_y = track.y + int((track.height - thumb_h) * (scroll_offset / max(1, max_scroll)))
            thumb = pygame.Rect(track.x + 1, thumb_y, track.width - 2, thumb_h)
            pygame.draw.rect(self.screen, (255, 201, 70), thumb, border_radius=3)

        if not offers:
            empty = pygame.Rect(card_x, card_y, card_w, 120)
            self._draw_game_panel(empty, (15, 51, 77), (74, 128, 165), 235)
            self._draw_fitted_text("DANG TIM DON", self.font_tiny, (220, 235, 245), empty, center=True)

        self._draw_left_cargo_card(cargo_rect, draw_frame=not has_orders_asset)

    def _shop_card_image(self, task):
        if task is None:
            return None

        name = self._store_display_name(task.store_pos)
        key = "".join(ch for ch in name.lower() if ch.isalnum())
        all_images = getattr(self, "shop_card_images", {})
        map_id = int(getattr(getattr(self, "settings", None), "selected_map_id", 1))
        images = all_images.get(map_id, {}) if isinstance(all_images, dict) else {}

        store_id = str(getattr(self, "store_ids", {}).get(task.store_pos, "")).strip().lower()
        if store_id in images:
            return images[store_id]

        if key in images:
            return images[key]

        for image_key, image in images.items():
            if key and (key in image_key or image_key in key):
                return image

        return None

    def _blit_cover(self, image, rect: pygame.Rect) -> None:
        if image is None or rect.width <= 0 or rect.height <= 0:
            return

        iw, ih = image.get_size()
        scale = max(rect.width / max(1, iw), rect.height / max(1, ih))
        size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
        scaled = pygame.transform.smoothscale(image, size)
        crop = pygame.Rect(0, 0, rect.width, rect.height)
        crop.center = scaled.get_rect().center
        self.screen.blit(scaled, rect, crop)

    def _draw_left_cargo_card(self, rect: pygame.Rect, draw_frame: bool = True) -> None:
        if draw_frame:
            pygame.draw.rect(self.screen, (20, 52, 80), rect, border_radius=8)
            pygame.draw.rect(self.screen, (90, 130, 155), rect, width=2, border_radius=8)

        box_icon = getattr(self, "icons", {}).get("box", None)
        if draw_frame and box_icon:
            icon_size = 42
            scaled_icon = pygame.transform.smoothscale(box_icon, (icon_size, icon_size))
            self.screen.blit(scaled_icon, (rect.x + 10, rect.centery - icon_size // 2))

        player_tasks = [
            task for task in getattr(self, "player_tasks", [])
            if getattr(task, "picked_up", False) and not getattr(task, "delivered", False)
        ]
        cargo_limit = int(getattr(self, "PLAYER_CARGO_LIMIT", 3))
        cargo_state = f"{len(player_tasks)} / {cargo_limit}"
        delivered = len(getattr(self, "delivered_house_numbers", []))
        gold = (255, 213, 74)

        if draw_frame:
            self._draw_text("HANG", self.font_tiny, gold, rect.x + 60, rect.y + 12)
            self._draw_text(cargo_state, self.font_small, gold, rect.x + 60, rect.y + 32)
        else:
            self._draw_fitted_text(cargo_state.replace(" ", ""), getattr(self, "font_small", self.font_tiny), gold, pygame.Rect(rect.x - 15, rect.y + 40, 80, 20), center=True)

        slot_size = min(42, rect.height - 14)
        slot_x = rect.x + (118 if draw_frame else 75)
        for index in range(cargo_limit):
            slot = pygame.Rect(slot_x + index * (slot_size + 8), rect.y + 5, slot_size, slot_size)
            if draw_frame:
                pygame.draw.rect(self.screen, (8, 22, 34), slot, border_radius=7)
                pygame.draw.rect(self.screen, (104, 82, 42), slot, width=2, border_radius=7)
            if index < len(player_tasks) and box_icon:
                box_rect = slot.inflate(-3, -3)
                scaled_box = pygame.transform.smoothscale(box_icon, box_rect.size)
                self.screen.blit(scaled_box, box_rect)

        if draw_frame:
            self._draw_text(f"Giao {delivered}", self.font_tiny, gold, rect.right - 62, rect.centery - 8)

    def _draw_side_order_card(self, rect: pygame.Rect, task, index: int) -> None:
        selected = index == getattr(self, "selected_player_order_index", -1)
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        locked = bool(
            self.player_task
            and self.player_task.picked_up
            and self.player_task is not task
            and task not in getattr(self, "player_tasks", [])
        )
        has_asset = self._draw_trimmed_ui_asset(getattr(self, "ui_shop_order_card", None), rect)

        border = (93, 232, 108) if selected else ((255, 205, 84) if hovered else (79, 145, 184))
        fill = (236, 226, 203) if not locked else (180, 180, 180)

        if not has_asset:
            pygame.draw.rect(self.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.screen, border, rect, width=3 if selected else 1, border_radius=8)
            if selected:
                pygame.draw.rect(self.screen, (255, 255, 255), rect.inflate(-6, -6), width=1, border_radius=6)

        header = pygame.Rect(rect.x, rect.y, rect.width, 24)
        if not has_asset:
            pygame.draw.rect(self.screen, (26, 78, 110) if not locked else (100, 100, 100), header, border_top_left_radius=8, border_top_right_radius=8)

        name = self._store_display_name(task.store_pos)
        house = self._house_number(task.house_pos)

        if not has_asset:
            self._draw_fitted_text(name, self.font_tiny, (255, 255, 255), pygame.Rect(header.x + 10, header.y + 2, header.width - 20, 20))

        if has_asset:
            dark_gold = (143, 87, 14)
            font = getattr(self, "font_small_bold", getattr(self, "font_mid", None))

            reward_rect = pygame.Rect(
                rect.x + int(rect.width * 0.65) - 18,
                rect.y + int(rect.height * 0.15) - 8,
                int(rect.width * 0.30),
                int(rect.height * 0.25),
            )
            house_rect = pygame.Rect(
                rect.x + int(rect.width * 0.65) - 12,
                rect.y + int(rect.height * 0.45) - 28,
                int(rect.width * 0.30),
                int(rect.height * 0.25),
            )
            button = pygame.Rect(
                rect.x + int(rect.width * 0.56),
                rect.y + int(rect.height * 0.68),
                int(rect.width * 0.41),
                int(rect.height * 0.30),
            )

            image = self._shop_card_image(task)
            if image:
                image_rect = pygame.Rect(
                    rect.x + int(rect.width * 0.02),
                    rect.y + int(rect.height * 0.04),
                    int(rect.width * 0.50),
                    int(rect.height * 0.91),
                )
                self._blit_cover(image, image_rect)

            self._draw_fitted_text(f"{task.reward} xu", font, dark_gold, reward_rect, center=True)
            self._draw_fitted_text(f"Nha {house:02d}", font, dark_gold, house_rect, center=True)
            if getattr(task, "stolen_by", None):
                button_key = "rob"
            else:
                button_key = "received" if task in getattr(self, "player_tasks", []) else "receive"
            button_icon = getattr(self, "icons", {}).get(button_key)
            if button_icon:
                scaled_button = pygame.transform.smoothscale(button_icon, button.size)
                self.screen.blit(scaled_button, button)
            else:
                button_color = (47, 163, 67) if not locked else (94, 103, 108)
                pygame.draw.rect(self.screen, button_color, button, border_radius=6)
                label = "DA NHAN" if task in getattr(self, "player_tasks", []) else "NHAN"
                self._draw_fitted_text(label, self.font_tiny, (255, 255, 255), button, center=True)
            return

        icon_rect = pygame.Rect(rect.x + 10, rect.y + 30, 28, 28)
        pygame.draw.rect(self.screen, (26, 78, 110), icon_rect, border_top_left_radius=14, border_top_right_radius=14)
        pygame.draw.circle(self.screen, (255, 174, 45), icon_rect.center, 12)
        self._draw_text("!", self.font_tiny, (255, 255, 255), icon_rect.centerx, icon_rect.y + 4, center=True)
        self._draw_fitted_text(f"{task.reward} xu", self.font_tiny, (143, 87, 14), pygame.Rect(rect.x + 46, rect.y + 36, 100, 20))

        route_y = rect.bottom - 26
        pygame.draw.circle(self.screen, (47, 163, 67), (rect.x + 16, route_y + 10), 4)
        pygame.draw.circle(self.screen, (75, 166, 237), (rect.x + 124, route_y + 10), 4)
        self._draw_fitted_text(f"SHOP -> Nha {house:02d}", self.font_tiny, (43, 55, 54), pygame.Rect(rect.x + 24, route_y + 1, 90, 20))

        button = pygame.Rect(rect.right - 90, rect.bottom - 30, 80, 24)
        button_color = (47, 163, 67) if not locked else (94, 103, 108)
        pygame.draw.rect(self.screen, button_color, button, border_radius=6)
        label = "DA CHON" if selected else "NHAN"
        self._draw_fitted_text(label, self.font_tiny, (255, 255, 255), button, center=True)

    def _handle_letterbox_gameplay_mouse_click(self, pos: tuple[int, int]) -> bool:
        if not self._has_letterbox_side_rails():
            return False

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
                return True

        indices = list(getattr(self, "_order_card_indices", []))
        for visible_index, rect in enumerate(getattr(self, "_order_card_rects", [])):
            if rect.collidepoint(pos):
                index = indices[visible_index] if visible_index < len(indices) else visible_index
                self._select_player_order(index)
                return True

        return False

    def _handle_scroll_event(self, command) -> None:
        if self.state != GameState.PLAYING:
            return

        pos = pygame.mouse.get_pos() if self._has_letterbox_side_rails() else self._world_mouse_pos()
        panel = getattr(self, "_orders_panel_rect", None)
        if panel is not None and not panel.collidepoint(pos):
            return

        offers = list(getattr(self, "available_player_tasks", []))
        visible = min(2, len(offers)) if offers else 0
        max_scroll = max(0, len(offers) - visible)
        delta = int(getattr(command, "value", 0) or 0)
        self.order_scroll_offset = max(0, min(max_scroll, int(getattr(self, "order_scroll_offset", 0)) - delta))

    def _draw_order_card(self, rect: pygame.Rect, task, index: int) -> None:
        selected = index == getattr(self, "selected_player_order_index", -1)
        locked = bool(
            self.player_task
            and self.player_task.picked_up
            and self.player_task is not task
            and task not in getattr(self, "player_tasks", [])
        )
        hovered = rect.collidepoint(self._world_mouse_pos())
        fill = (239, 234, 209) if not locked else (137, 146, 151)
        border = (89, 230, 91) if selected else ((255, 197, 72) if hovered else (70, 128, 165))
        self._draw_game_panel(rect, fill, border, 244)

        badge = pygame.Rect(rect.x + 12, rect.y + 18, 64, 64)
        pygame.draw.rect(self.screen, (25, 82, 119), badge, border_radius=10)
        pygame.draw.circle(self.screen, (255, 172, 47), badge.center, 23)
        self._draw_text("!", self.font_mid, (255, 255, 255), badge.centerx, badge.y + 17, center=True)

        name = self._store_display_name(task.store_pos)[:18]
        house = self._house_number(task.house_pos)
        remaining = max(0, int(task.expires_in - (self.elapsed_time - task.created_at)))
        time_text = f"{remaining // 60:02d}:{remaining % 60:02d}"
        text_x = rect.x + 88
        text_color = (18, 52, 77) if not locked else (62, 70, 76)
        self._draw_text(name, self.font_small, text_color, text_x, rect.y + 14)
        self._draw_text(f"{task.reward} xu", self.font_tiny, (146, 91, 15), text_x, rect.y + 45)
        self._draw_text(time_text, self.font_tiny, text_color, text_x + 92, rect.y + 45)
        self._draw_text(f"Nha {house:02d}", self.font_tiny, text_color, text_x, rect.y + 70)

        button = pygame.Rect(text_x, rect.bottom - 43, 126, 32)
        button_color = (45, 169, 55) if not locked else (91, 100, 103)
        pygame.draw.rect(self.screen, button_color, button, border_radius=8)
        pygame.draw.rect(self.screen, (225, 255, 213), button, width=2, border_radius=8)
        label = "DA CHON" if selected else "NHAN DON"
        self._draw_text(label, self.font_tiny, (255, 255, 255), button.centerx, button.y + 7, center=True)

        if selected:
            pygame.draw.circle(self.screen, (50, 186, 61), (rect.right - 25, rect.y + 25), 17)
            self._draw_check_mark(pygame.Rect(rect.right - 38, rect.y + 12, 26, 26))
