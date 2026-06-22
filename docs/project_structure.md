# Bản đồ cấu trúc dự án

Tài liệu này mô tả cấu trúc đang thực sự được sử dụng. Nhiều file rỗng trong
`src/` là khung dành cho phát triển sau này; chúng chưa tham gia vào luồng chạy.

## Luồng chạy chính

1. `game.py` đọc tham số dòng lệnh và tạo `GameSettings`.
2. `src/core/game_manager.py` khởi tạo Pygame, tải map/tài nguyên và chạy game loop.
3. `src/maps/` chuyển dữ liệu TMX hoặc ảnh map thành dữ liệu đường đi/va chạm.
4. `src/ai/game_pathfinder.py` tìm đường cho shipper theo thuật toán được chọn.
5. `src/gameplay/` tạo và quản lý nhiệm vụ nhận/giao đơn.
6. `src/systems/stats_logger.py` ghi kết quả ván chơi vào `stats.csv`.

## Thư mục và file gốc

- `game.py`: entry point duy nhất để chạy game; hỗ trợ `--map`, `--algorithm`, `--debug`.
- `requirements.txt`: thư viện cần cài. Pygame chạy game; Matplotlib tạo biểu đồ.
- `README.md`: hướng dẫn cài đặt, chạy, test và tổng quan kiến trúc.
- `stats.csv`: dữ liệu sinh trong lúc chơi, không phải mã nguồn.
- `out.log`: log chạy cục bộ; có thể xóa và không nên commit.
- `information`: file rỗng, hiện không có chức năng.
- `scratch_fix.py`: script sửa tạm, không thuộc luồng chạy chính.

## `src/` — mã nguồn

### `src/core/`

- `game_manager.py`: composition root; khởi tạo dịch vụ và chạy game loop. Logic
  command/update/render đã được chuyển sang các module chuyên trách.
- `command_handler.py`: xử lý `GameCommand` và gọi hành động tương ứng.
- `state_updater.py`: cập nhật timer và gameplay theo `GameState`.
- `settings.py`: cấu hình runtime, map và thuật toán đang chọn.
- `constants.py`: kích thước, màu sắc, loại tile và tên thuật toán.
- `event_handler.py`: đổi sự kiện Pygame thành command của game.
- `game_state.py`: enum các trạng thái/màn hình.

### `src/ai/`

- `game_pathfinder.py`: API tìm đường game đang dùng; triển khai các thuật toán và luật di chuyển liên quan vòng xuyến.
- `local_search/store_selector.py`: chấm điểm/chọn cửa hàng khi sinh đơn.
- `pathfinding/`, `reinforcement/`, `ai_controller.py`: khung phát triển, hiện rỗng.

### `src/gameplay/`

- `delivery_task.py`: mô hình dữ liệu của một nhiệm vụ giao hàng.
- `order_generator.py`: sinh đơn và phối hợp `StoreSelector`.
- `roundabout_geometry.py`: dựng/nội suy đường cong để xe chạy mượt qua vòng xuyến.
- `player_controller.py`: input, tự động tìm đường và cập nhật player.
- `npc_controller.py`: cập nhật đường đi, nhiệm vụ và chuyển động NPC.
- `movement_service.py`: thao tác di chuyển dùng chung cho các shipper.
- `delivery_manager.py`: tạo và kiểm tra khả năng tiếp cận nhiệm vụ.
- `game_flow.py`: reset ván chơi, thắng/thua và ghi thống kê.
- `gameplay_controller.py`: tạo player/NPC từ dữ liệu spawn và sprite.

### `src/maps/`

- `tmx_loader.py`: đọc XML/TMX của Tiled, layer, object và collision.
- `matrix_loader.py`: tạo/đọc ma trận ô đi được phục vụ tìm đường.
- `map_manager.py`: điều phối TMX/CSV/PNG, tọa độ, spawn và cấu hình vòng xuyến.

### `src/entities/`

- `directional_shipper.py`: sprite theo hướng, animation và chuyển động trên đường.
- Các file entity khác đang rỗng; logic tương ứng hiện nằm trong `GameManager`.

### `src/systems/`

- `asset_manager.py`: tải ảnh nền, UI, icon và sprite cho một phiên game.
- `asset_paths.py`: quy ước và tìm đường dẫn tài nguyên.
- `sprite_loader.py`: tải, scale và cache sprite Pygame.
- `stats_logger.py`: ghi một ván chơi thành một dòng CSV.
- `stats_analyzer.py`: tổng hợp CSV và tạo báo cáo/biểu đồ.
- `animation.py`, `camera.py`, `sound_manager.py`: file đặt chỗ cho phát triển sau.

### Các thư mục còn lại trong `src/`

- `algorithms/`: khung thuật toán cũ; game hiện gọi `src/ai/game_pathfinder.py`.
- `ui/`: các mixin trình bày đã được tách thành menu, button, popup, gameplay
  renderer, HUD, pause, result, text và viewport letterbox.
- `utils/`: khung tiện ích, hiện rỗng.
- `scripts/`: khung cũ; công cụ thật nằm ở `scripts/` cấp dự án.

## Dữ liệu và công cụ

- `assets/characters/`: sprite player và NPC theo bốn hướng.
- `assets/icons/`: icon nút điều khiển, vị trí, tiền và bẫy.
- `assets/images/map/`: ảnh map được game hiển thị.
- `assets/sounds/`, `assets/ui/`, `assets/fonts/`: âm thanh, giao diện và font.
- `maps/map1/`, `maps/map2/`: nguồn chỉnh sửa bằng Tiled (`.tmx`, `.tsx`, PNG),
  khác với ảnh runtime trong `assets/images/map/`.
- `tests/test_roundabout.py`: test luật vào/ra và chiều đi của vòng xuyến.
- `scripts/analyze_stats.py`: CLI tổng hợp kết quả từ `stats.csv`.
- `examples/sprite_integration_example.py`: ví dụ kiểm tra sprite riêng lẻ.
- `docs/algorithm_explanation.md`, `docs/project_report.md`: tài liệu thuật toán và báo cáo.

## Quy ước sau tái cấu trúc

- Mã chạy thật đặt trong `src/`; CLI trong `scripts/`; test trong `tests/`.
- Tài nguyên runtime đặt trong `assets/`; nguồn Tiled đặt trong `maps/`.
- Không commit cache, log, thống kê runtime, session Tiled hay file backup.
- Khi triển khai module rỗng, chuyển logic tương ứng khỏi `GameManager` và thêm
  test trước khi xóa code cũ.
