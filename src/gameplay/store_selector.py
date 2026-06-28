from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Tuple


GridPos = Tuple[int, int]
PathCostFn = Callable[[GridPos, GridPos], float]


@dataclass(frozen=True)
class StoreSelectionResult:
    selected_store: GridPos
    customer_pos: GridPos
    cost: float
    expanded_nodes: int
    generated_nodes: int
    iterations: int
    algorithm: str = "STORE_SELECTOR"


class StoreSelector:
    """
    Local Search đơn giản dùng cho Play Mode.

    Nhiệm vụ:
    - Nhận danh sách store.
    - Nhận vị trí customer/house.
    - Chọn store có chi phí đi đến customer thấp nhất.

    File này chủ yếu phục vụ OrderGenerator cũ của Play Mode.
    Auto-Mode không phụ thuộc trực tiếp vào file này.
    """

    def __init__(self, max_iterations: int = 20) -> None:
        self.max_iterations = max_iterations

    def select_store(
        self,
        stores: list[GridPos],
        customer_pos: GridPos,
        path_cost_fn: PathCostFn,
    ) -> StoreSelectionResult:
        if not stores:
            raise ValueError("StoreSelector requires at least one store.")

        best_store = stores[0]
        best_cost = float("inf")

        expanded_nodes = 0
        generated_nodes = len(stores)
        iterations = 0

        for store in stores:
            if iterations >= self.max_iterations:
                break

            iterations += 1
            expanded_nodes += 1

            cost = path_cost_fn(store, customer_pos)

            if cost < best_cost:
                best_cost = cost
                best_store = store

        if best_cost == float("inf"):
            best_cost = 0.0

        return StoreSelectionResult(
            selected_store=best_store,
            customer_pos=customer_pos,
            cost=best_cost,
            expanded_nodes=expanded_nodes,
            generated_nodes=generated_nodes,
            iterations=iterations,
        )