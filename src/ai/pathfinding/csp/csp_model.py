from __future__ import annotations

import random
from dataclasses import dataclass
from time import perf_counter

from src.ai.pathfinding.csp.route_state import (
    RouteState,
    get_order_id,
    is_delivery,
    is_pickup,
    make_route_state,
)


class RouteCostProvider:
    def get_cost(self, from_label: str, to_label: str) -> float:
        raise NotImplementedError


@dataclass
class CSPRouteProblem:
    order_ids: list[str]
    capacity: int
    cost_provider: RouteCostProvider


@dataclass
class CSPRouteSearchResult:
    algorithm: str
    best_state: RouteState
    initial_state: RouteState
    iterations: int
    expanded_nodes: int
    generated_nodes: int
    backtracks: int
    runtime_ms: float
    stopped_by_limit: bool

    @property
    def improved(self) -> bool:
        return self.best_state.total_cost < self.initial_state.total_cost


def make_all_actions(order_ids: list[str]) -> list[str]:
    """Tao tat ca hanh dong pickup/delivery cho cac don hang."""
    actions = []

    for order_id in order_ids:
        actions.append(f"P_{order_id}")
        actions.append(f"D_{order_id}")

    return actions


def make_domains(order_ids: list[str]) -> list[list[str]]:
    """Moi vi tri trong route deu co mien gia tri la tat ca action."""
    all_actions = make_all_actions(order_ids)
    total_steps = len(all_actions)
    domains = []

    for _ in range(total_steps):
        domains.append(list(all_actions))

    return domains


def is_action_allowed(
    action: str,
    used_actions: set[str],
    picked: set[str],
    carrying: set[str],
    delivered: set[str],
    capacity: int,
) -> bool:
    """Kiem tra mot hanh dong co hop le tai trang thai hien tai khong."""
    if action in used_actions:
        return False

    order_id = get_order_id(action) # lấy order_id từ action

    if is_pickup(action): # kiểm tra xem hành động có phải là pickup không
        if order_id in picked: # nếu order_id đã được pickup trước đó, hành động này không hợp lệ
            return False
        if len(carrying) >= capacity: # nếu số lượng đơn hàng đang mang đã đạt đến giới hạn capacity, hành động này không hợp lệ
            return False
        return True

    if is_delivery(action): # kiểm tra xem hành động có phải là delivery không
        if order_id not in carrying: # nếu order_id chưa được pickup trước đó, hành động này không hợp lệ
            return False
        if order_id in delivered: # nếu order_id đã được delivery trước đó, hành động này không hợp lệ
            return False
        return True

    return False


def get_available_actions(
    domain: list[str],
    used_actions: set[str],
    picked: set[str],
    carrying: set[str],
    delivered: set[str],
    capacity: int,
) -> list[str]:
    """Lay danh sach hanh dong co the chon tiep."""
    available = []

    for action in domain:
        if is_action_allowed(action, used_actions, picked, carrying, delivered, capacity):
            available.append(action)

    return available


def apply_action(
    action: str,
    used_actions: set[str],
    picked: set[str],
    carrying: set[str],
    delivered: set[str],
) -> tuple[set[str], set[str], set[str], set[str]]:
    """Tra ve cac tap moi sau khi chon mot hanh dong."""
    order_id = get_order_id(action)

    new_used = set(used_actions)
    new_picked = set(picked)
    new_carrying = set(carrying)
    new_delivered = set(delivered)

    new_used.add(action)

    if is_pickup(action):
        new_picked.add(order_id)
        new_carrying.add(order_id)
    elif is_delivery(action):
        new_carrying.remove(order_id)
        new_delivered.add(order_id)

    return new_used, new_picked, new_carrying, new_delivered


def simple_forward_check(
    next_domain: list[str],
    used_actions: set[str],
    picked: set[str],
    carrying: set[str],
    delivered: set[str],
    capacity: int,
) -> bool:
    """Forward checking don gian: sau buoc nay phai con it nhat 1 nuoc di."""
    return bool(
        get_available_actions(
            next_domain,
            used_actions,
            picked,
            carrying,
            delivered,
            capacity,
        )
    )


