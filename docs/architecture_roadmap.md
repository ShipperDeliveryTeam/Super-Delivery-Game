# Roadmap kiến trúc Super Delivery Game

## Gameplay

- `src/gameplay/play/`: người chơi điều khiển shipper, nhận đơn, giao đúng hạn,
  nhận thưởng và chịu phạt bởi chướng ngại.
- `src/gameplay/auto/`: NPC cạnh tranh, player tự động và chế độ mô phỏng.
- `delivery_manager.py`, `order_manager.py`, `score_manager.py`,
  `win_condition.py`: luật dùng chung và các điểm mở rộng tiếp theo.

## Ứng dụng Maps và AI

- `src/ai/game_pathfinder.py`: facade tìm đường mà game đang sử dụng.
- `src/ai/pathfinding/`: đích đến cho BFS, DFS, UCS, A*, Greedy, IDS, Beam và
  tìm kiếm trong môi trường quan sát một phần. Thuật toán trong package này
  không được phụ thuộc Pygame.
- `src/ai/local_search/`: lựa chọn cửa hàng, tối ưu chuỗi đơn và tuyến nhiều điểm.
- `src/ai/reinforcement/`: Q-learning và lưu/đọc Q-table.
- Tìm kiếm ràng buộc sẽ dùng để phân đơn, giới hạn thời gian, tải trọng và tránh
  nhiều shipper tranh cùng một nhiệm vụ.

## Map và độ khó

- `src/maps/`: tile, grid, collision, TMX và chuyển đổi map thành đồ thị tìm đường.
- Dễ: đường cơ bản và ít chướng ngại.
- Trung bình: cầu, vòng xuyến và ổ voi.
- Trung bình khó: tắc đường, đường thi công và chi phí cạnh thay đổi.
- Khó: mưa/lụt, quan sát một phần và thay đổi map theo thời gian.

Các hiện tượng môi trường nên cập nhật chi phí/khả năng đi qua của grid; không
được viết trực tiếp vào thuật toán tìm kiếm hoặc renderer.

## Thực thể và trình bày

- `src/entities/`: Player, NPC, Customer, Store, Order, Trap và shipper sprite.
- `src/systems/`: animation, camera, âm thanh, tài nguyên và thống kê.
- `src/ui/`: menu, HUD, gameplay renderer, popup, result và viewport.

Quy tắc phụ thuộc: AI và model không import UI/Pygame; UI chỉ đọc trạng thái;
Play và Auto dùng chung movement/delivery nhưng không import lẫn nhau.
