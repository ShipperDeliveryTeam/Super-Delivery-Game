from __future__ import annotations

import math
from typing import Any

import pygame


class DirectionalShipper:
    """
    Smooth grid shipper for Super Delivery Game.

    Fixes NPC stutter:
    - If a new adjacent step is requested while the shipper is still moving,
      it is queued instead of being rejected.
    - When the shipper reaches the current target cell, it immediately starts
      the queued next step.
    - Normal movement still only allows adjacent grid cells.
    """

    def __init__(self, name="Shipper", grid_pos=(0, 0), sprites=None, *args, **kwargs):
        self.name = name
        self.sprites = sprites or {}

        self.tile_size = int(kwargs.get("tile_size", 32))
        self.color = kwargs.get("color", (255, 200, 40))
        self.algorithm = kwargs.get("algorithm", "")
        self.speed_px = float(kwargs.get("speed", kwargs.get("speed_px", 118.0)))

        # Compatibility with old constructor call styles.
        for arg in args:
            if isinstance(arg, tuple) and len(arg) >= 3:
                self.color = arg[:3]
            elif isinstance(arg, str):
                self.algorithm = arg
            elif isinstance(arg, (int, float)):
                if int(arg) >= 16:
                    self.tile_size = int(arg)
                else:
                    self.speed_px = float(arg)

        # Keep movement readable but not sluggish.
        self.speed_px = max(70.0, min(float(self.speed_px), 150.0))

        self._grid_pos = (int(grid_pos[0]), int(grid_pos[1]))
        self.target_grid_pos = self._grid_pos
        self.queued_grid_pos = None

        self.pixel_x = float(self._grid_pos[0] * self.tile_size)
        self.pixel_y = float(self._grid_pos[1] * self.tile_size)

        self.direction = "down"
        self.is_moving = False
        self.allow_diagonal = bool(kwargs.get("allow_diagonal", False))

        self.money = int(kwargs.get("money", 0))
        self.orders = int(kwargs.get("orders", 0))
        self.expanded_nodes = int(kwargs.get("expanded_nodes", 0))

    # =====================================================
    # Position properties
    # =====================================================
    @property
    def grid_pos(self):
        return self._grid_pos

    @grid_pos.setter
    def grid_pos(self, value):
        self.set_grid_position(value)

    @property
    def grid_x(self):
        return self._grid_pos[0]

    @property
    def grid_y(self):
        return self._grid_pos[1]

    @property
    def render_pos(self):
        return (self.pixel_x / self.tile_size, self.pixel_y / self.tile_size)

    @property
    def center_render_pos(self):
        return (
            self.pixel_x / self.tile_size + 0.5,
            self.pixel_y / self.tile_size + 0.5,
        )

    @property
    def pixel_pos(self):
        return (self.pixel_x, self.pixel_y)

    @property
    def center_pixel_pos(self):
        return (
            self.pixel_x + self.tile_size / 2,
            self.pixel_y + self.tile_size / 2,
        )

    @property
    def x(self):
        return self.pixel_x

    @property
    def y(self):
        return self.pixel_y

    # =====================================================
    # Direction helpers
    # =====================================================
    def set_direction_from_delta(self, dx, dy):
        dx = int(dx)
        dy = int(dy)

        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"
        elif dy > 0:
            self.direction = "down"
        elif dy < 0:
            self.direction = "up"

    def _set_direction(self, dx, dy):
        self.set_direction_from_delta(dx, dy)

    # =====================================================
    # Position setters
    # =====================================================
    def set_grid_position(self, pos):
        pos = (int(pos[0]), int(pos[1]))
        self._grid_pos = pos
        self.target_grid_pos = pos
        self.queued_grid_pos = None
        self.pixel_x = float(pos[0] * self.tile_size)
        self.pixel_y = float(pos[1] * self.tile_size)
        self.is_moving = False

    def set_grid_pos(self, pos):
        self.set_grid_position(pos)

    def teleport_to_grid(self, pos):
        self.set_grid_position(pos)

    def snap_to_grid(self):
        self.set_grid_position(self._grid_pos)

    def stop(self):
        self.is_moving = False
        self.target_grid_pos = self._grid_pos
        self.queued_grid_pos = None
        self.pixel_x = float(self._grid_pos[0] * self.tile_size)
        self.pixel_y = float(self._grid_pos[1] * self.tile_size)

    # =====================================================
    # Movement
    # =====================================================
    def _is_adjacent(self, a, b):
        dx = abs(int(a[0]) - int(b[0]))
        dy = abs(int(a[1]) - int(b[1]))

        if self.allow_diagonal:
            return max(dx, dy) == 1 and dx + dy > 0

        return dx + dy == 1

    def move_grid(self, dx, dy, max_cols, max_rows, min_y=0, allow_diagonal=None):
        dx = int(dx)
        dy = int(dy)
        allow_diagonal = self.allow_diagonal if allow_diagonal is None else bool(allow_diagonal)

        if allow_diagonal:
            if max(abs(dx), abs(dy)) != 1 or (dx == 0 and dy == 0):
                return False
        elif abs(dx) + abs(dy) != 1:
            return False

        # If currently moving, queue from current target.
        base = self.target_grid_pos if self.is_moving else self._grid_pos

        nx = max(0, min(int(max_cols) - 1, base[0] + dx))
        ny = max(int(min_y), min(int(max_rows) - 1, base[1] + dy))

        if (nx, ny) == base:
            return True

        return self.move_to_grid((nx, ny), allow_diagonal=allow_diagonal)

    def move_to_grid(self, pos, allow_diagonal=None):
        """
        Move/queue one adjacent grid cell.
        """
        pos = (int(pos[0]), int(pos[1]))
        allow_diagonal = self.allow_diagonal if allow_diagonal is None else bool(allow_diagonal)

        # Current cell: not an error. Return True so path code can consume it.
        if pos == self._grid_pos and not self.is_moving:
            return True

        if self.is_moving:
            # Already heading there.
            if pos == self.target_grid_pos:
                return True

            # Queue next step if it is adjacent to the current target.
            old_allow_diagonal = self.allow_diagonal
            self.allow_diagonal = allow_diagonal
            is_adjacent_to_target = self._is_adjacent(self.target_grid_pos, pos)
            self.allow_diagonal = old_allow_diagonal

            if is_adjacent_to_target:
                self.queued_grid_pos = pos
                return True

            # If path code sends current cell while moving, accept but do nothing.
            if pos == self._grid_pos:
                return True

            return False

        dx = pos[0] - self._grid_pos[0]
        dy = pos[1] - self._grid_pos[1]

        if allow_diagonal:
            is_valid_step = max(abs(dx), abs(dy)) == 1 and abs(dx) + abs(dy) > 0
        else:
            is_valid_step = abs(dx) + abs(dy) == 1

        if not is_valid_step:
            return False

        self.set_direction_from_delta(dx, dy)
        self.target_grid_pos = pos
        self.is_moving = True
        return True

    def move_to(self, pos):
        return self.move_to_grid(pos)

    def start_move_to(self, pos):
        return self.move_to_grid(pos)

    def _begin_queued_move_if_any(self):
        if self.queued_grid_pos is None:
            return False

        next_pos = self.queued_grid_pos
        self.queued_grid_pos = None

        if not self._is_adjacent(self._grid_pos, next_pos):
            return False

        dx = next_pos[0] - self._grid_pos[0]
        dy = next_pos[1] - self._grid_pos[1]

        self.set_direction_from_delta(dx, dy)
        self.target_grid_pos = next_pos
        self.is_moving = True
        return True

    def update(self, dt):
        if not self.is_moving:
            return

        target_x = self.target_grid_pos[0] * self.tile_size
        target_y = self.target_grid_pos[1] * self.tile_size

        dx = target_x - self.pixel_x
        dy = target_y - self.pixel_y
        dist = math.hypot(dx, dy)

        step = self.speed_px * float(dt)

        if dist <= step or dist <= 0.01:
            self.pixel_x = float(target_x)
            self.pixel_y = float(target_y)
            self._grid_pos = self.target_grid_pos
            self.is_moving = False

            # Important: continue immediately if a next step was queued.
            self._begin_queued_move_if_any()
            return

        self.pixel_x += dx / dist * step
        self.pixel_y += dy / dist * step

    def update_smooth(self, dt):
        self.update(dt)

    # =====================================================
    # Drawing
    # =====================================================
    def draw(self, screen, *args, **kwargs):
        sprite = self._current_sprite()
        center_x = int(round(self.pixel_x + self.tile_size / 2))
        center_y = int(round(self.pixel_y + self.tile_size / 2))

        if sprite:
            rect = sprite.get_rect(center=(center_x, center_y))
            screen.blit(sprite, rect)
            return

        rect = pygame.Rect(0, 0, self.tile_size - 8, self.tile_size - 8)
        rect.center = (center_x, center_y)
        pygame.draw.ellipse(screen, self.color, rect)
        pygame.draw.ellipse(screen, (20, 20, 20), rect, width=2)

    def _current_sprite(self):
        if self.direction in self.sprites:
            return self.sprites[self.direction]

        if "idle" in self.sprites:
            return self.sprites["idle"]

        if "right" in self.sprites:
            return self.sprites["right"]

        if "down" in self.sprites:
            return self.sprites["down"]

        return None
