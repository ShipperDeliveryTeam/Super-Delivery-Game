from __future__ import annotations  # Cho phep ghi type hint gon hon trong Python.

"""No Observation.

Y tuong:
1. Tao 2 belief state. Moi belief la mot du doan rieng ve vi tri bay.
2. Moi belief tu chay A* rieng bang tap bay cua no.
3. Auto chon ngau nhien 1 belief de mo phong.
"""

import random  #
from dataclasses import dataclass  
from time import perf_counter 


GridPos = tuple[int, int]  # Kieu toa do tren grid: (x, y).


@dataclass  
class BeliefState:
    name: str  # Ten belief, vi du B1 hoac B2.
    traps: tuple[GridPos, ...]  # Tap bay ma belief nay dang du doan.


@dataclass  
class ComplexSearchResult:
    algorithm: str  # Ten thuat toan, vi du NO_OBSERVATION.
    actions: tuple[str, ...]  # Cac hanh dong giao hang
    normal_cost: float  # Chi phi cua duong di tren belief duoc chon.
    decision_cost: float  # O day bang normal_cost, khong cong them rui ro.
    risk_mode: str  # Mo ta cach mo phong bat dinh.
    belief_states: tuple[BeliefState, ...]  # Tat ca belief duoc tao ra.
    known_traps: tuple[GridPos, ...]  # Cac bay biet truoc, no observation se rong.
    iterations: int  # So belief da xet.
    expanded_nodes: int  # Tong so node A* da mo rong.
    generated_nodes: int  # Tong so node A* da sinh.
    runtime_ms: float  # Thoi gian chay tinh bang mili giay.
    belief_paths: tuple[tuple[GridPos, ...], ...] = ()  # Duong di rieng cua tung belief.
    belief_actions: tuple[tuple[str, ...], ...] = ()  # Actions rieng cua tung belief.
    belief_costs: tuple[float, ...] = ()  # Cost rieng cua tung belief.
    selected_belief_index: int = 0  # Belief nao duoc chon de auto mo phong.
    selected_traps: tuple[GridPos, ...] = ()  # Tap bay cua belief duoc chon.
    failed_on_trap: GridPos | None = None  # O bay that dau tien nam tren path, neu co.
    success: bool = True  # Co tim duoc actions hay khong.


def unique_positions(positions) -> list[GridPos]: 
    result = []  # Tao danh sach ket qua khong trung lap.
    for pos in positions:  # Duyet tung toa do dau vao.
        pos = tuple(pos)  # Chuyen pos ve tuple de dong nhat dang (x, y).
        if pos not in result:  # Neu toa do nay chua co trong ket qua.
            result.append(pos)  # Them toa do vao ket qua.
    return result  # Tra ve danh sach da loai trung.


def make_belief_states(candidate_cells, known_traps=(), max_traps=None, unknown_count=None):
    known_traps = tuple(unique_positions(known_traps))  # Loai trung bay da biet.
    candidate_cells = unique_positions(candidate_cells)  # Loai trung danh sach o ung vien.
    candidate_cells = [cell for cell in candidate_cells if cell not in known_traps]  # Khong doan lai bay da biet.

    if not candidate_cells and not known_traps:  # Neu khong co o nao de doan.
        return (BeliefState("B1", tuple()), BeliefState("B2", tuple()))  # Tao 2 belief rong.

    if max_traps is None:  # Neu khong truyen so bay toi da.
        max_count = min(3, len(candidate_cells) + len(known_traps))  # Gioi han mac dinh la 3 bay.
    else:  # Neu co truyen so bay toi da.
        max_count = min(max_traps, len(candidate_cells) + len(known_traps))  # Khong vuot qua so o co the.
    max_count = max(1, max_count)  # Dam bao moi belief co it nhat 1 bay neu co the.

    beliefs = []  # Danh sach 2 belief se tao.

    for index in range(2):  # Tao dung 2 belief: B1 va B2.
        traps = list(known_traps)  # Moi belief bat dau bang cac bay da biet.
        candidates = list(candidate_cells)  # Sao chep danh sach o ung vien.
        random.shuffle(candidates)  # Tron ngau nhien de moi belief doan khac nhau.

        if unknown_count is None:  # No observation: khong biet chinh xac so bay.
            if index == 0:  # Belief dau tien doan it bay.
                target_count = max(1, len(known_traps))  # So bay muc tieu cua B1.
            else:  # Belief thu hai doan nhieu bay hon.
                target_count = max_count  # So bay muc tieu cua B2.
            need_more = max(0, target_count - len(traps))  # So bay can doan them.
        else:  # Partial observation: biet can doan them bao nhieu bay.
            need_more = max(0, unknown_count)  # Lay dung so bay can doan them.

        for trap in candidates:  # Duyet cac bay ung vien sau khi da tron.
            if need_more <= 0:  # Neu da du so bay can doan.
                break  # Dung them bay vao belief.
            traps.append(trap)  # Them bay nay vao belief.
            need_more -= 1  # Giam so bay con can them.

        beliefs.append(BeliefState(f"B{index + 1}", tuple(traps)))  # Luu belief vua tao.

    return tuple(beliefs)  # Tra ve 2 belief.


