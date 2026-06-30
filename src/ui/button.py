from __future__ import annotations

import pygame


class ButtonMixin:
    def _draw_image_button(self, image, rect: pygame.Rect, fallback_text: str, bg_color: tuple[int, int, int]) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)

        scale_rect = rect.copy()
        if hover:
            scale_rect.inflate_ip(8, 8)

        if image:
            img = pygame.transform.smoothscale(image, (scale_rect.width, scale_rect.height))
            self.screen.blit(img, scale_rect)
        else:
            color = tuple(min(255, c + 25) for c in bg_color) if hover else bg_color
            pygame.draw.rect(self.screen, color, scale_rect, border_radius=16)
            pygame.draw.rect(self.screen, (255, 255, 255), scale_rect, width=3, border_radius=16)
            self._draw_text(fallback_text, self.font_mid, (255, 255, 255), scale_rect.centerx, scale_rect.centery, center=True)

    def _draw_simulation_button(self, rect: pygame.Rect) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)

        draw_rect = rect.copy()
        if hover:
            draw_rect.inflate_ip(8, 8)

        if self.ui_simulation_button:
            img = pygame.transform.smoothscale(self.ui_simulation_button, (draw_rect.width, draw_rect.height))
            self.screen.blit(img, draw_rect)
        else:
            color = (78, 220, 48) if hover else (55, 190, 70)
            pygame.draw.rect(self.screen, color, draw_rect, border_radius=18)
            pygame.draw.rect(self.screen, (20, 35, 24), draw_rect, width=5, border_radius=18)
            self._draw_text("AUTO", self.font_big, (255, 255, 255), draw_rect.centerx, draw_rect.centery, center=True)

    def _draw_small_round_button(self, rect: pygame.Rect, image, fallback_text: str, bg_color: tuple[int, int, int]) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)

        draw_rect = rect.copy()
        if hover:
            draw_rect.inflate_ip(5, 5)

        if image:
            img = pygame.transform.smoothscale(image, (draw_rect.width, draw_rect.height))
            self.screen.blit(img, draw_rect)
        else:
            color = tuple(min(255, c + 30) for c in bg_color) if hover else bg_color
            pygame.draw.ellipse(self.screen, color, draw_rect)
            pygame.draw.ellipse(self.screen, (255, 255, 255), draw_rect, width=2)
            self._draw_text(fallback_text, self.font_small, (255, 255, 255), draw_rect.centerx, draw_rect.centery, center=True)

    def _draw_text_button(self, rect: pygame.Rect, text: str, bg_color: tuple[int, int, int]) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        color = tuple(min(255, c + 25) for c in bg_color) if hover else bg_color
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, width=2, border_radius=10)
        self._draw_text(text, self.font_small, (255, 255, 255), rect.centerx, rect.centery, center=True)
