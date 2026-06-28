from __future__ import annotations

import random
from src.core.game_state import GameState
from src.core.constants import NPC_COLORS, TILE_SIZE
from src.entities.directional_shipper import DirectionalShipper
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.visualizer import AutoVisualAgentPlan, build_auto_visual_plans
from src.systems.asset_paths import get_npc_sprite_paths


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
        if not hasattr(self, "auto_visual_group_id"):
            self.auto_visual_group_id = 1
        self._init_auto_visual_demo()
        self.state = GameState.SIMULATION

    def _update_auto_mode(self, dt: float) -> None:
        if getattr(self, "auto_visual_enabled", False):
            self._update_auto_visual_demo(dt)
            return

        self.npc_timer += dt
        if self.npc_timer >= 0.065:
            self.npc_timer = 0.0
            self._update_npcs()

    def _init_auto_visual_demo(self) -> None:
        """
        Visual demo cho Auto-Mode.

        Simulation chạy theo từng nhóm thuật toán.
        Mỗi nhóm có đúng 3 thuật toán, tương ứng 3 shipper.
        Có thể đổi nhóm bằng các nút G1..G6 trên HUD.
        """
        self.auto_visual_enabled = True
        self.auto_visual_finished = False
        self.auto_visual_error = ""
        self.auto_visual_plan_building = True

        try:
            self.auto_visual_orders = load_orders_for_map(self.settings.selected_map_id)
            group_id = int(getattr(self, "auto_visual_group_id", 1))
            plans = build_auto_visual_plans(
                map_id=self.settings.selected_map_id,
                group_id=group_id,
                visual_safe=True,
            )
        except Exception as exc:
            self.auto_visual_error = f"Không tạo được Auto visual demo: {exc}"
            print(f"[AUTO VISUAL ERROR] {exc}")
            plans = []

        self.auto_visual_plan_building = False
        self.auto_visual_plans: list[AutoVisualAgentPlan] = plans
        self.auto_visual_path_index = {}
        self.auto_visual_completed = {}
        self.auto_visual_targets = {}
        self.auto_visual_hidden_traps = set()
        self.auto_visual_revealed_traps = set()
        self.auto_visual_trap_hits = set()
        self.auto_visual_last_trap_pos = {}
        self.auto_visual_trap_wait_until = {}
        self.auto_visual_started_at = getattr(self, "elapsed_time", 0.0)

        self.npc_shippers = []
        self.npc_paths = {}
        self.npc_tasks = {}
        self.npc_expanded = {}

        for plan in plans:
            self.auto_visual_hidden_traps.update(getattr(plan, "hidden_traps", ()))

        visual_colors = [
            (255, 80, 80),    # shipper 1 - đỏ
            (60, 235, 125),   # shipper 2 - xanh lá
            (255, 180, 55),   # shipper 3 - cam
        ]

        # Dịch nhẹ 3 shipper/path để khi BFS/UCS hoặc các thuật toán trùng đường
        # vẫn nhìn thấy cả 3 thay vì bị đè lên nhau.
        visual_offsets = [
            (-7, -7),
            (0, 0),
            (7, 7),
        ]

        for index, plan in enumerate(plans):
            start_pos = plan.path[0] if plan.path else self.player_spawn
            sprite_index = (index % 3) + 1
            fallback_color = visual_colors[index % len(visual_colors)]

            sprites = self.sprite_loader.load_directional_set(
                get_npc_sprite_paths(sprite_index),
                size=(TILE_SIZE, TILE_SIZE),
                fallback_color=fallback_color,
                label=str(plan.group_id),
            )

            npc = DirectionalShipper(
                f"{plan.algorithm}",
                start_pos,
                sprites,
                TILE_SIZE,
            )
            npc.algorithm = plan.algorithm
            npc.auto_visual_index = index
            npc.auto_visual_color = visual_colors[index % len(visual_colors)]
            npc.auto_visual_offset = visual_offsets[index % len(visual_offsets)]
            npc.auto_visual_alternative_paths = [list(item) for item in getattr(plan, "alternative_paths", ())]
            npc.auto_visual_alternative_actions = [tuple(item) for item in getattr(plan, "alternative_actions", ())]
            npc.allow_diagonal = self._allow_diagonal_movement()
            npc.speed_px = 180.0
            npc.configure_roundabout(
                self._roundabout_center(),
                self._roundabout_ring(),
                self._roundabout_connections(),
            )

            self.npc_shippers.append(npc)
            self.npc_paths[npc.name] = list(plan.path[1:])
            self.npc_expanded[npc.name] = plan.expanded_nodes
            self.auto_visual_targets[npc.name] = self._auto_visual_action_targets(plan.actions)
            self.auto_visual_path_index[npc.name] = 0
            self.auto_visual_completed[npc.name] = False

    def _auto_visual_action_targets(self, actions: tuple[str, ...]) -> list[tuple[str, tuple[int, int]]]:
        orders = {order.id: order for order in getattr(self, "auto_visual_orders", [])}
        targets: list[tuple[str, tuple[int, int]]] = []

        for action in actions:
            if "_" not in action:
                continue

            kind, order_id = action.split("_", 1)
            order = orders.get(order_id)
            if order is None:
                continue

            if kind == "P":
                targets.append(("store", order.store_pos))
            elif kind == "D":
                targets.append(("house", order.customer_pos))

        return targets

    def _advance_auto_visual_target(self, npc, base_pos: tuple[int, int]) -> None:
        targets = getattr(self, "auto_visual_targets", {}).get(npc.name, [])

        while targets and targets[0][1] == base_pos:
            targets.pop(0)

    def _and_or_replan_if_trap_ahead(
        self,
        npc,
        base_pos: tuple[int, int],
        next_pos: tuple[int, int],
        path: list[tuple[int, int]],
    ) -> bool:
        if getattr(npc, "algorithm", "") != "AND_OR_SEARCH":
            return False

        hidden_traps = getattr(self, "auto_visual_hidden_traps", set())
        if next_pos not in hidden_traps:
            return False

        revealed = getattr(self, "auto_visual_revealed_traps", set())
        revealed.add(next_pos)
        self.auto_visual_revealed_traps = revealed

        blocked = set(revealed)
        plans = getattr(npc, "auto_visual_alternative_paths", [])
        current_targets = [target_pos for _, target_pos in self.auto_visual_targets.get(npc.name, [])]

        for plan_path in plans:
            for index, pos in enumerate(plan_path):
                if pos != base_pos:
                    continue

                remain = list(plan_path[index + 1:])
                if not remain:
                    continue
                if any(pos in blocked for pos in remain):
                    continue

                search_from = 0
                valid_plan = True
                for target_pos in current_targets:
                    try:
                        found_at = remain.index(target_pos, search_from)
                    except ValueError:
                        valid_plan = False
                        break
                    search_from = found_at + 1

                if not valid_plan:
                    continue

                self.npc_paths[npc.name] = remain
                return True

        return False

    def _update_auto_visual_demo(self, dt: float) -> None:
        if not getattr(self, "auto_visual_plans", []):
            return

        all_done = True

        for npc in self.npc_shippers:
            if self.auto_visual_completed.get(npc.name, False):
                continue

            wait_until = self.auto_visual_trap_wait_until.get(npc.name, 0.0)
            if wait_until > getattr(self, "elapsed_time", 0.0):
                all_done = False
                continue

            all_done = False

            if getattr(npc, "queued_grid_pos", None) is not None:
                continue

            path = self.npc_paths.get(npc.name, [])
            base_pos = self._movement_base_pos(npc)
            if self._check_auto_visual_hidden_trap(npc, base_pos):
                all_done = False
                continue
            self._advance_auto_visual_target(npc, base_pos)

            while path and path[0] == base_pos:
                path.pop(0)

            if not path:
                self.auto_visual_completed[npc.name] = True
                npc.orders = 6
                continue

            next_pos = path[0]
            if getattr(npc, "algorithm", "") == "AND_OR_SEARCH" and next_pos in getattr(self, "auto_visual_hidden_traps", set()):
                if self._and_or_replan_if_trap_ahead(npc, base_pos, next_pos, path):
                    all_done = False
                    continue
                # Neu khong co plan nao ne duoc bay nay thi cu di tiep,
                # de phan xu ly bay giu 5 giay roi chay tiep binh thuong.

            next_pos = path[0]
            dx = next_pos[0] - base_pos[0]
            dy = next_pos[1] - base_pos[1]

            if self._try_move_auto_visual_delta(npc, dx, dy):
                path.pop(0)
            else:
                # Route Auto đã được tính hợp lệ. Nếu có cell lệch do render/runtime,
                # bỏ qua cell này để demo không kẹt cứng.
                path.pop(0)

        self.auto_visual_finished = all_done

    def _check_auto_visual_hidden_trap(self, npc, base_pos: tuple[int, int]) -> bool:
        hidden_traps = getattr(self, "auto_visual_hidden_traps", set())
        last_pos = getattr(self, "auto_visual_last_trap_pos", {})

        if base_pos not in hidden_traps:
            last_pos.pop(npc.name, None)
            self.auto_visual_last_trap_pos = last_pos
            return False

        if last_pos.get(npc.name) == base_pos:
            return False

        last_pos[npc.name] = base_pos
        self.auto_visual_last_trap_pos = last_pos

        revealed = getattr(self, "auto_visual_revealed_traps", set())
        revealed.add(base_pos)
        self.auto_visual_revealed_traps = revealed

        waits = getattr(self, "auto_visual_trap_wait_until", {})
        waits[npc.name] = float(getattr(self, "elapsed_time", 0.0)) + 5.0
        self.auto_visual_trap_wait_until = waits
        return True

    def _draw_auto_visual_locations(self, bounce_offset: float) -> None:
        """Vẽ pickup/delivery của 6 đơn trong Auto TMX."""
        try:
            import pygame
        except Exception:
            return

        orders = getattr(self, "auto_visual_orders", [])
        cell_w, cell_h = self._cell_size_screen()

        for order in orders:
            sx, sy = self._grid_to_screen(order.store_pos)
            cx, cy = sx + cell_w // 2, sy + cell_h // 2 - int(bounce_offset * 0.35)
            pygame.draw.circle(self.screen, (255, 170, 45), (cx, cy), 10)
            pygame.draw.circle(self.screen, (20, 20, 20), (cx, cy), 10, 2)
            self._draw_text(order.id, self.font_tiny_bold, (255, 255, 255), cx, cy - 8, center=True)

            hx, hy = self._grid_to_screen(order.customer_pos)
            hcx, hcy = hx + cell_w // 2, hy + cell_h // 2
            pygame.draw.circle(self.screen, (80, 220, 120), (hcx, hcy), 9)
            pygame.draw.circle(self.screen, (20, 20, 20), (hcx, hcy), 9, 2)
            self._draw_text(order.id.replace("O", "D"), self.font_tiny_bold, (255, 255, 255), hcx, hcy - 8, center=True)

        self._draw_auto_visual_hidden_traps(bounce_offset)
        self._draw_auto_visual_current_targets(bounce_offset)

    def _draw_auto_visual_hidden_traps(self, bounce_offset: float) -> None:
        try:
            import pygame
        except Exception:
            return

        hidden_traps = getattr(self, "auto_visual_hidden_traps", set())
        revealed = getattr(self, "auto_visual_revealed_traps", set())
        cell_w, cell_h = self._cell_size_screen()
        trap_icon = getattr(self, "icons", {}).get("trap")

        for pos in hidden_traps:
            sx, sy = self._grid_to_screen(pos)
            cx = sx + cell_w // 2
            cy = sy + cell_h // 2 - int(bounce_offset * 0.25)

            if pos in revealed:
                if trap_icon:
                    rect = trap_icon.get_rect(center=(cx, cy))
                    self.screen.blit(trap_icon, rect)
                else:
                    pygame.draw.circle(self.screen, (230, 55, 55), (cx, cy), 11)
                    self._draw_text("!", self.font_tiny_bold, (255, 255, 255), cx, cy - 8, center=True)
            else:
                pygame.draw.circle(self.screen, (40, 80, 120), (cx, cy), 11)
                pygame.draw.circle(self.screen, (255, 230, 90), (cx, cy), 11, 2)
                self._draw_text("?", self.font_tiny_bold, (255, 255, 255), cx, cy - 8, center=True)

    def _draw_auto_visual_current_targets(self, bounce_offset: float) -> None:
        try:
            import pygame
        except Exception:
            return

        targets_by_name = getattr(self, "auto_visual_targets", {})
        cell_w, cell_h = self._cell_size_screen()

        for npc in getattr(self, "npc_shippers", []):
            targets = targets_by_name.get(npc.name, [])
            if not targets:
                continue

            target_kind, target_pos = targets[0]
            sx, sy = self._grid_to_screen(target_pos)
            cx = sx + cell_w // 2
            cy = sy + cell_h // 2 - int(12 + bounce_offset * 0.5)

            icon_key = f"location_npc{getattr(npc, 'auto_visual_index', 0) + 1}"
            icon = getattr(self, "icons", {}).get(icon_key)
            if icon:
                rect = icon.get_rect(center=(cx, cy))
                self.screen.blit(icon, rect)
            else:
                color = getattr(npc, "auto_visual_color", (255, 220, 80))
                pygame.draw.circle(self.screen, color, (cx, cy), 12)
                pygame.draw.circle(self.screen, (20, 20, 20), (cx, cy), 12, 2)

            label = "S" if target_kind == "store" else "H"
            self._draw_text(label, self.font_tiny_bold, (255, 255, 255), cx, cy - 8, center=True)

    def _handle_auto_visual_mouse_click(self, pos: tuple[int, int]) -> bool:
        """Xử lý click riêng trong Auto Visualizer."""
        rects = getattr(self, "auto_visual_group_button_rects", {})

        for group_id, rect in rects.items():
            if rect and rect.collidepoint(pos):
                self.auto_visual_group_id = int(group_id)
                self.elapsed_time = 0.0
                self._init_auto_visual_demo()
                return True

        return False

    def _try_move_auto_visual_delta(self, shipper, dx: int, dy: int) -> bool:
        """
        Di chuyển riêng cho Auto Visualizer.

        Không dùng _try_move_shipper_delta vì hàm đó kiểm tra collision bằng
        Play Mode pathfinder. Auto Visualizer dùng Auto TMX riêng, route đã được
        build từ AutoMapGraph nên chỉ cần kiểm tra bước liền kề rồi move_grid.
        """
        dx = int(dx)
        dy = int(dy)
        allow_diagonal = self._allow_diagonal_movement()

        if allow_diagonal:
            if max(abs(dx), abs(dy)) != 1 or (dx == 0 and dy == 0):
                return False
        else:
            if abs(dx) + abs(dy) != 1:
                return False

        shipper.allow_diagonal = allow_diagonal
        return bool(
            shipper.move_grid(
                dx,
                dy,
                self.map_cols,
                self.map_rows,
                min_y=0,
                allow_diagonal=allow_diagonal,
            )
        )

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
            if wait_action == "pickup":
                self._clear_npc_wait(npc.name)
                wait_action = None

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
                task.stolen_by = npc.name
                task.holder_name = npc.name
                task.picked_up = True
                self._drop_player_task(task)
                self.available_player_tasks = [
                    offer for offer in getattr(self, "available_player_tasks", [])
                    if offer is not task
                ]
                self._replenish_player_order_offers()
                self._start_npc_wait(npc.name, "pickup", 10.0)
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
