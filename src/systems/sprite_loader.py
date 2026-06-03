from pathlib import Path
from typing import Optional, Tuple

import pygame


class SpriteLoader:
    """
    Load ảnh game an toàn.

    Nếu thiếu file ảnh:
    - Game không crash.
    - Tự vẽ ô màu fallback có chữ.
    """

    def __init__(self, tile_size: int = 32):
        self.tile_size = tile_size
        self.cache: dict[tuple[str, int, int], pygame.Surface] = {}

    def load_image(
        self,
        path: Optional[Path],
        size: Optional[Tuple[int, int]] = None,
        fallback_color: Tuple[int, int, int] = (255, 0, 255),
        fallback_text: str = "?",
    ) -> pygame.Surface:
        if size is None:
            size = (self.tile_size, self.tile_size)

        if path is None or not Path(path).exists():
            return self._fallback(size, fallback_color, fallback_text)

        key = (str(path), size[0], size[1])

        if key in self.cache:
            return self.cache[key]

        try:
            image = pygame.image.load(str(path)).convert_alpha()
            image = pygame.transform.smoothscale(image, size)
            self.cache[key] = image
            return image
        except Exception:
            return self._fallback(size, fallback_color, fallback_text)

    def load_directional_set(
        self,
        paths: dict,
        size: Optional[Tuple[int, int]] = None,
        fallback_color: Tuple[int, int, int] = (80, 130, 220),
        label: str = "P",
    ) -> dict[str, pygame.Surface]:
        """
        Trả về bộ sprite 4 hướng:
        - left
        - right
        - up
        - down
        - idle

        Nếu chỉ có ảnh ngang Shipper.png thì tự flip trái/phải.
        """
        side = self.load_image(
            paths.get("side"),
            size=size,
            fallback_color=fallback_color,
            fallback_text=label,
        )

        front = self.load_image(
            paths.get("front"),
            size=size,
            fallback_color=fallback_color,
            fallback_text=label,
        )

        back = self.load_image(
            paths.get("back"),
            size=size,
            fallback_color=fallback_color,
            fallback_text=label,
        )

        return {
            "left": pygame.transform.flip(side, True, False),
            "right": side,
            "down": front,
            "up": back,
            "idle": front,
        }

    def _fallback(
        self,
        size: Tuple[int, int],
        color: Tuple[int, int, int],
        text: str,
    ) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surface, color, surface.get_rect(), border_radius=6)
        pygame.draw.rect(surface, (20, 20, 20), surface.get_rect(), width=2, border_radius=6)

        if pygame.font.get_init():
            font_size = max(12, size[1] // 2)
            font = pygame.font.SysFont("arial", font_size, bold=True)
            txt = font.render(str(text), True, (255, 255, 255))
            rect = txt.get_rect(center=(size[0] // 2, size[1] // 2))
            surface.blit(txt, rect)

        return surface
