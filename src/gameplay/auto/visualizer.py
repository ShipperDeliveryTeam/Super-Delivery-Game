from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Iterable

from src.ai.pathfinding.adversarial.alpha_beta import alpha_beta_search
from src.ai.pathfinding.adversarial.expectimax import expectimax_search
from src.ai.pathfinding.adversarial.game_state import (
    PLAYER_TURN,
    AdversarialGameState,
    build_reward_map,
    calculate_order_gain,
)
from src.ai.pathfinding.adversarial.minimax import minimax_search
from src.ai.pathfinding.complex_search import and_or_search, no_observation_search, partial_observation_search
from src.ai.pathfinding.complex_search.no_observation import union_belief_traps
from src.ai.pathfinding.csp.ac3_backtracking import ac3_backtracking_search
from src.ai.pathfinding.csp.backtracking import backtracking_search
from src.ai.pathfinding.csp.forward_checking import forward_checking_search
from src.gameplay.auto.algorithm_groups import get_algorithms_by_group, get_group_name
from src.gameplay.auto.config import get_auto_map_config
from src.gameplay.auto.complex_traps import build_trap_setup
from src.gameplay.auto.delivery_search import delivery_search
from src.gameplay.auto.maps.tmx_loader import GridPos, load_auto_map
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.route_cost_matrix import RouteCostMatrix, build_route_cost_matrix


ADVERSARIAL_VISUAL_ALGORITHM = "ALPHA_BETA"
GREEDY_OPPONENT_ALGORITHM = "GREEDY"
ADVERSARIAL_VISUAL_ALGORITHMS = ("MINIMAX", "ALPHA_BETA", "EXPECTIMAX")


def normalize_adversarial_visual_algorithm(algorithm: str | None) -> str:
    normalized = str(algorithm or ADVERSARIAL_VISUAL_ALGORITHM).upper()
    return normalized if normalized in ADVERSARIAL_VISUAL_ALGORITHMS else ADVERSARIAL_VISUAL_ALGORITHM


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
    hidden_traps: tuple[GridPos, ...] = ()
    belief_traps: tuple[GridPos, ...] = ()
    belief_states: tuple[tuple[GridPos, ...], ...] = ()
    known_traps: tuple[GridPos, ...] = ()
    belief_count: int = 0
    alternative_paths: tuple[tuple[GridPos, ...], ...] = ()
    alternative_actions: tuple[tuple[str, ...], ...] = ()

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


def _actions_from_order_ids(order_ids: Iterable[str]) -> tuple[str, ...]:
    actions: list[str] = []

    for order_id in order_ids:
        actions.append(f"P_{order_id}")
        actions.append(f"D_{order_id}")

    return tuple(actions)


def _cost_from_actions(matrix: RouteCostMatrix, actions: Iterable[str]) -> float:
    total_cost = 0.0
    current_label = "START"

    for action in actions:
        total_cost += matrix.get_cost(current_label, action)
        current_label = action

    return total_cost


def _best_greedy_order(
    order_ids: list[str],
    matrix: RouteCostMatrix,
    reward_map: dict[str, float],
    current_label: str,
) -> str | None:
    if not order_ids:
        return None

    return max(
        order_ids,
        key=lambda order_id: (
            calculate_order_gain(matrix, reward_map, current_label, order_id),
            order_id,
        ),
    )


def _run_adversarial_search(
    algorithm: str,
    order_ids: list[str],
    orders,
    matrix: RouteCostMatrix,
    initial_state: AdversarialGameState | None = None,
):
    depth_limit = len(order_ids)

    if algorithm == "MINIMAX":
        return minimax_search(
            order_ids=order_ids,
            orders=orders,
            matrix=matrix,
            depth_limit=depth_limit,
            initial_state=initial_state,
        )
    if algorithm == "ALPHA_BETA":
        return alpha_beta_search(
            order_ids=order_ids,
            orders=orders,
            matrix=matrix,
            depth_limit=depth_limit,
            initial_state=initial_state,
        )
    if algorithm == "EXPECTIMAX":
        return expectimax_search(
            order_ids=order_ids,
            orders=orders,
            matrix=matrix,
            depth_limit=depth_limit,
            initial_state=initial_state,
        )

    raise ValueError(f"Unsupported adversarial algorithm: {algorithm}")


