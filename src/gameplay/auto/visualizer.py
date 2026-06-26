from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Iterable

from src.ai.adversarial.alpha_beta import alpha_beta_search
from src.ai.adversarial.expectimax import expectimax_search
from src.ai.adversarial.minimax import minimax_search
from src.ai.complex_search.and_or_graph import and_or_search
from src.ai.complex_search.no_observation import no_observation_search
from src.ai.complex_search.partial_observation import partial_observation_search
from src.ai.complex_search.uncertainty_model import UncertaintyModel
from src.ai.csp.ac3_backtracking import ac3_backtracking_search
from src.ai.csp.backtracking import backtracking_search
from src.ai.csp.forward_checking import forward_checking_search
from src.ai.local_search.hill_climbing import hill_climbing
from src.ai.local_search.local_beam import local_beam_search
from src.ai.local_search.route_state import build_default_route_actions
from src.ai.local_search.simulated_annealing import simulated_annealing
from src.gameplay.auto.algorithm_groups import get_algorithms_by_group, get_group_name
from src.gameplay.auto.config import get_auto_map_config
from src.gameplay.auto.maps.graph_adapter import AutoMapGraph
from src.gameplay.auto.maps.tmx_loader import GridPos, load_auto_map
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.pathfinder_adapter import find_auto_path
from src.gameplay.auto.route_cost_matrix import RouteCostMatrix, build_route_cost_matrix


@dataclass(frozen=True)
class AutoVisualAgentPlan:
    group_id: int
    group_name: str
    algorithm: str
    actions: tuple[str, ...]
    path: list[GridPos]
    total_cost: float
    expanded_nodes: int
    runtime_ms: float
    note: str = ""

    @property
    def completed_orders(self) -> int:
        return sum(1 for action in self.actions if action.startswith("D_"))


def _node_path_from_actions(
    matrix: RouteCostMatrix,
    actions: Iterable[str],
) -> list[GridPos]:
    full_path: list[GridPos] = []
    current_label = "START"

    for action in actions:
        segment = matrix.get_path(current_label, action)

        if not segment:
            current_label = action
            continue

        if not full_path:
            full_path.extend(segment)
        else:
            full_path.extend(segment[1:])

        current_label = action

    return full_path


def _default_actions(order_ids: list[str]) -> tuple[str, ...]:
    return build_default_route_actions(order_ids)


def _build_pathfinding_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    algorithm: str,
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    map_data = load_auto_map(map_id)
    graph = AutoMapGraph(map_data)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    node_positions: dict[str, GridPos] = {"START": map_data.start_position}
    for order in orders:
        node_positions[f"P_{order.id}"] = order.store_pos
        node_positions[f"D_{order.id}"] = order.customer_pos

    actions = _default_actions(order_ids)
    current_pos = map_data.start_position
    full_path: list[GridPos] = [current_pos]
    total_cost = 0.0
    expanded_nodes = 0
    note = "Sequential route"

    for action in actions:
        target_pos = node_positions[action]
        result = find_auto_path(
            graph=graph,
            start=current_pos,
            goal=target_pos,
            algorithm=algorithm,
        )

        expanded_nodes += result.expanded_nodes

        if not result.found:
            note = f"Stopped before {action}"
            break

        total_cost += result.cost
        full_path.extend(result.path[1:])
        current_pos = target_pos

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm=algorithm,
        actions=actions,
        path=full_path,
        total_cost=total_cost,
        expanded_nodes=expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note=note,
    )


def _build_hill_climbing_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    matrix: RouteCostMatrix,
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    result = hill_climbing(
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
        max_iterations=100,
    )

    actions = result.best_state.actions

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm="HILL_CLIMBING",
        actions=actions,
        path=_node_path_from_actions(matrix, actions),
        total_cost=result.best_state.total_cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note="Local optimum",
    )


def _build_local_beam_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    matrix: RouteCostMatrix,
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    result = local_beam_search(
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
        beam_width=5,
        max_iterations=100,
        seed=42,
    )

    actions = result.best_state.actions

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm="LOCAL_BEAM",
        actions=actions,
        path=_node_path_from_actions(matrix, actions),
        total_cost=result.best_state.total_cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note="Beam width = 5",
    )


def _build_simulated_annealing_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    matrix: RouteCostMatrix,
    visual_safe: bool,
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    result = simulated_annealing(
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
        initial_temperature=120.0,
        cooling_rate=0.985,
        min_temperature=0.01,
        max_iterations=350 if visual_safe else 1000,
        seed=42,
        restart_count=3 if visual_safe else 8,
    )

    actions = result.best_state.actions

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm="SIMULATED_ANNEALING",
        actions=actions,
        path=_node_path_from_actions(matrix, actions),
        total_cost=result.best_state.total_cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note="Visual preset nhẹ" if visual_safe else "Benchmark preset",
    )


def _build_no_observation_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    matrix: RouteCostMatrix,
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]
    uncertainty_model = UncertaintyModel(matrix)

    result = no_observation_search(
        order_ids=order_ids,
        capacity=config.capacity,
        uncertainty_model=uncertainty_model,
    )

    actions = result.actions

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm="NO_OBSERVATION",
        actions=actions,
        path=_node_path_from_actions(matrix, actions),
        total_cost=result.normal_cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note="Expected risk cost",
    )


