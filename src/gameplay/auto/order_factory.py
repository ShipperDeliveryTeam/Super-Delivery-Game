from __future__ import annotations

import random
from collections.abc import Sequence

from src.gameplay.auto.config import get_auto_map_config
from src.gameplay.auto.maps.tmx_loader import AutoMapData, TmxObject, load_auto_map
from src.gameplay.auto.models import AutoOrder, GridPos


def build_fixed_orders(
    map_id: int,
    store_positions: Sequence[GridPos],
    house_positions: Sequence[GridPos],
) -> list[AutoOrder]:
    config = get_auto_map_config(map_id)
    order_count = min(config.order_count, len(store_positions), len(house_positions))

    orders: list[AutoOrder] = []

    for index in range(order_count):
        reward = 100 + index * 20

        orders.append(
            AutoOrder(
                id=f"O{index + 1}",
                store_pos=store_positions[index],
                customer_pos=house_positions[index],
                reward=reward,
                deadline=config.deadline_seconds,
            )
        )

    return orders


def _get_reward_from_pickup(pickup: TmxObject, fallback_reward: int) -> int:
    raw_reward = pickup.properties.get("base_reward")

    if isinstance(raw_reward, int):
        return raw_reward

    return fallback_reward


def build_orders_from_auto_map(map_data: AutoMapData) -> list[AutoOrder]:
    """
    Tạo số đơn cố định từ TMX Auto theo cấu hình map.

    Cách ghép hiện tại:
    - PickupPoint được sắp theo object id tăng dần.
    - DeliveryPoint được sắp theo object id tăng dần.
    - pickup thứ i ghép với delivery thứ i.

    Nhờ vậy mỗi map luôn sinh ra cùng một bộ đơn, phù hợp Benchmark Mode.
    """
    config = get_auto_map_config(map_data.map_id)

    pickup_points = sorted(map_data.pickup_points, key=lambda item: item.id)
    delivery_points = sorted(map_data.delivery_points, key=lambda item: item.id)

    order_count = min(config.order_count, len(pickup_points), len(delivery_points))

    # Mỗi lần load map, các cửa hàng được ghép ngẫu nhiên với các nhà.
    # Seed theo map_id để các thuật toán trong cùng một nhóm dùng chung môi trường.
    rng = random.Random(map_data.map_id * 1000 + 2026)
    delivery_points = list(delivery_points[:order_count])
    rng.shuffle(delivery_points)

    orders: list[AutoOrder] = []

    for index in range(order_count):
        pickup = pickup_points[index]
        delivery = delivery_points[index]

        reward = _get_reward_from_pickup(
            pickup=pickup,
            fallback_reward=100 + index * 20,
        )

        orders.append(
            AutoOrder(
                id=f"O{index + 1}",
                store_pos=pickup.grid_pos,
                customer_pos=delivery.grid_pos,
                reward=reward,
                deadline=config.deadline_seconds,
            )
        )

    return orders


def load_orders_for_map(map_id: int) -> list[AutoOrder]:
    map_data = load_auto_map(map_id)
    return build_orders_from_auto_map(map_data)


def clone_orders_for_benchmark(orders: Sequence[AutoOrder]) -> list[AutoOrder]:
    return [order.clone() for order in orders]


def validate_orders(orders: Sequence[AutoOrder]) -> bool:
    if not orders:
        return False

    order_ids = [order.id for order in orders]

    return len(order_ids) == len(set(order_ids))


def print_orders_summary(map_id: int) -> None:
    orders = load_orders_for_map(map_id)

    print(f"Map {map_id} orders:")

    for order in orders:
        print(
            f"- {order.id}: "
            f"store={order.store_pos} -> customer={order.customer_pos}, "
            f"reward={order.reward}, deadline={order.deadline}"
        )

    print("-" * 40)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        print_orders_summary(current_map_id)
