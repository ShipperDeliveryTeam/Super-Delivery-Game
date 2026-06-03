import random
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

GridPos = Tuple[int, int]


@dataclass
class StoreSelectionResult:
    selected_store: GridPos
    customer_pos: GridPos
    cost: int
    iterations: int
    algorithm: str = "LOCAL_SEARCH"


class StoreSelector:
    """
    Local Search: khách hàng chọn cửa hàng phù hợp nhất để đặt hàng.
    """

    def __init__(self, max_iterations: int = 20):
        self.max_iterations = max_iterations

    def select_store(
        self,
        stores: List[GridPos],
        customer_pos: GridPos,
        path_cost_fn: Optional[Callable[[GridPos, GridPos], int]] = None,
    ) -> StoreSelectionResult:
        if not stores:
            raise ValueError("Không có cửa hàng nào để chọn.")

        current = random.choice(stores)
        current_cost = self._cost(current, customer_pos, path_cost_fn)
        iterations = 0

        candidates = list(stores)
        random.shuffle(candidates)

        improved = True

        while improved and iterations < self.max_iterations:
            improved = False
            iterations += 1

            best_store = current
            best_cost = current_cost

            for store in candidates:
                cost = self._cost(store, customer_pos, path_cost_fn)

                if cost < best_cost:
                    best_store = store
                    best_cost = cost
                    improved = True

            if improved:
                current = best_store
                current_cost = best_cost

        return StoreSelectionResult(
            selected_store=current,
            customer_pos=customer_pos,
            cost=current_cost,
            iterations=iterations,
        )

    def _cost(
        self,
        store: GridPos,
        customer: GridPos,
        path_cost_fn: Optional[Callable[[GridPos, GridPos], int]] = None,
    ) -> int:
        if path_cost_fn is not None:
            cost = path_cost_fn(store, customer)

            if cost > 0:
                return cost

        return self.manhattan(store, customer)

    @staticmethod
    def manhattan(a: GridPos, b: GridPos) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
