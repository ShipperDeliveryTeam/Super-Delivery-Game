from typing import Dict, Tuple

import pygame


class DirectionalShipper:
    """
    Entity shipper.
    Logic đi theo grid, render dùng render_x/render_y để di chuyển mượt.
    """

    def __init__(
        self,
        name: str,
        grid_pos: Tuple[int, int],
        sprites: Dict[str, pygame.Surface],
        tile_size: int = 32,
    ):
        self.name = name

        self.grid_x = int(grid_pos[0])
        self.grid_y = int(grid_pos[1])

        self.render_x = float(self.grid_x)
        self.render_y = float(self.grid_y)

        self.sprites = sprites
        self.tile_size = tile_size
        self.direction = "down"

        self.money = 0
        self.orders = 0
        self.algorithm = "ASTAR"

        self.smooth_speed = 12.0

    @property
    def grid_pos(self) -> Tuple[int, int]:
        return self.grid_x, self.grid_y

    @property
    def render_pos(self) -> Tuple[float, float]:
        return self.render_x, self.render_y

    def set_grid_pos(self, pos: Tuple[int, int]) -> None:
        self.grid_x = int(pos[0])
        self.grid_y = int(pos[1])
        self.render_x = float(self.grid_x)
        self.render_y = float(self.grid_y)

    def set_direction_from_delta(self, dx: int, dy: int) -> None:
        if dx < 0:
            self.direction = "left"
        elif dx > 0:
            self.direction = "right"
        elif dy < 0:
            self.direction = "up"
        elif dy > 0:
            self.direction = "down"

    def move_grid(self, dx: int, dy: int, max_cols: int, max_rows: int, min_y: int = 0) -> None:
        self.set_direction_from_delta(dx, dy)

        self.grid_x = max(0, min(max_cols - 1, self.grid_x + dx))
        self.grid_y = max(min_y, min(max_rows - 1, self.grid_y + dy))

    def update_smooth(self, dt: float) -> None:
        target_x = float(self.grid_x)
        target_y = float(self.grid_y)

        self.render_x = self._approach(self.render_x, target_x, self.smooth_speed * dt)
        self.render_y = self._approach(self.render_y, target_y, self.smooth_speed * dt)

    @staticmethod
    def _approach(current: float, target: float, max_delta: float) -> float:
        if current < target:
            return min(current + max_delta, target)
        if current > target:
            return max(current - max_delta, target)
        return current
