import os
import unittest


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import game  # Adds the optional project-local dependency directory to sys.path.
# pyrefly: ignore [missing-import]
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
        self.assertIn(task, manager.available_player_tasks)
        manager._draw_player_offer_markers(0)
        marker_stores = [
            offer.store_pos
            for offer in manager.available_player_tasks
            if not getattr(offer, "picked_up", False)
        ]
        self.assertEqual(len(manager._offer_marker_rects), len(marker_stores))
        self.assertNotIn(task.store_pos, marker_stores)

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

    def test_player_loses_carried_order_and_coins_when_delivery_timer_expires(self):
        manager = GameManager(GameSettings(), debug=True)
        manager._start_play_mode()

        manager.player.money = 100
        self.assertTrue(manager._select_player_order(0))
        task = manager.player_tasks[0]
        task.reward = 200
        task.delivery_time_limit = 5.0

        manager.player.set_grid_pos(task.store_pos)
        manager._handle_player_task_at_current_pos()
        self.assertTrue(task.picked_up)
        self.assertIsNotNone(task.delivery_started_at)

        manager.elapsed_time = task.delivery_started_at + 5.1
        manager._update_player_delivery_timeouts()

        self.assertTrue(task.lost)
        self.assertNotIn(task, manager.player_tasks)
        self.assertNotIn(task, manager.available_player_tasks)
        self.assertEqual(manager.player.money, 50)
        self.assertEqual(len(manager.available_player_tasks), 5)

    def test_delivery_timer_stays_fixed_until_pickup_then_counts_down(self):
        manager = GameManager(GameSettings(), debug=True)
        manager._start_play_mode()

        self.assertTrue(manager._select_player_order(0))
        task = manager.player_tasks[0]
        task.delivery_time_limit = 125.0

        start_display = manager._delivery_display_seconds(task)
        manager.elapsed_time += 30.0
        self.assertEqual(manager._delivery_display_seconds(task), start_display)

        manager.player.set_grid_pos(task.store_pos)
        manager._handle_player_task_at_current_pos()
        self.assertTrue(task.picked_up)
        self.assertEqual(manager._delivery_display_seconds(task), start_display)

        manager.elapsed_time += 25.0
        self.assertEqual(manager._delivery_display_seconds(task), start_display - 25.0)

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

    def test_player_order_offers_use_unique_random_shops(self):
        manager = GameManager(GameSettings(), debug=True)
        manager._start_play_mode()

        stores = [task.store_pos for task in manager.available_player_tasks]
        self.assertEqual(len(stores), 5)
        self.assertEqual(len(set(stores)), len(stores))

        manager._replenish_player_order_offers()
        stores = [task.store_pos for task in manager.available_player_tasks]
        self.assertEqual(len(set(stores)), len(stores))

    def test_npc_picks_up_immediately_then_waits_and_removes_shop_offer(self):
        manager = GameManager(GameSettings(), debug=True)
        manager._start_play_mode()
        npc = manager.npc_shippers[0]
        task = manager.available_player_tasks[0]
        npc.set_grid_pos(task.store_pos)
        manager.npc_tasks[npc.name] = task
        manager.npc_paths[npc.name] = []

        manager._update_npcs()

        self.assertTrue(task.picked_up)
        self.assertEqual(task.stolen_by, npc.name)
        self.assertNotIn(task, manager.available_player_tasks)
        self.assertGreater(manager.npc_wait_until.get(npc.name, 0), manager.elapsed_time)
        self.assertEqual(manager.npc_wait_action.get(npc.name), "pickup")


if __name__ == "__main__":
    unittest.main()
