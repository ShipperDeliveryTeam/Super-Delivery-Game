from __future__ import annotations

import pygame

from src.core.constants import SCREEN_HEIGHT, SCREEN_WIDTH


class ViewportMixin:
    """Present the fixed-size game world inside any window using letterboxing."""

    def _draw(self) -> None:
        world_size = (SCREEN_WIDTH, SCREEN_HEIGHT)

        if not hasattr(self, "_letterbox_world_surface"):
            self._letterbox_world_surface = pygame.Surface(world_size).convert()

        display_screen = self.screen
        self.screen = self._letterbox_world_surface
        self._letterbox_world_surface.fill((0, 0, 0))

        super()._draw()

        self.screen = display_screen
        self._present_letterbox(self._letterbox_world_surface)

    def _present_letterbox(self, world_surface: pygame.Surface) -> None:
        display = pygame.display.get_surface()
        if display is None:
            return

        win_w, win_h = display.get_size()
        world_w, world_h = world_surface.get_size()
        scale = min(win_w / world_w, win_h / world_h)
        scaled_w = max(1, int(world_w * scale))
        scaled_h = max(1, int(world_h * scale))
        offset_x = (win_w - scaled_w) // 2
        offset_y = (win_h - scaled_h) // 2

        self._viewport_scale = scale
        self._viewport_offset = (offset_x, offset_y)

        display.fill((0, 0, 0))
        scaled = pygame.transform.smoothscale(world_surface, (scaled_w, scaled_h))
        display.blit(scaled, (offset_x, offset_y))
        pygame.display.flip()

    def _handle_mouse_click(self, pos: tuple[int, int]) -> None:
        scale = getattr(self, "_viewport_scale", 1.0)
        offset_x, offset_y = getattr(self, "_viewport_offset", (0, 0))

        if scale > 0:
            pos = (
                int((pos[0] - offset_x) / scale),
                int((pos[1] - offset_y) / scale),
            )

        super()._handle_mouse_click(pos)

