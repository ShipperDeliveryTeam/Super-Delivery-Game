class Node:
    def __init__(self, state, parent=None, cost=0):
        self.state = state  # state = ((r, c), tuple_of_orders)
        self.parent = parent
        self.cost = cost

    @property
    def position(self):
        return self.state[0]

    @property
    def goals(self):
        return self.state[1]

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.state == other.state

    def __hash__(self):
        return hash(self.state)

def normalize_orders(orders):
    return tuple(sorted(orders))

def get_neighbors(state, grid):
    (r, c), orders = state
    neighbors = []

    directions = [
        (-1, 0),  # Lên
        (1, 0),   # Xuống
        (0, -1),  # Trái
        (0, 1)    # Phải
    ]

    for dr, dc in directions:
        nr, nc = r + dr, c + dc

        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]):
            if grid[nr][nc] != '#':
                new_pos = (nr, nc)
                # Nếu đi vào ô có nhà đặt đơn (đích) thì giao đơn đó
                new_orders = tuple(o for o in orders if o != new_pos)
                neighbors.append((new_pos, new_orders))

    return neighbors

def reconstruct_path(node):
    path = []
    while node:
        path.append(node.state[0])
        node = node.parent
    return path[::-1]

def is_in_frontier(state, frontier):
    return any(node.state == state for node in frontier)