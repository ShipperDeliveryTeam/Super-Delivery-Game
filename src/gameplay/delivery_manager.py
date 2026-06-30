from __future__ import annotations

import random
from typing import Optional, Tuple

from src.gameplay.delivery_task import DeliveryTask


class DeliveryManagerMixin:
    PLAYER_OFFER_COUNT = 5
    PLAYER_CARGO_LIMIT = 3
    PLAYER_DELIVERY_BASE_SECONDS = 30.0
    PLAYER_DELIVERY_SECONDS_PER_STEP = 1.2
    PLAYER_MIN_DELIVERY_TIME_LIMIT = 45.0
    PLAYER_MAX_DELIVERY_TIME_LIMIT = 150.0
    PLAYER_LATE_DELIVERY_PENALTY_RATIO = 0.25
    PLAYER_MIN_LATE_DELIVERY_PENALTY = 20
    PLAYER_MAX_LATE_DELIVERY_PENALTY = 120

    def _new_task(self, holder_name: Optional[str] = None) -> DeliveryTask:
        fallback_task = None

        for _ in range(40):
            task = self.order_generator.create_order(
                stores=self.store_positions,
                houses=self.house_positions,
                pathfinder=self.pathfinder,
                holder_name=holder_name,
            )

            if fallback_task is None:
                fallback_task = task

            if self._task_is_reachable(task, holder_name):
                return task

        reachable_task = self._first_reachable_task(holder_name)
        return reachable_task or fallback_task

    def _holder_grid_pos(self, holder_name: Optional[str]) -> Tuple[int, int] | None:
        if holder_name == "Player" and self.player:
            return self._movement_base_pos(self.player)

        for npc in self.npc_shippers:
            if npc.name == holder_name:
                return self._movement_base_pos(npc)

        return None

    def _task_is_reachable(self, task: DeliveryTask, holder_name: Optional[str]) -> bool:
        start = self._holder_grid_pos(holder_name)

        if start is not None:
            to_store = self.pathfinder.find_path(start, task.store_pos, "ASTAR")

            if not to_store.success:
                return False

        to_house = self.pathfinder.find_path(task.store_pos, task.house_pos, "ASTAR")
        return bool(to_house.success)

    def _first_reachable_task(self, holder_name: Optional[str]) -> DeliveryTask | None:
        start = self._holder_grid_pos(holder_name)

        for store in self.store_positions:
            if start is not None and not self.pathfinder.find_path(start, store, "ASTAR").success:
                continue

            for house in self.house_positions:
                result = self.pathfinder.find_path(store, house, "ASTAR")

                if result.success:
                    self.order_generator.last_result = None
                    return DeliveryTask(
                        store_pos=store,
                        house_pos=house,
                        reward=90,
                        holder_name=holder_name,
                    )

        return None

    def _create_player_order_offer(self, used_stores: set[Tuple[int, int]] | None = None) -> DeliveryTask:
        used_stores = set(used_stores or set())
        task = self._random_player_offer_for_unused_store(used_stores) or self._new_task(None)
        self._next_player_order_id = getattr(self, "_next_player_order_id", 0) + 1
        task.order_id = f"A{self._next_player_order_id:02d}"
        task.created_at = float(getattr(self, "elapsed_time", 0.0))
        task.expires_in = 150.0 + (self._next_player_order_id % 3) * 30.0
        task.delivery_time_limit = self._delivery_time_limit_for_task(task)
        task.delivery_started_at = None
        task.lost = False
        return task

    def _delivery_time_limit_for_task(self, task: DeliveryTask) -> float:
        result = self.pathfinder.find_path(task.store_pos, task.house_pos, "ASTAR")
        steps = len(result.path) - 1 if result.success and result.path else 50
        limit = self.PLAYER_DELIVERY_BASE_SECONDS + steps * self.PLAYER_DELIVERY_SECONDS_PER_STEP
        return max(
            self.PLAYER_MIN_DELIVERY_TIME_LIMIT,
            min(self.PLAYER_MAX_DELIVERY_TIME_LIMIT, float(limit)),
        )

    def _format_seconds(self, seconds: float | int) -> str:
        remaining = max(0, int(seconds))
        return f"{remaining // 60:02d}:{remaining % 60:02d}"

    def _delivery_remaining_seconds(self, task: DeliveryTask, now: float | None = None) -> float | None:
        if not getattr(task, "picked_up", False) or getattr(task, "delivered", False) or getattr(task, "lost", False):
            return None

        started_at = getattr(task, "delivery_started_at", None)
        if started_at is None:
            return float(getattr(task, "delivery_time_limit", 0.0))

        current_time = float(getattr(self, "elapsed_time", 0.0) if now is None else now)
        return float(getattr(task, "delivery_time_limit", 0.0)) - (current_time - float(started_at))

    def _delivery_display_seconds(self, task: DeliveryTask, now: float | None = None) -> float:
        remaining = self._delivery_remaining_seconds(task, now)
        if remaining is not None:
            return remaining

        return float(getattr(task, "delivery_time_limit", 0.0))

    def _late_delivery_penalty(self, task: DeliveryTask) -> int:
        penalty = round(int(getattr(task, "reward", 0)) * self.PLAYER_LATE_DELIVERY_PENALTY_RATIO)
        return max(
            self.PLAYER_MIN_LATE_DELIVERY_PENALTY,
            min(self.PLAYER_MAX_LATE_DELIVERY_PENALTY, int(penalty)),
        )

    def _expire_player_delivery(self, task: DeliveryTask) -> int:
        penalty = self._late_delivery_penalty(task)
        was_active_task = self.player_task is task
        offers_before = list(getattr(self, "available_player_tasks", []))
        selected_index = int(getattr(self, "selected_player_order_index", -1))
        selected_task = offers_before[selected_index] if 0 <= selected_index < len(offers_before) else None

        if self.player:
            self.player.money = max(0, int(self.player.money) - penalty)

        task.lost = True
        task.holder_name = None
        self.available_player_tasks = [
            offer for offer in offers_before
            if offer is not task
        ]
        self._drop_player_task(task)
        if selected_task is task or self.selected_player_order_index >= len(self.available_player_tasks):
            self.selected_player_order_index = (
                self.available_player_tasks.index(self.player_task)
                if self.player_task in self.available_player_tasks
                else -1
            )

        if was_active_task and self.delivery_confirmation_open:
            self.delivery_confirmation_open = False
            self.delivery_checkbox_checked = False

        self.last_delivery_timeout_message = f"QUA GIO! Mat don #{task.order_id}, tru {penalty} xu"
        self.delivery_timeout_notice_until = float(getattr(self, "elapsed_time", 0.0)) + 3.0
        self._replenish_player_order_offers()
        self._refresh_player_path_hint()
        return penalty

    def _update_player_delivery_timeouts(self) -> None:
        now = float(getattr(self, "elapsed_time", 0.0))
        for task in list(getattr(self, "player_tasks", [])):
            remaining = self._delivery_remaining_seconds(task, now)
            if remaining is not None and remaining <= 0:
                self._expire_player_delivery(task)

    def _random_player_offer_for_unused_store(self, used_stores: set[Tuple[int, int]]) -> DeliveryTask | None:
        stores = [store for store in getattr(self, "store_positions", []) if store not in used_stores]
        houses = list(getattr(self, "house_positions", []))
        random.shuffle(stores)

        for store in stores:
            random.shuffle(houses)
            for house in houses:
                result = self.pathfinder.find_path(store, house, "ASTAR")
                if not result.success:
                    continue

                base_reward = int(getattr(self, "store_rewards", {}).get(store, 60))
                distance_bonus = min(120, len(result.path) * 3)
                reward = base_reward + distance_bonus + random.randint(0, 30)
                return DeliveryTask(store_pos=store, house_pos=house, reward=reward)

        return None

    def _generate_player_order_offers(self, count: int | None = None) -> None:
        target_count = int(count or self.PLAYER_OFFER_COUNT)
        offers: list[DeliveryTask] = []
        used_stores: set[Tuple[int, int]] = set()

        for _ in range(target_count * 20):
            task = self._create_player_order_offer(used_stores)

            if task.store_pos in used_stores:
                continue

            used_stores.add(task.store_pos)
            offers.append(task)

            if len(offers) >= target_count:
                break

        self.available_player_tasks = offers
        self.selected_player_order_index = -1
        self.player_task = None

    def _replenish_player_order_offers(self) -> None:
        offers = list(getattr(self, "available_player_tasks", []))
        used_stores = {task.store_pos for task in offers}

        for _ in range(self.PLAYER_OFFER_COUNT * 20):
            if len(offers) >= self.PLAYER_OFFER_COUNT:
                break

            task = self._create_player_order_offer(used_stores)

            if task.store_pos in used_stores:
                continue

            used_stores.add(task.store_pos)
            offers.append(task)

        self.available_player_tasks = offers

    def _select_player_order(self, index: int) -> bool:
        offers = getattr(self, "available_player_tasks", [])

        if not 0 <= int(index) < len(offers):
            return False

        task = offers[index]

        if getattr(task, "stolen_by", None) or getattr(task, "lost", False):
            return False

        player_tasks = list(getattr(self, "player_tasks", []))

        self.selected_player_order_index = int(index)

        if task not in player_tasks:
            if len(player_tasks) >= self.PLAYER_CARGO_LIMIT:
                return False

            player_tasks.append(task)

        task.holder_name = "Player"
        self.player_tasks = player_tasks
        if getattr(task, "picked_up", False):
            self.player_task = task
        elif self.player_task is task:
            self.player_task = None
        self.delivery_confirmation_open = False
        self.delivery_checkbox_checked = False
        self._refresh_player_path_hint()
        return True

    def _drop_player_task(self, task: DeliveryTask) -> None:
        self.player_tasks = [
            item for item in getattr(self, "player_tasks", [])
            if item is not task
        ]

        if self.player_task is task:
            picked_tasks = [
                item for item in self.player_tasks
                if getattr(item, "picked_up", False) and not getattr(item, "delivered", False)
            ]
            self.player_task = picked_tasks[0] if picked_tasks else None
            self.selected_player_order_index = (
                self.available_player_tasks.index(self.player_task)
                if self.player_task in getattr(self, "available_player_tasks", [])
                else -1
            )

    def _house_number(self, pos: Tuple[int, int]) -> int:
        try:
            return self.house_positions.index(pos) + 1
        except ValueError:
            return 0

    def _store_display_name(self, pos: Tuple[int, int]) -> str:
        name = str(getattr(self, "store_names", {}).get(pos, "Cua hang"))
        return name.replace("_", " ").strip().upper()

    def _confirm_player_delivery(self) -> bool:
        task = getattr(self, "player_task", None)

        if (
            not task
            or not self.player
            or not getattr(self, "delivery_checkbox_checked", False)
            or self.player.grid_pos != task.house_pos
        ):
            return False

        remaining = self._delivery_remaining_seconds(task)
        if remaining is not None and remaining <= 0:
            self._expire_player_delivery(task)
            return False

        if not task.try_deliver("Player", self.player.grid_pos):
            return False

        self.player.money += task.reward
        self.player.orders += 1
        house_number = self._house_number(task.house_pos)
        delivered = getattr(self, "delivered_house_numbers", [])

        if house_number and house_number not in delivered:
            delivered.append(house_number)

        self.delivered_house_numbers = delivered[-6:]
        self.available_player_tasks = [
            offer for offer in getattr(self, "available_player_tasks", [])
            if offer is not task
        ]
        self._drop_player_task(task)
        self.delivery_confirmation_open = False
        self.delivery_checkbox_checked = False
        self._delivery_prompt_dismissed_pos = None
        self._replenish_player_order_offers()
        self._play_sound_effect("delivery")

        return True