def _build_pathfinding_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    algorithm: str,
    visual_traps: tuple[GridPos, ...] = (),
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    map_data = load_auto_map(map_id)
    orders = load_orders_for_map(map_id)

    result = delivery_search(
        map_data=map_data,
        orders=orders,
        algorithm=algorithm,
        trap_cells=visual_traps,
    )

    note = "Delivery-state search"
    if not result.found:
        note = "Stopped before all orders"

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm=algorithm,
        actions=result.actions,
        path=result.path or [map_data.start_position],
        total_cost=result.cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note=note,
    )


def _build_local_search_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    algorithm: str,
    visual_traps: tuple[GridPos, ...] = (),
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    map_data = load_auto_map(map_id)
    orders = load_orders_for_map(map_id)

    result = delivery_search(
        map_data=map_data,
        orders=orders,
        algorithm=algorithm,
        trap_cells=visual_traps,
    )

    note = "Local path search by 4 directions"
    if not result.found or len(result.actions) < len(orders) * 2:
        note = "Stopped at local optimum"

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm=algorithm,
        actions=result.actions,
        path=result.path or [map_data.start_position],
        total_cost=result.cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note=note,
    )


def _build_complex_astar_plan(
    map_id: int,
    group_id: int,
    group_name: str,
    algorithm: str,
    visual_traps: tuple[GridPos, ...] = (),
) -> AutoVisualAgentPlan:
    started_at = perf_counter()
    map_data = load_auto_map(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]
    trap_setup = build_trap_setup(map_data, orders, algorithm)
    active_traps = tuple(visual_traps or trap_setup.traps)

    if algorithm == "NO_OBSERVATION":
        complex_result = no_observation_search(
            order_ids=order_ids,
            possible_traps=trap_setup.possible_traps,
            max_traps=len(trap_setup.traps),
        )
        astar_traps = union_belief_traps(complex_result.belief_states)
    elif algorithm == "PARTIAL_OBSERVATION":
        known_traps = trap_setup.traps[:2]
        complex_result = partial_observation_search(
            order_ids=order_ids,
            possible_traps=trap_setup.possible_traps,
            known_traps=known_traps,
            max_traps=len(trap_setup.traps),
        )
        astar_traps = union_belief_traps(complex_result.belief_states)
    else:
        complex_result = and_or_search(
            order_ids=order_ids,
            possible_traps=trap_setup.possible_traps,
            max_traps=len(trap_setup.traps),
        )
        astar_traps = union_belief_traps(complex_result.belief_states)

    alternative_paths: list[tuple[GridPos, ...]] = []
    alternative_actions: list[tuple[str, ...]] = []
    if algorithm == "AND_OR_SEARCH":
        for belief in complex_result.belief_states:
            alt_result = delivery_search(
                map_data=map_data,
                orders=orders,
                algorithm="ASTAR",
                trap_cells=active_traps,
            )
            if alt_result.path and len(alt_result.actions) == len(orders) * 2:
                alt_path = tuple(alt_result.path)
                alt_actions = tuple(alt_result.actions)
                if alt_path not in alternative_paths:
                    alternative_paths.append(alt_path)
                    alternative_actions.append(alt_actions)

    if algorithm == "AND_OR_SEARCH":
        contingency_sets = []

        for trap in trap_setup.traps:
            contingency_sets.append((trap,))

        for first_index in range(len(trap_setup.traps)):
            for second_index in range(first_index + 1, len(trap_setup.traps)):
                contingency_sets.append((
                    trap_setup.traps[first_index],
                    trap_setup.traps[second_index],
                ))

        contingency_sets.append(tuple(trap_setup.traps))

        for trap_cells in contingency_sets:
            alt_result = delivery_search(
                map_data=map_data,
                orders=orders,
                algorithm="ASTAR",
                trap_cells=active_traps,
            )
            if alt_result.path and len(alt_result.actions) == len(orders) * 2:
                alt_path = tuple(alt_result.path)
                alt_actions = tuple(alt_result.actions)
                if alt_path not in alternative_paths:
                    alternative_paths.append(alt_path)
                    alternative_actions.append(alt_actions)

    if algorithm == "AND_OR_SEARCH" and not alternative_paths:
        safe_result = delivery_search(
            map_data=map_data,
            orders=orders,
            algorithm="ASTAR",
            trap_cells=active_traps,
        )
        if safe_result.path and len(safe_result.actions) == len(orders) * 2:
            alternative_paths.append(tuple(safe_result.path))
            alternative_actions.append(tuple(safe_result.actions))

    result = delivery_search(
        map_data=map_data,
        orders=orders,
        algorithm="ASTAR",
        trap_cells=active_traps,
    )

    if algorithm == "AND_OR_SEARCH" and len(result.actions) == len(orders) * 2:
        main_path = tuple(result.path)
        if main_path not in alternative_paths:
            alternative_paths.append(main_path)
            alternative_actions.append(tuple(result.actions))

    if algorithm == "AND_OR_SEARCH" and alternative_paths:
        result.path = list(alternative_paths[0])
        result.actions = alternative_actions[0]

    if algorithm == "AND_OR_SEARCH":
        note = (
            f"{complex_result.risk_mode}, "
            f"cases={len(complex_result.belief_states)}, "
            f"plans={len(alternative_paths)}"
        )
    else:
        note = (
            f"{complex_result.risk_mode}, "
            f"belief={len(complex_result.belief_states)}, "
            f"A* né={len(astar_traps)} ô"
        )

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm=algorithm,
        actions=result.actions,
        path=result.path or [map_data.start_position],
        total_cost=result.cost,
        expanded_nodes=complex_result.expanded_nodes + result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note=note,
        hidden_traps=active_traps,
        belief_traps=astar_traps,
        belief_states=tuple(belief.traps for belief in complex_result.belief_states),
        known_traps=complex_result.known_traps,
        belief_count=len(complex_result.belief_states),
        alternative_paths=tuple(alternative_paths),
        alternative_actions=tuple(alternative_actions),
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

    result = _run_adversarial_search(
        algorithm=algorithm,
        order_ids=order_ids,
        orders=orders,
        matrix=matrix,
    )

    action_tuple = _actions_from_order_ids(result.best_sequence)

    return AutoVisualAgentPlan(
        group_id=group_id,
        group_name=group_name,
        algorithm=algorithm,
        actions=action_tuple,
        path=_node_path_from_actions(matrix, action_tuple),
        total_cost=_cost_from_actions(matrix, action_tuple),
        expanded_nodes=result.expanded_nodes,
        runtime_ms=(perf_counter() - started_at) * 1000,
        note=f"Utility={round(result.expected_utility, 2)}, pruned={result.pruned_nodes}",
    )


