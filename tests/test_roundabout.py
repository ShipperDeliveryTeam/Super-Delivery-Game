import unittest
from pathlib import Path
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from src.ai.game_pathfinder import GamePathfinder
from src.gameplay.roundabout_geometry import build_roundabout_curve, curve_point
from src.maps.tmx_loader import TmxMapLoader


RING = (
    (22, 14), (23, 14), (24, 14), (25, 15), (25, 16),
    (25, 17), (24, 18), (23, 18), (22, 18), (21, 17),
    (21, 16), (21, 15),
)
CONNECTIONS = (
    ((23, 13), (23, 14)),
    ((23, 18), (23, 19)),
    ((20, 16), (21, 16)),
    ((20, 18), (21, 17)),
    ((25, 16), (26, 16)),
    ((25, 17), (26, 18)),
)


class RoundaboutPathfinderTests(unittest.TestCase):
    def setUp(self):
        self.pathfinder = GamePathfinder(
            48,
            32,
            allow_diagonal=True,
            roundabout_ring=RING,
            roundabout_connections=CONNECTIONS,
        )

    def test_ring_only_allows_counter_clockwise_flow(self):
        self.assertTrue(self.pathfinder.can_step((23, 18), (24, 18)))
        self.assertFalse(self.pathfinder.can_step((23, 18), (22, 18)))

    def test_ring_can_only_be_entered_through_a_gate(self):
        self.assertTrue(self.pathfinder.can_step((23, 19), (23, 18)))
        self.assertFalse(self.pathfinder.can_step((22, 19), (22, 18)))

    def test_vertical_gates_stay_centered_in_both_directions(self):
        for start, end in (
            ((23, 13), (23, 14)),
            ((23, 14), (23, 13)),
            ((23, 18), (23, 19)),
            ((23, 19), (23, 18)),
        ):
            curve = build_roundabout_curve(
                start, end, (23.5, 16.0), RING, CONNECTIONS
            )

            for sample in range(11):
                x, _ = curve_point(curve, sample / 10.0)
                self.assertAlmostEqual(x, 23.0)

    def test_horizontal_gates_stay_level_in_both_directions(self):
        for start, end in (
            ((20, 16), (21, 16)),
            ((21, 16), (20, 16)),
            ((25, 16), (26, 16)),
            ((26, 16), (25, 16)),
        ):
            curve = build_roundabout_curve(
                start, end, (23.5, 16.0), RING, CONNECTIONS
            )

            for sample in range(11):
                _, y = curve_point(curve, sample / 10.0)
                self.assertAlmostEqual(y, 16.0)

    def test_map2_collision_keeps_the_full_ring_and_gates_open(self):
        pygame.init()
        pygame.display.set_mode((1, 1))
        self.addCleanup(pygame.quit)

        map_path = Path(__file__).resolve().parents[1] / "maps" / "map2" / "map2.tmx"
        data = TmxMapLoader().load(map_path)
        blocked = TmxMapLoader().blocked_positions(data.grid)

        self.assertFalse(set(RING) & blocked)
        self.assertFalse({point for edge in CONNECTIONS for point in edge} & blocked)


if __name__ == "__main__":
    unittest.main()
