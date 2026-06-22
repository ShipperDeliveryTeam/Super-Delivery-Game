import unittest

from src.ai.game_pathfinder import GamePathfinder
from src.gameplay.roundabout_geometry import build_roundabout_curve, curve_point


RING = (
    (22, 14), (23, 14), (24, 14), (25, 15), (26, 16),
    (26, 17), (25, 18), (24, 19), (23, 19), (22, 18),
    (21, 17), (21, 16), (21, 15),
)
CONNECTIONS = (
    ((23, 13), (23, 14)),
    ((23, 19), (23, 20)),
    ((20, 15), (21, 16)),
    ((20, 18), (21, 17)),
    ((26, 16), (27, 15)),
    ((26, 17), (27, 18)),
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
        self.assertTrue(self.pathfinder.can_step((23, 19), (24, 19)))
        self.assertFalse(self.pathfinder.can_step((23, 19), (22, 18)))

    def test_ring_can_only_be_entered_through_a_gate(self):
        self.assertTrue(self.pathfinder.can_step((23, 20), (23, 19)))
        self.assertFalse(self.pathfinder.can_step((22, 19), (22, 18)))

    def test_south_gate_blends_into_ring_tangent(self):
        curve = build_roundabout_curve(
            (23, 20),
            (23, 19),
            (23.5, 16.5),
            RING,
            CONNECTIONS,
        )
        near_end = curve_point(curve, 0.98)
        end = curve_point(curve, 1.0)
        self.assertGreater(end[0], near_end[0])
        self.assertAlmostEqual(end[1], near_end[1], delta=0.04)


if __name__ == "__main__":
    unittest.main()
