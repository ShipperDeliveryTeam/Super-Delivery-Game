from __future__ import annotations

from src.core.game_state import GameState


class AutoModeMixin:
    """Pathfinding, autonomous movement and simulation updates."""

    def _start_simulation_mode(self) -> None:
        self.simulation_mode = True
        self._reset_game()
        self.auto_player_enabled = False
        self.player_path_hint = []
        self.state = GameState.SIMULATION

    def _update_auto_mode(self, dt: float) -> None:
        self.npc_timer += dt
        if self.npc_timer >= 0.065:
            self.npc_timer = 0.0
            self._update_npcs()

    def _move_player_auto(self) -> None:
        if not self.player:
            return

        if self.player_task is None or self.player_task.delivered:
            self.player_task = self._new_task("Player")

        base_pos = self._movement_base_pos(self.player)

        if (
            not self.player_path_hint
            or self.player_path_hint[-1] != self.player_task.target_pos
            or base_pos not in self.player_path_hint[:2]
        ):
            self._refresh_player_path_hint()

        while self.player_path_hint and self.player_path_hint[0] == base_pos:
            self.player_path_hint.pop(0)

        if not self.player_path_hint:
            self._refresh_player_path_hint()

        if not self.player_path_hint:
            return

        next_pos = self.player_path_hint[0]
        dx = next_pos[0] - base_pos[0]
        dy = next_pos[1] - base_pos[1]

        if not self.pathfinder.can_step(base_pos, next_pos):
            self._refresh_player_path_hint()
            return

        old_dir = self.move_dir
        self.move_dir = (dx, dy)
        self._move_player()
        self.move_dir = old_dir

        if self.player_path_hint and self.player_path_hint[0] == next_pos:
            self.player_path_hint.pop(0)

    def _refresh_player_path_hint(self) -> None:
        if not self.player:
            return

        if self.player_task is None or self.player_task.delivered:
            self.player_task = self._new_task("Player")

        result = self.pathfinder.find_path(
            self._movement_base_pos(self.player),
            self.player_task.target_pos,
            self.settings.selected_algorithm,
        )

        self.player_path_hint = result.path
        self.player_path_expanded = result.expanded_nodes

    def _update_npcs(self) -> None:
        for npc in self.npc_shippers:
            if npc.name not in self.npc_tasks or self.npc_tasks[npc.name].delivered:
                self.npc_tasks[npc.name] = self._new_task(npc.name)
                self.npc_paths[npc.name] = []

            task = self.npc_tasks[npc.name]
            task.assign_to(npc.name)

            if not self.npc_paths.get(npc.name):
                result = self.pathfinder.find_path(
                    self._movement_base_pos(npc), task.target_pos, npc.algorithm
                )
                self.npc_paths[npc.name] = (
                    result.path[1:] if result.success and len(result.path) > 1 else []
                )
                self.npc_expanded[npc.name] = result.expanded_nodes

            path = self.npc_paths.get(npc.name, [])

            if path and getattr(npc, "queued_grid_pos", None) is None:
                base_pos = self._movement_base_pos(npc)

                while path and path[0] == base_pos:
                    path.pop(0)

                if path:
                    next_pos = path[0]
                    dx = next_pos[0] - base_pos[0]
                    dy = next_pos[1] - base_pos[1]

                    if self._try_move_shipper_delta(npc, dx, dy):
                        path.pop(0)
                    else:
                        self.npc_paths[npc.name] = []

            picked = task.try_pickup(npc.name, npc.grid_pos)
            delivered = task.try_deliver(npc.name, npc.grid_pos)

            if picked:
                self.npc_paths[npc.name] = []

            if delivered:
                npc.money += task.reward
                npc.orders += 1
                self.npc_tasks[npc.name] = self._new_task(npc.name)
                self.npc_paths[npc.name] = []

            if npc.grid_pos in self.trap_positions:
                npc.money = max(0, npc.money - 10)
