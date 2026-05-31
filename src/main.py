import os
import sys

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.game import Game

def main():
    # Provide the path to the map file
    map_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'maps', 'map1.txt')
    
    # Check if map file exists
    if not os.path.exists(map_file_path):
        print(f"Error: Map file not found at {map_file_path}")
        sys.exit(1)
        
    game = Game(map_file_path)
    game.run()

if __name__ == "__main__":
    main()