def _build_adversarial_duel_plans(
    map_id: int,
    group_id: int,
    group_name: str,
    matrix: RouteCostMatrix,
    algorithm: str = ADVERSARIAL_VISUAL_ALGORITHM,
) -> list[AutoVisualAgentPlan]:
    started_at = perf_counter()
    orders = load_orders_for_map(map_id)
    reward_map = build_reward_map(orders)
    remaining_order_ids = [order.id for order in orders]
    player_order_ids: list[str] = []
    opponent_order_ids: list[str] = []
    player_label = "START"
    opponent_label = "START"
    player_score = 0.0
    opponent_score = 0.0
    expanded_nodes = 0
    pruned_nodes = 0
    replans = 0

    while remaining_order_ids:
        state = AdversarialGameState(
            remaining_order_ids=tuple(remaining_order_ids),
            player_label=player_label,
            opponent_label=opponent_label,
            player_score=player_score,
            opponent_score=opponent_score,
            turn=PLAYER_TURN,
            depth=0,
        )
        result = _run_adversarial_search(
            algorithm=algorithm,
            order_ids=remaining_order_ids,
            orders=orders,
            matrix=matrix,
            initial_state=state,
        )
        expanded_nodes += result.expanded_nodes
        pruned_nodes += result.pruned_nodes
        replans += 1

        player_order_id = result.best_order_id
        if player_order_id not in remaining_order_ids:
            player_order_id = _best_greedy_order(
                remaining_order_ids,
                matrix,
                reward_map,
                player_label,
            )
        if player_order_id is None:
            break

        player_order_ids.append(player_order_id)
        player_score += calculate_order_gain(matrix, reward_map, player_label, player_order_id)
        player_label = f"D_{player_order_id}"
        remaining_order_ids.remove(player_order_id)

        opponent_order_id = _best_greedy_order(
            remaining_order_ids,
            matrix,
            reward_map,
            opponent_label,
        )
        if opponent_order_id is None:
            continue

        opponent_order_ids.append(opponent_order_id)
        opponent_score += calculate_order_gain(matrix, reward_map, opponent_label, opponent_order_id)
        opponent_label = f"D_{opponent_order_id}"
        remaining_order_ids.remove(opponent_order_id)

    runtime_ms = (perf_counter() - started_at) * 1000
    player_actions = _actions_from_order_ids(player_order_ids)
    opponent_actions = _actions_from_order_ids(opponent_order_ids)
    player_note = (
        f"vs GREEDY | score={round(player_score, 1)} | "
        f"opp={round(opponent_score, 1)} | replans={replans}"
    )
    opponent_note = (
        f"Greedy opponent | score={round(opponent_score, 1)} | "
        f"opp={round(player_score, 1)}"
    )

    return [
        AutoVisualAgentPlan(
            group_id=group_id,
            group_name=group_name,
            algorithm=algorithm,
            actions=player_actions,
            path=_node_path_from_actions(matrix, player_actions),
            total_cost=_cost_from_actions(matrix, player_actions),
            expanded_nodes=expanded_nodes,
            runtime_ms=runtime_ms,
            note=player_note,
        ),
        AutoVisualAgentPlan(
            group_id=group_id,
            group_name=group_name,
            algorithm=GREEDY_OPPONENT_ALGORITHM,
            actions=opponent_actions,
            path=_node_path_from_actions(matrix, opponent_actions),
            total_cost=_cost_from_actions(matrix, opponent_actions),
            expanded_nodes=len(opponent_order_ids),
            runtime_ms=0.0,
            note=opponent_note,
        ),
    ]


