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

    def test_player_can_select_and_confirm_delivery_orders(self):
        manager = GameManager(GameSettings(), debug=True)
        manager._start_play_mode()

        self.assertEqual(len(manager.available_player_tasks), 5)
        self.assertTrue(manager._select_player_order(0))
        self.assertTrue(manager._select_player_order(1))
        self.assertTrue(manager._select_player_order(2))
        self.assertEqual(len(manager.player_tasks), 3)
        self.assertIsNone(manager.player_task)
        task = manager.player_tasks[0]
        reward = task.reward

        manager.player.set_grid_pos(task.store_pos)
        manager._handle_player_task_at_current_pos()
        self.assertTrue(task.picked_up)

        manager.player.set_grid_pos(task.house_pos)
        manager._handle_player_task_at_current_pos()
        self.assertFalse(manager.delivery_confirmation_open)
        manager._draw()
        self.assertIsNotNone(manager._delivery_action_rect)
        manager._handle_gameplay_mouse_click(manager._delivery_action_rect.center)
        self.assertTrue(manager.delivery_confirmation_open)

        manager.delivery_confirmation_open = False
        manager._has_letterbox_side_rails = lambda: True
        self.assertTrue(manager._handle_letterbox_gameplay_mouse_click(manager._delivery_action_rect.center))
        self.assertTrue(manager.delivery_confirmation_open)

        self.assertTrue(manager._select_player_order(0))
        manager.player_task = task

        manager.delivery_checkbox_checked = True
        self.assertTrue(manager._confirm_player_delivery())
        self.assertEqual(manager.player.money, reward)
        self.assertEqual(manager.player.orders, 1)
        self.assertEqual(len(manager.available_player_tasks), 5)

    def test_player_can_pick_up_multiple_accepted_orders_before_delivery(self):
        manager = GameManager(GameSettings(), debug=True)
        manager._start_play_mode()

        self.assertTrue(manager._select_player_order(0))
        self.assertTrue(manager._select_player_order(1))
        first, second = manager.player_tasks[:2]

        manager.player.set_grid_pos(first.store_pos)
        manager._handle_player_task_at_current_pos()
        self.assertTrue(first.picked_up)
        self.assertFalse(second.picked_up)
        self.assertIs(manager.player_task, first)

        self.assertTrue(manager._select_player_order(1))
        manager._refresh_player_path_hint()
        self.assertTrue(manager.player_path_hint)
        self.assertEqual(manager.player_path_hint[-1], second.store_pos)

        manager.player.set_grid_pos(second.store_pos)
        manager._handle_player_task_at_current_pos()
        self.assertTrue(second.picked_up)
        self.assertIs(manager.player_task, second)

    def test_player_wins_at_target_revenue_without_changing_map(self):
        settings = GameSettings()
        settings.set_map(1)
        manager = GameManager(settings, debug=True)
        manager._start_play_mode()

        manager.player.money = settings.target_revenue
        manager._update_play_mode(0.1)

        self.assertEqual(settings.target_revenue, 1500)
        self.assertEqual(settings.selected_map_id, 1)
        self.assertEqual(manager.state, GameState.WIN)
        self.assertEqual(manager.winner_name, "Player")


if __name__ == "__main__":
    unittest.main()
