from __future__ import annotations

import pygame

from src.core.constants import SCREEN_HEIGHT, SCREEN_WIDTH


class PauseMenuMixin:
    def _draw_pause(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        self._draw_text("PAUSED", self.font_big, (255, 255, 255), SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40, center=True)
        self._draw_text("ESC or ENTER to continue", self.font_mid, (255, 255, 255), SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, center=True)