def build_auto_visual_plans(
    map_id: int,
    group_id: int = 1,
    visual_safe: bool = True,
    visual_traps: tuple[GridPos, ...] = (),
    adversarial_algorithm: str | None = None,
) -> list[AutoVisualAgentPlan]:
    group_id = int(group_id)
    algorithms = get_algorithms_by_group(group_id)

    if not algorithms:
        raise ValueError(f"Invalid visual group: {group_id}")

    group_name = get_group_name(group_id)
    if not visual_traps:
        map_data = load_auto_map(map_id)
        orders = load_orders_for_map(map_id)
        visual_traps = build_trap_setup(map_data, orders, "VISUAL").traps

    matrix = build_route_cost_matrix(map_id=map_id, algorithm="ASTAR", trap_cells=visual_traps)

    if group_id == 6:
        return _build_adversarial_duel_plans(
            map_id=map_id,
            group_id=group_id,
            group_name=group_name,
            matrix=matrix,
            algorithm=normalize_adversarial_visual_algorithm(adversarial_algorithm),
        )

    plans: list[AutoVisualAgentPlan] = []

    for algorithm in algorithms:
        if group_id in (1, 2):
            plans.append(_build_pathfinding_plan(map_id, group_id, group_name, algorithm, visual_traps))
        elif algorithm in ("SIMPLE_HILL", "STEEPEST_HILL", "LOCAL_BEAM"):
            plans.append(_build_local_search_plan(map_id, group_id, group_name, algorithm, visual_traps))
        elif algorithm in ("NO_OBSERVATION", "PARTIAL_OBSERVATION", "AND_OR_SEARCH"):
            plans.append(_build_complex_astar_plan(map_id, group_id, group_name, algorithm, visual_traps))
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
