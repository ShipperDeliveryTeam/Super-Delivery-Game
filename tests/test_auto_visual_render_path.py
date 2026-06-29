from types import SimpleNamespace

from src.gameplay.auto.controller import AutoModeMixin


class FakeAutoMapData:
    def __init__(self, blocked=()):
        self.map_id = 2
        self.width = 3
        self.height = 2
        self.blocked = {tuple(pos) for pos in blocked}

    def in_bounds(self, pos):
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, pos):
        return self.in_bounds(pos) and tuple(pos) not in self.blocked

    def movement_cost(self, pos):
        return 1.0 if self.is_walkable(pos) else float("inf")


class AutoVisualRenderHarness(AutoModeMixin):
    def __init__(self, traps=()):
        self.auto_visual_map_data = FakeAutoMapData()
        self.auto_visual_hidden_traps = {tuple(pos) for pos in traps}

    def _auto_visual_keep_diagonal_edge(self, start, end):
        return False


def test_diagonal_render_expansion_avoids_trap_middle_cell():
    harness = AutoVisualRenderHarness(traps={(1, 0)})

    path = harness._expand_auto_visual_render_path([(0, 0), (1, 1)])

    assert path == [(0, 0), (0, 1), (1, 1)]


def test_diagonal_render_expansion_keeps_diagonal_when_both_middle_cells_are_traps():
    harness = AutoVisualRenderHarness(traps={(1, 0), (0, 1)})

    path = harness._expand_auto_visual_render_path([(0, 0), (1, 1)])

    assert path == [(0, 0), (1, 1)]


def test_replan_avoids_revealed_trap_in_remaining_path():
    harness = AutoVisualRenderHarness()
    npc = SimpleNamespace(name="ASTAR")
    path = [(1, 0), (2, 0)]

    harness.auto_visual_revealed_traps = {(1, 0)}
    harness.auto_visual_targets = {"ASTAR": [("house", (2, 0))]}
    harness.npc_paths = {"ASTAR": path}

    replanned = harness._auto_visual_replan_around_revealed_traps(npc, (0, 0), path)

    assert replanned is True
    assert (1, 0) not in harness.npc_paths["ASTAR"]
    assert harness.npc_paths["ASTAR"][-1] == (2, 0)
