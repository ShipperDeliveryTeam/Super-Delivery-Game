class Node:
    def __init__(self, state, parent=None, cost = 0):
        self.state = state  # state = ((x, y), tuple_of_dirties)
        self.parent = parent
        self.cost = cost

    def __eq__(self, other):
        return self.state == other.state

    def __hash__(self):
        return hash(self.state)