def simple_ac3_check(order_ids: list[str]) -> bool:
    """AC-3 ban don gian: du lieu dau vao khong duoc rong/trung ma don."""
    seen = set()

    for order_id in order_ids:
        if not order_id or order_id in seen:
            return False
        seen.add(order_id)

    return True


def solve_csp_route(
    problem: CSPRouteProblem,
    algorithm: str,
    action_strategy: str,
    use_forward_checking: bool,
    use_ac3_precheck: bool,
    max_expanded_nodes: int,
) -> CSPRouteSearchResult:
    """Giai CSP bang backtracking truc tiep, viet ro tung buoc de de doc."""
    started_at = perf_counter()

    _ = action_strategy

    if use_ac3_precheck and not simple_ac3_check(problem.order_ids):
        raise ValueError("AC-3 preprocessing failed.")

    initial_state = RouteState(
        actions=tuple(),
        total_cost=float("inf"),
        is_valid=False,
        reason="No route has been assigned yet.",
    )

    domains = make_domains(problem.order_ids)
    total_steps = len(domains)
    rng = random.Random()

    best_state: RouteState | None = None    
    stopped_by_limit = False

    iterations = 0
    expanded_nodes = 0
    generated_nodes = 1
    backtracks = 0

    def backtrack(
        actions: list[str],
        used_actions: set[str],
        picked: set[str],
        carrying: set[str],
        delivered: set[str],
    ) -> None:
        nonlocal best_state
        nonlocal stopped_by_limit
        nonlocal iterations
        nonlocal expanded_nodes
        nonlocal generated_nodes
        nonlocal backtracks

        if expanded_nodes >= max_expanded_nodes: # vượt quá số lượng nút mở rộng tối đa, dừng lại
            stopped_by_limit = True
            return

        iterations += 1 # mở rộng một nút mới, tăng số lượng nút đã mở rộng lên 1
        expanded_nodes += 1 # tổng số nút được xét tăng lên 1

        if len(actions) == total_steps:
            candidate = make_route_state(
                actions=actions,
                order_ids=problem.order_ids,
                capacity=problem.capacity,
                cost_provider=problem.cost_provider,
            )

            if candidate.is_valid and (best_state is None or candidate.better_than(best_state)): # nếu candidate hợp lệ và tốt hơn best_state hiện tại, cập nhật best_state
                best_state = candidate

            if not candidate.is_valid:
                backtracks += 1
            return
        
        step = len(actions) 
        domain = list(domains[step]) # lấy miền giá trị của bước hiện tại
        rng.shuffle(domain)

        choices = get_available_actions(
            domain,
            used_actions,
            picked,
            carrying,
            delivered,
            problem.capacity,
        )
        generated_nodes += len(choices)

        if not choices:
            backtracks += 1
            return

        for action in choices:
            new_used, new_picked, new_carrying, new_delivered = apply_action(
                action,
                used_actions,
                picked,
                carrying,
                delivered,
            )

            route_is_not_finished = len(actions) + 1 < total_steps # nếu chưa fill xong
            if use_forward_checking and route_is_not_finished:
                next_step = len(actions) + 1 # tính bước tiếp theo
                can_continue = simple_forward_check(
                    domains[next_step],
                    new_used,
                    new_picked,
                    new_carrying,
                    new_delivered,
                    problem.capacity,
                )

                if not can_continue:
                    backtracks += 1
                    continue

            backtrack(
                actions=[*actions, action],
                used_actions=new_used,
                picked=new_picked,
                carrying=new_carrying,
                delivered=new_delivered,
            )

            if stopped_by_limit:
                return

    backtrack(
        actions=[],
        used_actions=set(),
        picked=set(),
        carrying=set(),
        delivered=set(),
    )

    return CSPRouteSearchResult(
        algorithm=algorithm,
        best_state=best_state or initial_state,
        initial_state=initial_state,
        iterations=iterations,
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        backtracks=backtracks,
        runtime_ms=(perf_counter() - started_at) * 1000,
        stopped_by_limit=stopped_by_limit,
    )
