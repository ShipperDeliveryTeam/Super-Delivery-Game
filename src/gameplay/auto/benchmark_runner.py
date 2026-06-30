from __future__ import annotations

from src.gameplay.auto.algorithm_groups import (
    get_algorithms_by_group,
    get_group_name,
)
from src.gameplay.auto.config import get_auto_map_config
from src.gameplay.auto.complex_traps import build_trap_setup
from src.gameplay.auto.models import AutoModeType, RunResult
from src.ai.pathfinding.delivery_search import delivery_search
from src.gameplay.auto.order_factory import load_orders_for_map
from src.gameplay.auto.maps.tmx_loader import load_auto_map
from src.gameplay.auto.planner import build_plan_for_map
from src.gameplay.auto.route_cost_matrix import build_route_cost_matrix
from src.gameplay.auto.scoring import apply_benchmark_rank_bonus
from src.ai.pathfinding.complex_search.and_or_graph import and_or_search
from src.ai.pathfinding.complex_search.no_observation import no_observation_search
from src.ai.pathfinding.complex_search.partial_observation import partial_observation_search
from src.ai.pathfinding.csp.ac3_backtracking import ac3_backtracking_search
from src.ai.pathfinding.csp.backtracking import backtracking_search
from src.ai.pathfinding.csp.forward_checking import forward_checking_search
from src.ai.pathfinding.adversarial.alpha_beta import alpha_beta_search
from src.ai.pathfinding.adversarial.expectimax import expectimax_search
from src.ai.pathfinding.adversarial.minimax import minimax_search

def _estimate_score(
    completed_orders: int,
    total_cost: float,
    success: bool,
) -> float:
    base_score = completed_orders * 100

    if not success:
        base_score *= 0.5

    cost_penalty = total_cost * 0.2

    return max(0.0, round(base_score - cost_penalty, 2))


def _build_run_result(
    map_id: int,
    group_id: int,
    algorithm: str,
    total_orders: int,
    completed_orders: int,
    total_cost: float,
    expanded_nodes: int,
    runtime_ms: float,
    success: bool,
) -> RunResult:
    score = _estimate_score(
        completed_orders=completed_orders,
        total_cost=total_cost,
        success=success,
    )

    return RunResult(
        map_id=map_id,
        mode=AutoModeType.BENCHMARK,
        algorithm_group=group_id,
        algorithm=algorithm,
        shipper_name=f"AI_{algorithm}",
        completed_orders=completed_orders,
        on_time_orders=completed_orders if success else 0,
        late_orders=0 if success else max(0, total_orders - completed_orders),
        total_score=score,
        total_distance=total_cost,
        finish_time=total_cost,
        expanded_nodes=expanded_nodes,
        runtime_ms=runtime_ms,
        memory_kb=0.0,
        replan_count=0,
        trap_hits=0,
        total_orders=total_orders,
    )


def run_pathfinding_benchmark_algorithm(
    map_id: int,
    group_id: int,
    algorithm: str,
) -> RunResult:
    plan_result = build_plan_for_map(
        map_id=map_id,
        algorithm=algorithm,
    )

    return _build_run_result(
        map_id=map_id,
        group_id=group_id,
        algorithm=algorithm,
        total_orders=plan_result.total_orders,
        completed_orders=plan_result.completed_orders,
        total_cost=plan_result.total_cost,
        expanded_nodes=plan_result.expanded_nodes,
        runtime_ms=plan_result.runtime_ms,
        success=plan_result.success,
    )


def run_local_search_benchmark_algorithm(
    map_id: int,
    group_id: int,
    algorithm: str,
) -> RunResult:
    map_data = load_auto_map(map_id)
    orders = load_orders_for_map(map_id)

    result = delivery_search(
        map_data=map_data,
        orders=orders,
        algorithm=algorithm,
    )

    completed_orders = sum(1 for action in result.actions if action.startswith("D_"))

    return _build_run_result(
        map_id=map_id,
        group_id=group_id,
        algorithm=algorithm,
        total_orders=len(orders),
        completed_orders=completed_orders,
        total_cost=result.cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=result.runtime_ms,
        success=completed_orders == len(orders),
    )

def run_complex_search_benchmark_algorithm(
    map_id: int,
    group_id: int,
    algorithm: str,
) -> RunResult:
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    map_data = load_auto_map(map_id)
    trap_setup = build_trap_setup(map_data, orders, algorithm)
    max_traps = len(trap_setup.traps)

    if algorithm == "NO_OBSERVATION":
        result = no_observation_search(
            order_ids=order_ids,
            capacity=config.capacity,
            max_traps=max_traps,
            map_data=map_data,
            orders=orders,
            true_traps=trap_setup.traps,
        )

    elif algorithm == "PARTIAL_OBSERVATION":
        result = partial_observation_search(
            order_ids=order_ids,
            possible_traps=trap_setup.possible_traps,
            known_traps=trap_setup.traps[:1],
            capacity=config.capacity,
            max_iterations=100,
            max_traps=max_traps,
            map_data=map_data,
            orders=orders,
            true_traps=trap_setup.traps,
        )

    elif algorithm == "AND_OR_SEARCH":
        result = and_or_search(
            order_ids=order_ids,
            possible_traps=trap_setup.possible_traps,
            capacity=config.capacity,
            beam_width=5,
            max_iterations=100,
            seed=42,
            max_traps=max_traps,
        )

    else:
        raise ValueError(f"Unsupported complex search algorithm: {algorithm}")

    success = bool(getattr(result, "success", True))
    completed_orders = len(orders) if success else 0

    return _build_run_result(
        map_id=map_id,
        group_id=group_id,
        algorithm=algorithm,
        total_orders=len(orders),
        completed_orders=completed_orders,
        total_cost=result.normal_cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=result.runtime_ms,
        success=success,
    )
    
