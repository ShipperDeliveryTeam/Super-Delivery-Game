from __future__ import annotations

# pyrefly: ignore [missing-import]
import pygame


class LeftInformationCardMixin:
    def _draw_stats_grid(self, rect: pygame.Rect) -> None:
        has_asset = self._draw_trimmed_ui_asset(getattr(self, "ui_information_card", None), rect)
        if not has_asset:
            pygame.draw.rect(self.screen, (9, 21, 41), rect, border_radius=8)
            pygame.draw.rect(self.screen, (229, 168, 58), rect, width=2, border_radius=8)

        money = self.player.money if self.player else 0
        orders = self.player.orders if self.player else 0
        minutes = int(self.elapsed_time) // 60
        seconds = int(self.elapsed_time) % 60
        combo = max(1, min(9, orders + 1))

        pad = 8
        w = (rect.width - pad * 3) // 2
        h = (rect.height - pad * 3) // 2

        if has_asset:
            gold = (255, 213, 74)
            font = getattr(self, "font_small_bold", getattr(self, "font_mid", None))

            box_xu = pygame.Rect(rect.x + pad + int(w * 0.40) - 5, rect.y + pad + 13, int(w * 0.60), h)
            self._draw_fitted_text(f"{money:04d}", font, gold, box_xu, center=True)

            box_time = pygame.Rect(rect.x + pad * 2 + w + int(w * 0.45) - 10, rect.y + pad + int(h * 0.45) + 5, int(w * 0.55), int(h * 0.55))
            self._draw_fitted_text(f"{minutes:02d}:{seconds:02d}", font, gold, box_time, center=True)

            box_del = pygame.Rect(rect.x + pad + int(w * 0.45) - 12, rect.y + pad * 2 + h + int(h * 0.45) - 8, int(w * 0.55), int(h * 0.55))
            self._draw_fitted_text(f"{orders:02d}", font, gold, box_del, center=True)

            box_combo = pygame.Rect(rect.x + pad * 2 + w + int(w * 0.45) - 12, rect.y + pad * 2 + h + int(h * 0.45) - 8, int(w * 0.55), int(h * 0.55))
            self._draw_fitted_text(f"x{combo}", font, gold, box_combo, center=True)
            return

        pad = 8
        w = (rect.width - pad * 3) // 2
        h = (rect.height - pad * 3) // 2
        self._draw_stats_item(
            pygame.Rect(rect.x + pad, rect.y + pad, w, h),
            "XU",
            f"{money:04d}",
            getattr(self, "icons", {}).get("coin", None) or getattr(self, "icons", {}).get("money", None),
        )
        self._draw_stats_item(
            pygame.Rect(rect.x + pad * 2 + w, rect.y + pad, w, h),
            "THOI GIAN",
            f"{minutes:02d}:{seconds:02d}",
            getattr(self, "icons", {}).get("clock", None),
        )
        self._draw_stats_item(
            pygame.Rect(rect.x + pad, rect.y + pad * 2 + h, w, h),
            "DA GIAO",
            f"{orders:02d}",
            getattr(self, "icons", {}).get("box", None),
        )
        self._draw_stats_item(
            pygame.Rect(rect.x + pad * 2 + w, rect.y + pad * 2 + h, w, h),
            "COMBO",
            f"x{combo}",
            getattr(self, "icons", {}).get("star", None),
        )

    def _draw_stats_item(self, rect: pygame.Rect, title: str, value: str, icon_img) -> None:
        pygame.draw.rect(self.screen, (24, 52, 78), rect, border_radius=8)
        pygame.draw.rect(self.screen, (74, 115, 145), rect, width=1, border_radius=8)

        if icon_img:
            icon_size = 40
            icon_rect = pygame.Rect(rect.x + 10, rect.centery - icon_size // 2, icon_size, icon_size)
            scaled_icon = pygame.transform.smoothscale(icon_img, (icon_size, icon_size))
            self.screen.blit(scaled_icon, icon_rect)

        title_surf = self.font_tiny.render(title, True, (190, 205, 215))
        value_surf = self.font_mid.render(value, True, (255, 255, 255))
        self.screen.blit(title_surf, (rect.right - 10 - title_surf.get_width(), rect.y + 8))
        self.screen.blit(value_surf, (rect.right - 10 - value_surf.get_width(), rect.bottom - 8 - value_surf.get_height()))
