from __future__ import annotations

from src.core.constants import SCREEN_WIDTH
from src.core.game_state import GameState


class StateUpdaterMixin:
    """Dispatch each frame to the active gameplay mode."""

    def _update(self, dt: float) -> None:
        if self.state == GameState.MENU:
            self.menu_cloud_offset = (
                getattr(self, "menu_cloud_offset", 0.0) + dt * 28
            ) % (SCREEN_WIDTH + 360)
            return

        if self.state not in (GameState.PLAYING, GameState.SIMULATION):
            return

        self._update_smooth_entities(dt)
        self.elapsed_time += dt

        if self.state == GameState.PLAYING:
            self._update_play_mode(dt)
        else:
            self._update_auto_mode(dt)
