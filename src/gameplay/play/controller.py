from __future__ import annotations

# pyrefly: ignore [missing-import]
import pygame

from src.core.game_state import GameState


class PlayModeMixin:
    """Input, movement and update loop for the manual play mode."""

    def _start_play_mode(self) -> None:
        self.simulation_mode = False
        self._reset_game()
        self.state = GameState.PLAYING

    def _update_play_mode(self, dt: float) -> None:
        if not self.auto_player_enabled:
            self._poll_keyboard_movement()

        self.move_timer += dt
        if self.move_timer >= 0.065:
            self.move_timer = 0.0
            if self.auto_player_enabled:
                self._move_player_auto()
            else:
                self._move_player(allow_queue=True)

        self.npc_timer += dt
        if self.npc_timer >= 0.065:
            self.npc_timer = 0.0
            self._update_npcs()

        self.order_timer += dt
        if self.order_timer >= 0.8:
            self.order_timer = 0.0
            self._refresh_player_path_hint()

        if self.player and self.player.money >= self.settings.target_revenue:
            self._finish_game("Player")
            return

        for npc in self.npc_shippers:
            if npc.money >= self.settings.target_revenue:
                self._finish_game(npc.name)
                return

    def _request_player_step(self, dx: int, dy: int) -> None:
        if self.state != GameState.PLAYING or self.auto_player_enabled:
            return

        if self._allow_diagonal_movement():
            self._poll_keyboard_movement()
            return

        self.move_dir = (int(dx), int(dy))
        self._move_player(allow_queue=True)

    def _poll_keyboard_movement(self) -> None:
        keys = pygame.key.get_pressed()

        dx, dy = 0, 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1

        if not self._allow_diagonal_movement() and dx != 0:
            dy = 0

        self.move_dir = (dx, dy)

        if self.player and (dx != 0 or dy != 0):
            self.player.set_direction_from_delta(dx, dy)

    def _handle_player_task_at_current_pos(self) -> None:
        if not self.player:
            return

        if self.player_task is None or self.player_task.delivered:
            self.player_task = self._new_task("Player")

        self.player_task.assign_to("Player")

        picked = self.player_task.try_pickup("Player", self.player.grid_pos)
        delivered = self.player_task.try_deliver("Player", self.player.grid_pos)

        if picked:
            self._refresh_player_path_hint()

        if delivered:
            self.player.money += self.player_task.reward
            self.player.orders += 1
            self.player_task = self._new_task("Player")
            self._refresh_player_path_hint()

        if self.player.grid_pos in self.trap_positions:
            if self._player_last_trap_penalty_pos == self.player.grid_pos:
                return

            self.player.money = max(0, self.player.money - 15)
            self._player_last_trap_penalty_pos = self.player.grid_pos
        else:
            self._player_last_trap_penalty_pos = None

    def _move_player(self, allow_queue: bool = True) -> None:
        if not self.player:
            return

        dx, dy = self.move_dir

        if dx == 0 and dy == 0:
            return

        if not self._try_move_shipper_delta(
            self.player, dx, dy, allow_queue=allow_queue
        ):
            return

        self._handle_player_task_at_current_pos()
