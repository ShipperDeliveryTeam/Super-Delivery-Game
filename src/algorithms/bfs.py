from collections import deque

def bfs(grid, start, end):
    """
    Breadth-First Search on a 2D grid.
    
    :param grid: 2D list of strings representing the map.
    :param start: (row, col) tuple of the starting position.
    :param end: (row, col) tuple of the destination position.
    :return: A list of (row, col) tuples representing the shortest path, or None if no path exists.
             Also returns the set of visited nodes for visualization purposes.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    
    queue = deque([start])
    visited = set()
    visited.add(start)
    
    # Store the parent of each node to reconstruct the path later
    parent = {start: None}
    
    # Define directions: Up, Down, Left, Right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # Optional: order to visit (in a game, checking straight directions first is normal)
    
    path_found = False
    
    while queue:
        current = queue.popleft()
        
        if current == end:
            path_found = True
            break
            
        r, c = current
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            
            # Check bounds
            if 0 <= nr < rows and 0 <= nc < cols:
                # Check if it's traversable and not visited
                if grid[nr][nc] != '#' and (nr, nc) not in visited:
                    queue.append((nr, nc))
                    visited.add((nr, nc))
                    parent[(nr, nc)] = current

    path = []
    if path_found:
        curr = end
        while curr is not None:
            path.append(curr)
            curr = parent[curr]
        path.reverse()  # Reverse to get path from start to end
        return path, visited
        
    return None, visited