def run_csp_benchmark_algorithm(
    map_id: int,
    group_id: int,
    algorithm: str,
) -> RunResult:
    config = get_auto_map_config(map_id)
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    matrix = build_route_cost_matrix(
        map_id=map_id,
        algorithm="ASTAR",
    )

    if algorithm == "BACKTRACKING":
        result = backtracking_search(
            order_ids=order_ids,
            capacity=config.capacity,
            cost_provider=matrix,
            max_expanded_nodes=10000,
        )

    elif algorithm == "FORWARD_CHECKING":
        result = forward_checking_search(
            order_ids=order_ids,
            capacity=config.capacity,
            cost_provider=matrix,
            max_expanded_nodes=15000,
        )

    elif algorithm == "AC3_BACKTRACKING":
        result = ac3_backtracking_search(
            order_ids=order_ids,
            capacity=config.capacity,
            cost_provider=matrix,
            max_expanded_nodes=20000,
        )

    else:
        raise ValueError(f"Unsupported CSP algorithm: {algorithm}")

    return _build_run_result(
        map_id=map_id,
        group_id=group_id,
        algorithm=algorithm,
        total_orders=len(orders),
        completed_orders=len(orders),
        total_cost=result.best_state.total_cost,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=result.runtime_ms,
        success=True,
    )    
    
def run_adversarial_benchmark_algorithm(
    map_id: int,
    group_id: int,
    algorithm: str,
) -> RunResult:
    orders = load_orders_for_map(map_id)
    order_ids = [order.id for order in orders]

    matrix = build_route_cost_matrix(
        map_id=map_id,
        algorithm="ASTAR",
    )

    depth_limit = len(order_ids)

    if algorithm == "MINIMAX":
        result = minimax_search(
            order_ids=order_ids,
            orders=orders,
            matrix=matrix,
            depth_limit=depth_limit,
        )

    elif algorithm == "ALPHA_BETA":
        result = alpha_beta_search(
            order_ids=order_ids,
            orders=orders,
            matrix=matrix,
            depth_limit=depth_limit,
        )

    elif algorithm == "EXPECTIMAX":
        result = expectimax_search(
            order_ids=order_ids,
            orders=orders,
            matrix=matrix,
            depth_limit=depth_limit,
        )

    else:
        raise ValueError(f"Unsupported adversarial algorithm: {algorithm}")

    # Group 6 is a competition decision model, so convert its utility into benchmark score.
    total_score = max(0.0, round(300.0 + result.expected_utility, 2))

    run_result = RunResult(
        map_id=map_id,
        mode=AutoModeType.BENCHMARK,
        algorithm_group=group_id,
        algorithm=algorithm,
        shipper_name=f"AI_{algorithm}",
        completed_orders=len(orders),
        on_time_orders=len(orders),
        late_orders=0,
        total_score=total_score,
        total_distance=0.0,
        finish_time=0.0,
        expanded_nodes=result.expanded_nodes,
        runtime_ms=result.runtime_ms,
        memory_kb=0.0,
        replan_count=result.pruned_nodes,
        trap_hits=0,
        total_orders=len(orders),
    )

    return run_result

def run_benchmark_for_algorithms(
    map_id: int,
    group_id: int,
    algorithms: list[str],
) -> list[RunResult]:
    results: list[RunResult] = []

    for algorithm in algorithms:
        if group_id in (1, 2):
            result = run_pathfinding_benchmark_algorithm(
                map_id=map_id,
                group_id=group_id,
                algorithm=algorithm,
            )
        elif group_id == 3:
            result = run_local_search_benchmark_algorithm(
                map_id=map_id,
                group_id=group_id,
                algorithm=algorithm,
            )
        elif group_id == 4:
            result = run_complex_search_benchmark_algorithm(
                map_id=map_id,
                group_id=group_id,
                algorithm=algorithm,
            )
        elif group_id == 5:
            result = run_csp_benchmark_algorithm(
                map_id=map_id,
                group_id=group_id,
                algorithm=algorithm,
            )
        elif group_id == 6:
            result = run_adversarial_benchmark_algorithm(
                map_id=map_id,
                group_id=group_id,
                algorithm=algorithm,
            )
        else:
            raise ValueError(f"Benchmark for group {group_id} is not implemented yet.")

        results.append(result)

    return apply_benchmark_rank_bonus(results)


def run_benchmark_group(
    map_id: int,
    group_id: int,
) -> list[RunResult]:
    algorithms = get_algorithms_by_group(group_id)

    if not algorithms:
        raise ValueError(f"Invalid algorithm group: {group_id}")

    return run_benchmark_for_algorithms(
        map_id=map_id,
        group_id=group_id,
        algorithms=algorithms,
    )


def print_benchmark_group(
    map_id: int,
    group_id: int,
) -> None:
    group_name = get_group_name(group_id)
    results = run_benchmark_group(map_id, group_id)

    print(f"Benchmark Map {map_id} - Group {group_id}: {group_name}")

    for result in results:
        total_orders = result.total_orders or len(load_orders_for_map(map_id))
        status = "OK" if result.completed_orders >= total_orders else "FAILED"

        print(
            f"#{result.rank} {result.algorithm}: {status}, "
            f"completed={result.completed_orders}/{total_orders}, "
            f"score={result.total_score}, "
            f"distance={round(result.total_distance, 2)}, "
            f"expanded={result.expanded_nodes}, "
            f"runtime_ms={round(result.runtime_ms, 4)}"
        )

    print("-" * 80)


if __name__ == "__main__":
    for current_map_id in (1, 2, 3):
        for current_group_id in (1, 2, 3, 4, 5, 6):
            print_benchmark_group(
                map_id=current_map_id,
                group_id=current_group_id,
            )