def _build_partial_observation_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    matrix: RouteCostMatrix,
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]
    uncertainty_model = UncertaintyModel(matrix)

    result = partial_observation_search(
        order_ids=order_ids,
        capacity=config.capacity,
        uncertainty_model=uncertainty_model,
        max_iterations=100,
    )

    actions = result.actions

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm="PARTIAL_OBSERVATION",
        actions=actions,
        path=_node_path_from_actions(matrix, actions),
        total_cost=result.normal_cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note="Partial risk cost",
    )


def _build_and_or_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    matrix: RouteCostMatrix,
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]
    uncertainty_model = UncertaintyModel(matrix)

    result = and_or_search(
        order_ids=order_ids,
        capacity=config.capacity,
        uncertainty_model=uncertainty_model,
        beam_width=5,
        max_iterations=100,
        seed=42,
    )

    actions = result.actions

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm="AND_OR_SEARCH",
        actions=actions,
        path=_node_path_from_actions(matrix, actions),
        total_cost=result.normal_cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note="Worst-case route",
    )


def _build_backtracking_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    matrix: RouteCostMatrix,
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    result = backtracking_search(
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
        max_expanded_nodes=10000,
    )

    actions = result.best_state.actions

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm="BACKTRACKING",
        actions=actions,
        path=_node_path_from_actions(matrix, actions),
        total_cost=result.best_state.total_cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note="Pure CSP backtracking",
    )


def _build_forward_checking_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    matrix: RouteCostMatrix,
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    result = forward_checking_search(
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
        max_expanded_nodes=15000,
    )

    actions = result.best_state.actions

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm="FORWARD_CHECKING",
        actions=actions,
        path=_node_path_from_actions(matrix, actions),
        total_cost=result.best_state.total_cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note="CSP + forward checking",
    )


def _build_ac3_backtracking_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    matrix: RouteCostMatrix,
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    result = ac3_backtracking_search(
        order_ids=order_ids,
        capacity=config.capacity,
        cost_provider=matrix,
        max_expanded_nodes=20000,
    )

    actions = result.best_state.actions

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm="AC3_BACKTRACKING",
        actions=actions,
        path=_node_path_from_actions(matrix, actions),
        total_cost=result.best_state.total_cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note="AC-3 precheck + CSP",
    )


def _build_adversarial_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    matrix: RouteCostMatrix,
    algorithm: str,
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    if algorithm == "MINIMAX":
        result = minimax_search(order_ids=order_ids, orders=orders, matrix=matrix, depth_limit=len(order_ids))
    elif algorithm == "ALPHA_BETA":
        result = alpha_beta_search(order_ids=order_ids, orders=orders, matrix=matrix, depth_limit=len(order_ids))
    elif algorithm == "EXPECTIMAX":
        result = expectimax_search(order_ids=order_ids, orders=orders, matrix=matrix, depth_limit=len(order_ids))
    else:
        raise ValueError(f"Unsupported adversarial algorithm: {algorithm}")

    actions: list[str] = []
    for order_id in result.best_sequence:
        actions.append(f"P_{order_id}")
        actions.append(f"D_{order_id}")

    action_tuple = tuple(actions)

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm=algorithm,
        actions=action_tuple,
        path=_node_path_from_actions(matrix, action_tuple),
        total_cost=0.0,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note=f"Utility={round(result.expected_utility, 2)}, pruned={result.pruned_nodes}",
    )


def build_auto_visual_plans(
    map_id: int,
    group_id: int = 1,
    visual_safe: bool = True,
) -> list[AutoVisualAgentPlan]:
    group_id = int(group_id)
    algorithms = get_algorithms_by_group(group_id)

    if not algorithms:
        raise ValueError(f"Invalid visual group: {group_id}")

    group_name = get_group_name(group_id)
    matrix = build_route_cost_matrix(map_id=map_id, algorithm="ASTAR")
    plans: list[AutoVisualAgentPlan] = []

    for algorithm in algorithms:
        if group_id in (1, 2):
            plans.append(_build_pathfinding_plan(map_id, group_id, group_name, algorithm))
        elif algorithm == "HILL_CLIMBING":
            plans.append(_build_hill_climbing_plan(map_id, group_id, group_name, matrix))
        elif algorithm == "LOCAL_BEAM":
            plans.append(_build_local_beam_plan(map_id, group_id, group_name, matrix))
        elif algorithm == "SIMULATED_ANNEALING":
            plans.append(_build_simulated_annealing_plan(map_id, group_id, group_name, matrix, visual_safe))
        elif algorithm == "NO_OBSERVATION":
            plans.append(_build_no_observation_plan(map_id, group_id, group_name, matrix))
        elif algorithm == "PARTIAL_OBSERVATION":
            plans.append(_build_partial_observation_plan(map_id, group_id, group_name, matrix))
        elif algorithm == "AND_OR_SEARCH":
            plans.append(_build_and_or_plan(map_id, group_id, group_name, matrix))
        elif algorithm == "BACKTRACKING":
            plans.append(_build_backtracking_plan(map_id, group_id, group_name, matrix))
        elif algorithm == "FORWARD_CHECKING":
            plans.append(_build_forward_checking_plan(map_id, group_id, group_name, matrix))
        elif algorithm == "AC3_BACKTRACKING":
            plans.append(_build_ac3_backtracking_plan(map_id, group_id, group_name, matrix))
        elif algorithm in ("MINIMAX", "ALPHA_BETA", "EXPECTIMAX"):
            plans.append(_build_adversarial_plan(map_id, group_id, group_name, matrix, algorithm))
        else:
            raise ValueError(f"Unsupported visual algorithm: {algorithm}")

    return plans
