from collections import deque
from .common import Node, normalize_orders, get_neighbors, reconstruct_path, is_in_frontier

def bfs(grid, start, end):
    orders = normalize_orders((end,))
    start_state = (start, orders)
    start_node = Node(start_state)
    
    if len(orders) == 0:
        yield start_node, [], set()
        return

    frontier = deque([start_node])
    explored = set()

    while frontier:
        current_node = frontier.popleft()
        
        yield current_node, frontier, explored
        
        if len(current_node.state[1]) == 0:
            return

        explored.add(current_node.state)

        for next_state in get_neighbors(current_node.state, grid):
            child_node = Node(next_state, current_node, current_node.cost + 1)
            
            if child_node.state not in explored and not is_in_frontier(child_node.state, frontier):
                if len(child_node.state[1]) == 0:
                    yield child_node, frontier, explored
                    return
                frontier.append(child_node)

    yield None, frontier, explored
