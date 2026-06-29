import random
from typing import List, Optional, Tuple

from src.gameplay.store_selector import StoreSelector, StoreSelectionResult
from src.gameplay.delivery_task import DeliveryTask

GridPos = Tuple[int, int]


class OrderGenerator:
    """
    Customer / House -> Local Search chọn Store -> tạo DeliveryTask.
    """

    def __init__(self):
        self.store_selector = StoreSelector(max_iterations=20)
        self.last_result: Optional[StoreSelectionResult] = None

    def create_order(
        self,
        stores: List[GridPos],
        houses: List[GridPos],
        pathfinder=None,
        holder_name: Optional[str] = None,
    ) -> DeliveryTask:
        if not stores:
            raise ValueError("Không có store trong map.")

        if not houses:
            raise ValueError("Không có house/customer trong map.")

        customer_pos = random.choice(houses)

        def path_cost(store: GridPos, customer: GridPos) -> int:
            if pathfinder is None:
                return 0

            result = pathfinder.find_path(store, customer, "ASTAR")

            if result.success and result.path:
                return len(result.path)

            return 1_000_000

        result = self.store_selector.select_store(
            stores=stores,
            customer_pos=customer_pos,
            path_cost_fn=path_cost,
        )

        self.last_result = result

        base_reward = 60
        distance_bonus = min(120, result.cost * 3)
        reward = base_reward + distance_bonus + random.randint(0, 30)

        return DeliveryTask(
            store_pos=result.selected_store,
            house_pos=customer_pos,
            reward=reward,
            holder_name=holder_name,
        )