def run_astar_for_each_belief(map_data, orders, belief_states):
    from src.ai.pathfinding.delivery_search import delivery_search  # Import trong ham de tranh vong import.

    paths = []  # Luu path A* cua tung belief.
    actions = []  # Luu actions A* cua tung belief.
    costs = []  # Luu cost A* cua tung belief.
    expanded = 0  # Tong node da mo rong.
    generated = 0  # Tong node da sinh.

    for belief in belief_states:  # Moi belief chay A* rieng.
        result = delivery_search(  # Goi bai toan giao hang tong quat bang A*.
            map_data=map_data,  # Ban do auto.
            orders=orders,  # Danh sach don hang.
            algorithm="ASTAR",  # Dung A* de tim duong.
            trap_cells=belief.traps,  # A* chi thay tap bay cua belief nay.
        )

        paths.append(tuple(result.path))  # Luu path cua belief nay.
        actions.append(tuple(result.actions))  # Luu actions cua belief nay.
        costs.append(result.cost)  # Luu cost cua belief nay.
        expanded += result.expanded_nodes  # Cong so node mo rong.
        generated += result.generated_nodes  # Cong so node sinh ra.

    return tuple(paths), tuple(actions), tuple(costs), expanded, generated  # Tra ve toan bo ket qua.


def build_candidate_cells(map_data, orders):
    blocked = {map_data.start_position}  # Khong doan bay o vi tri xuat phat.
    for order in orders:  # Duyet tat ca don hang.
        blocked.add(order.store_pos)  # Khong dat bay vao shop.
        blocked.add(order.customer_pos)  # Khong dat bay vao nha giao.

    cells = []  # Danh sach o ma thuat toan co the doan la bay.
    for y in range(map_data.height):  # Duyet tung dong cua map.
        for x in range(map_data.width):  # Duyet tung cot cua map.
            pos = (x, y)  # Tao toa do hien tai.
            if pos in blocked:  # Bo qua start/shop/nha.
                continue
            if map_data.is_walkable(pos):  # Chi doan tren o co the di qua.
                cells.append(pos)
    return cells  # Tra ve tat ca o ung vien.


def first_trap_on_path(path, true_traps):
    true_traps = {tuple(pos) for pos in true_traps}  # Chuyen bay that sang set de tim nhanh.
    for pos in path:  # Duyet tung o tren duong di.
        if tuple(pos) in true_traps:  # Neu o nay la bay that.
            return tuple(pos)  # Tra ve bay dau tien bi di qua.
    return None  # Neu path khong di qua bay that nao.


