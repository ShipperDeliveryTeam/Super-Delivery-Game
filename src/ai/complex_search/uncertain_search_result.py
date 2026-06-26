from __future__ import annotations

from dataclasses import dataclass

from src.ai.local_search.route_state import RouteState


@dataclass
class UncertainSearchResult:
    algorithm: str
    best_state: RouteState
    decision_cost: float
    risk_mode: str
    iterations: int
    expanded_nodes: int
    generated_nodes: int
    runtime_ms: float

    @property
    def normal_cost(self) -> float:
        return self.best_state.total_cost

    @property
    def actions(self) -> tuple[str, ...]:
        return self.best_state.actions