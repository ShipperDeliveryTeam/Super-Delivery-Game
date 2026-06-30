"""Cac ham tim duong nho dung chung cho map grid.

Nhung ham nay de tranh viec cac file auto tu viet lai BFS/Dijkstra.
"""

from collections import deque
from heapq import heappop, heappush


def build_path(parent, goal):
    if goal not in parent:
        return []

    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()
    return path


def bfs_grid_path(start, goal, get_neighbors, blocked=None):
    """Tim duong ngan theo so buoc tren grid."""

    blocked = blocked or set()

    if start == goal:
        return [start]

    frontier = deque([start])
    parent = {start: None}

    while frontier:
        current = frontier.popleft()

        if current == goal:
            break

        for next_pos, _ in get_neighbors(current):
            next_pos = tuple(next_pos)

            if next_pos in blocked:
                continue

            if next_pos in parent:
                continue

            parent[next_pos] = current
            frontier.append(next_pos)

    return build_path(parent, goal)


def dijkstra_grid_path(start, goal, get_neighbors, blocked=None):
    """Tim duong co tong chi phi nho nhat tren grid."""

    blocked = blocked or set()

    if start == goal:
        return [start], 0.0

    frontier = []
    order = 0
    heappush(frontier, (0.0, order, start))

    parent = {start: None}
    cost = {start: 0.0}

    while frontier:
        current_cost, _, current = heappop(frontier)

        if current == goal:
            break

        if current_cost > cost.get(current, float("inf")):
            continue

        for next_pos, step_cost in get_neighbors(current):
            next_pos = tuple(next_pos)

            if next_pos in blocked:
                continue

            new_cost = current_cost + step_cost

            if new_cost >= cost.get(next_pos, float("inf")):
                continue

            cost[next_pos] = new_cost
            parent[next_pos] = current
            order += 1
            heappush(frontier, (new_cost, order, next_pos))

    return build_path(parent, goal), cost.get(goal, float("inf"))
