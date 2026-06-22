import os
import unittest


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import game  # Adds the optional project-local dependency directory to sys.path.
import pygame

from src.core.game_manager import GameManager
from src.core.game_state import GameState
from src.core.settings import GameSettings


class GameSmokeTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_primary_screens_initialize_update_and_draw(self):
        manager = GameManager(GameSettings(), debug=True)

        manager._draw()
        manager._start_play_mode()
        manager._update(0.1)
        manager._draw()

        manager.state = GameState.PAUSED
        manager._draw()

        manager._start_simulation_mode()
        manager._update(0.1)
        manager._draw()

        manager.winner_name = "Player"
        manager.state = GameState.WIN
        manager._draw()


if __name__ == "__main__":
    unittest.main()