def make_result(
    algorithm,
    order_ids,
    risk_mode,
    belief_states,
    known_traps,
    started_at,
    map_data=None,
    orders=None,
    true_traps=(),
):
    selected_index = random.randrange(len(belief_states)) if belief_states else 0  # Random belief de mo phong.
    selected_traps = belief_states[selected_index].traps if belief_states else tuple()  # Lay bay cua belief da chon.

    paths = tuple()  # Mac dinh chua co path.
    actions = tuple()  # Mac dinh chua co actions.
    costs = tuple()  # Mac dinh chua co cost.
    expanded = 0  # Mac dinh chua mo rong node nao.
    generated = 0  # Mac dinh chua sinh node nao.

    if map_data is not None and orders is not None:  # Neu co du du lieu ban do va don hang.
        paths, actions, costs, expanded, generated = run_astar_for_each_belief(  # Chay A* cho tung belief.
            map_data,  # Ban do auto.
            orders,  # Danh sach don hang.
            belief_states,  # Danh sach belief.
        )

    if actions:  # Neu A* da tra ve actions.
        selected_actions = actions[selected_index]  # Lay actions cua belief duoc chon.
    else:  # Neu khong chay A*.
        selected_actions = tuple()  # Khong tu tao actions gia.

    if costs:  # Neu A* da tra ve cost.
        selected_cost = costs[selected_index]  # Lay cost cua belief duoc chon.
    else:  # Neu khong co cost.
        selected_cost = 0.0  # Cost mac dinh la 0.

    trap_hit = None  # Mac dinh la khong di qua bay that.
    if paths and true_traps:  # Neu co path va co tap bay that.
        trap_hit = first_trap_on_path(paths[selected_index], true_traps)  # Tim bay that dau tien tren path.

    return ComplexSearchResult(  # Dong goi ket qua tra ve.
        algorithm=algorithm,  # Ten thuat toan.
        actions=selected_actions,  # Actions cua belief duoc chon.
        normal_cost=selected_cost,  # Cost cua belief duoc chon.
        decision_cost=selected_cost,  # Khong cong them cost rui ro.
        risk_mode=risk_mode,  # Mo ta che do uncertainty.
        belief_states=belief_states,  # Tat ca belief.
        known_traps=tuple(known_traps),  # Bay da biet.
        iterations=len(belief_states),  # So belief da xu ly.
        expanded_nodes=len(belief_states) + expanded,  # So node mo rong.
        generated_nodes=len(belief_states) * max(1, len(order_ids)) + generated,  # So node sinh ra.
        runtime_ms=(perf_counter() - started_at) * 1000,  # Thoi gian chay.
        belief_paths=paths,  # Path cua tung belief.
        belief_actions=actions,  # Actions cua tung belief.
        belief_costs=costs,  # Cost cua tung belief.
        selected_belief_index=selected_index,  # Belief duoc chon.
        selected_traps=selected_traps,  # Tap bay belief duoc chon.
        failed_on_trap=trap_hit,  # Bay that bi di qua neu co.
        success=bool(selected_actions),  # True neu co actions.
    )


def no_observation_search(
    order_ids,
    capacity=1,
    max_traps=None,
    map_data=None,
    orders=None,
    true_traps=(),
):
    started_at = perf_counter()  # Bat dau do thoi gian.
    if map_data is not None and orders is not None:  # Neu co ban do va don hang.
        candidate_cells = build_candidate_cells(map_data, orders)  # Tu lay cac o ung vien trong map.
    else:  # Truong hop thieu du lieu map.
        candidate_cells = []  # Khong co o nao de doan.

    belief_states = make_belief_states(candidate_cells, max_traps=max_traps)  # Tao 2 belief random tu o ung vien.

    return make_result(  # Tao ket qua cuoi cung.
        algorithm="NO_OBSERVATION",  # Ten thuat toan.
        order_ids=list(order_ids),  # Danh sach id don hang.
        risk_mode="TWO_UNKNOWN_BELIEFS",  # Mo ta co 2 belief chua biet bay.
        belief_states=belief_states,  # 2 belief vua tao.
        known_traps=(),  # No observation khong biet truoc bay nao.
        started_at=started_at,  # Moc thoi gian bat dau.
        map_data=map_data,  # Ban do auto.
        orders=orders,  # Don hang auto.
        true_traps=true_traps,  # Bay that dung de mo phong va hien thi.
    )
