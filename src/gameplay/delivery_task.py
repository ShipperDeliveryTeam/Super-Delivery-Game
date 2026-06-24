from dataclasses import dataclass
from typing import Optional, Tuple

GridPos = Tuple[int, int]


@dataclass
class DeliveryTask:
    store_pos: GridPos
    house_pos: GridPos
    reward: int
    holder_name: Optional[str] = None
    picked_up: bool = False
    delivered: bool = False
    order_id: str = ""
    created_at: float = 0.0
    expires_in: float = 180.0
    stolen_by: Optional[str] = None
    pickup_started_at: Optional[float] = None
    delivery_started_at: Optional[float] = None

    @property
    def target_pos(self) -> GridPos:
        if self.picked_up:
            return self.house_pos
        return self.store_pos

    def assign_to(self, shipper_name: str) -> bool:
        if self.holder_name is not None and self.holder_name != shipper_name:
            return False

        self.holder_name = shipper_name
        return True

    def try_pickup(self, shipper_name: str, pos: GridPos) -> bool:
        if self.delivered:
            return False

        if self.stolen_by and self.stolen_by != shipper_name:
            return False

        if self.holder_name != shipper_name:
            return False

        if not self.picked_up and pos == self.store_pos:
            self.picked_up = True
            return True

        return False

    def try_deliver(self, shipper_name: str, pos: GridPos) -> bool:
        if self.delivered:
            return False

        if self.holder_name != shipper_name:
            return False

        if self.picked_up and pos == self.house_pos:
            self.delivered = True
            return True

        return False
