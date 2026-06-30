from __future__ import annotations

from typing import Tuple

import pygame


class TextRendererMixin:
    def _draw_text(self, text: str, font: pygame.font.Font, color: Tuple[int, int, int], x: int, y: int, center: bool = False) -> None:
        surface = font.render(str(text), True, color)
        rect = surface.get_rect()

        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)

        self.screen.blit(surface, rect)
