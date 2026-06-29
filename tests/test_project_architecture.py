import ast
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"


class ProjectArchitectureTests(unittest.TestCase):
    def test_game_manager_is_a_small_composition_root(self):
        path = SRC_ROOT / "core" / "game_manager.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        game_manager = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "GameManager"
        )
        method_names = {
            node.name for node in game_manager.body if isinstance(node, ast.FunctionDef)
        }

        self.assertEqual(method_names, {"__init__", "run"})
        self.assertLessEqual(len(source.splitlines()), 200)

    def test_extracted_modules_have_no_duplicate_methods(self):
        module_paths = [
            SRC_ROOT / "core" / "command_handler.py",
            SRC_ROOT / "core" / "state_updater.py",
            SRC_ROOT / "maps" / "map_manager.py",
            SRC_ROOT / "systems" / "asset_manager.py",
            SRC_ROOT / "gameplay" / "delivery_manager.py",
            SRC_ROOT / "gameplay" / "game_flow.py",
            SRC_ROOT / "gameplay" / "gameplay_controller.py",
            SRC_ROOT / "gameplay" / "movement_service.py",
            SRC_ROOT / "gameplay" / "auto" / "controller.py",
            SRC_ROOT / "gameplay" / "play" / "controller.py",
            SRC_ROOT / "ui" / "button.py",
            SRC_ROOT / "ui" / "game_renderer.py",
            SRC_ROOT / "ui" / "hud.py",
            SRC_ROOT / "ui" / "menu.py",
            SRC_ROOT / "ui" / "pause_menu.py",
            SRC_ROOT / "ui" / "popup.py",
            SRC_ROOT / "ui" / "result_screen.py",
            SRC_ROOT / "ui" / "text_renderer.py",
            SRC_ROOT / "ui" / "viewport.py",
        ]

        for path in module_paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                class_node = next(
                    node for node in tree.body if isinstance(node, ast.ClassDef)
                )
                method_names = [
                    node.name
                    for node in class_node.body
                    if isinstance(node, ast.FunctionDef)
                ]
                self.assertEqual(len(method_names), len(set(method_names)))
                self.assertLessEqual(
                    len(path.read_text(encoding="utf-8").splitlines()), 400
                )

    def test_play_and_auto_are_separate_gameplay_modules(self):
        manager_source = (SRC_ROOT / "core" / "game_manager.py").read_text(
            encoding="utf-8"
        )
        play_source = (
            SRC_ROOT / "gameplay" / "play" / "controller.py"
        ).read_text(encoding="utf-8")
        auto_source = (
            SRC_ROOT / "gameplay" / "auto" / "controller.py"
        ).read_text(encoding="utf-8")

        self.assertIn("PlayModeMixin", manager_source)
        self.assertIn("AutoModeMixin", manager_source)
        self.assertIn("_update_play_mode", play_source)
        self.assertNotIn("def _update_auto_mode", play_source)
        self.assertIn("_update_auto_mode", auto_source)
        self.assertNotIn("def _update_play_mode", auto_source)

    def test_replaced_legacy_modules_are_removed(self):
        replaced_paths = [
            SRC_ROOT / "gameplay" / "player_controller.py",
            SRC_ROOT / "gameplay" / "npc_controller.py",
            SRC_ROOT / "algorithms",
            SRC_ROOT / "scripts",
        ]

        for path in replaced_paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                self.assertFalse(path.exists())

    def test_future_extension_points_are_preserved(self):
        extension_paths = [
            SRC_ROOT / "ai" / "pathfinding",
            SRC_ROOT / "ai" / "local_search",
            SRC_ROOT / "ai" / "reinforcement",
            SRC_ROOT / "entities" / "player.py",
            SRC_ROOT / "entities" / "npc_shipper.py",
            SRC_ROOT / "gameplay" / "level_manager.py",
            SRC_ROOT / "gameplay" / "order_manager.py",
            SRC_ROOT / "maps" / "collision.py",
            SRC_ROOT / "maps" / "grid_map.py",
            SRC_ROOT / "systems" / "animation.py",
            SRC_ROOT / "systems" / "camera.py",
            SRC_ROOT / "systems" / "sound_manager.py",
        ]

        for path in extension_paths:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
