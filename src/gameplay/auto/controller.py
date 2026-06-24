from __future__ import annotations

import random

from src.core.game_state import GameState


class AutoModeMixin:
    """Pathfinding, autonomous movement and simulation updates."""

    def _player_route_task(self):
        offers = list(getattr(self, "available_player_tasks", []))
        selected_index = int(getattr(self, "selected_player_order_index", -1))
        if 0 <= selected_index < len(offers):
            selected = offers[selected_index]
            if (
                selected in getattr(self, "player_tasks", [])
                and not getattr(selected, "delivered", False)
                and not getattr(selected, "stolen_by", None)
                and not getattr(selected, "picked_up", False)
            ):
                return selected

        task = getattr(self, "player_task", None)
        if task is not None and not getattr(task, "delivered", False):
            return task

        player_tasks = [
            item for item in getattr(self, "player_tasks", [])
            if not getattr(item, "delivered", False)
        ]
        return player_tasks[0] if player_tasks else None

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

        route_task = self._player_route_task()
        if route_task is None:
            return

        base_pos = self._movement_base_pos(self.player)

        if (
            not self.player_path_hint
            or self.player_path_hint[-1] != route_task.target_pos
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

        route_task = self._player_route_task()
        if route_task is None:
            self.player_path_hint = []
            self.player_path_expanded = 0
            return

        result = self.pathfinder.find_path(
            self._movement_base_pos(self.player),
            route_task.target_pos,
            self.settings.selected_algorithm,
        )

        self.player_path_hint = result.path
        self.player_path_expanded = result.expanded_nodes

    def _update_npcs(self) -> None:
        for npc in self.npc_shippers:
            wait_until = getattr(self, "npc_wait_until", {}).get(npc.name, 0.0)
            if wait_until > getattr(self, "elapsed_time", 0.0):
                continue
            wait_action = getattr(self, "npc_wait_action", {}).get(npc.name)

            if npc.name not in self.npc_tasks or self.npc_tasks[npc.name].delivered or getattr(self.npc_tasks[npc.name], "stolen_by", None) not in (None, npc.name):
                task = self._choose_npc_disruption_task(npc)
                if task is None:
                    continue
                self.npc_tasks[npc.name] = task
                self.npc_paths[npc.name] = []

            task = self.npc_tasks[npc.name]
            if task.picked_up and getattr(task, "stolen_by", None) != npc.name:
                self.npc_tasks.pop(npc.name, None)
                self.npc_paths[npc.name] = []
                continue

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

            if not task.picked_up and npc.grid_pos == task.store_pos:
                if wait_action != "pickup":
                    self._start_npc_wait(npc.name, "pickup", 10.0)
                    continue

                self._clear_npc_wait(npc.name)
                task.stolen_by = npc.name
                task.holder_name = npc.name
                task.picked_up = True
                self._drop_player_task(task)
                self.available_player_tasks = [
                    offer for offer in getattr(self, "available_player_tasks", [])
                    if offer is not task
                ]
                self._replenish_player_order_offers()
                self.npc_paths[npc.name] = []
                continue

            if task.picked_up and npc.grid_pos == task.house_pos:
                if wait_action != "deliver":
                    self._start_npc_wait(npc.name, "deliver", 10.0)
                    continue

                self._clear_npc_wait(npc.name)
                task.delivered = True
                npc.money += task.reward
                npc.orders += 1
                self.npc_tasks.pop(npc.name, None)
                self.npc_paths[npc.name] = []
                continue

            if npc.grid_pos in self.trap_positions:
                npc.money = max(0, npc.money - 10)

    def _start_npc_wait(self, npc_name: str, action: str, seconds: float) -> None:
        waits = getattr(self, "npc_wait_until", {})
        waits[npc_name] = float(getattr(self, "elapsed_time", 0.0)) + float(seconds)
        self.npc_wait_until = waits
        actions = getattr(self, "npc_wait_action", {})
        actions[npc_name] = action
        self.npc_wait_action = actions

    def _clear_npc_wait(self, npc_name: str) -> None:
        waits = getattr(self, "npc_wait_until", {})
        waits.pop(npc_name, None)
        self.npc_wait_until = waits
        actions = getattr(self, "npc_wait_action", {})
        actions.pop(npc_name, None)
        self.npc_wait_action = actions

    def _choose_npc_disruption_task(self, npc) -> object | None:
        offers = [
            task for task in getattr(self, "available_player_tasks", [])
            if not task.delivered and not task.picked_up and not getattr(task, "stolen_by", None)
        ]
        if not offers:
            return None

        if random.random() < 0.5:
            return random.choice(offers)

        if self.player:
            player_pos = self._movement_base_pos(self.player)
            offers.sort(key=lambda task: abs(task.store_pos[0] - player_pos[0]) + abs(task.store_pos[1] - player_pos[1]))
            return random.choice(offers[: min(3, len(offers))])

        offers.sort(key=lambda task: task.reward, reverse=True)
        return random.choice(offers[: min(3, len(offers))])
