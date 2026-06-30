# Báo cáo giải thích code Super Delivery Game

Tài liệu này viết theo góc nhìn một sinh viên Công nghệ thông tin đang bảo vệ dự án. Mục tiêu là giúp bạn nắm được cấu trúc, luồng chạy, chức năng từng nhóm file, các đoạn code quan trọng và những câu hỏi giảng viên có thể hỏi.

## 1. Tổng quan dự án

`Super Delivery Game` là game mô phỏng giao hàng viết bằng Python và Pygame. Người chơi điều khiển shipper nhận đơn, lấy hàng tại cửa hàng, giao tới khách, tránh bẫy và cạnh tranh với các shipper NPC. Dự án còn có `Auto Mode` để trực quan hóa và benchmark nhiều nhóm thuật toán AI.

Công nghệ chính:

- Python: ngôn ngữ lập trình chính.
- Pygame: tạo cửa sổ game, xử lý input, vẽ hình ảnh, sprite, UI.
- CSV/XML/TMX: lưu map, ma trận đường đi, dữ liệu benchmark.
- Matplotlib: tạo biểu đồ thống kê benchmark.
- unittest/pytest style tests: kiểm thử smoke test, kiến trúc, vòng xuyến, auto visual.

Hai chế độ chính:

- `Play Mode`: người chơi điều khiển shipper thủ công.
- `Simulation/Auto Mode`: AI điều khiển shipper và hiển thị thuật toán.

## 2. Cấu trúc thư mục

```text
Super-Delivery-Game/
  game.py                 Điểm chạy chính của toàn bộ chương trình
  requirements.txt        Danh sách thư viện cần cài
  README.md               Hướng dẫn tổng quan, demo, thuật toán, benchmark
  stats.csv               Kết quả các ván chơi đã ghi lại

  assets/                 Tài nguyên runtime
    characters/           Sprite player và NPC theo hướng
    icons/                Icon nút, trap, tick, location
    images/               Ảnh bản đồ và ảnh shop
    sounds/               Âm thanh
    ui/                   Ảnh nền, card, popup, logo

  maps/                   File nguồn bản đồ từ Tiled
    map1/, map2/, map3/   TMX/TSX gốc cho từng map
    auto/                 TMX riêng cho auto/benchmark

  src/                    Mã nguồn chính
    core/                 Vòng đời game, settings, trạng thái, event, command
    entities/             Đối tượng game như shipper
    gameplay/             Luật chơi, đơn hàng, auto mode, play mode
    ai/                   Thuật toán tìm kiếm và lập kế hoạch
    maps/                 Đọc TMX/CSV, quản lý map, collision
    systems/              Asset loader, sprite loader, stats
    ui/                   Vẽ menu, HUD, popup, result screen, renderer
    utils/                Tiện ích, hiện nhiều file còn là placeholder

  data/                   Kết quả benchmark, GIF, chart
  docs/                   Tài liệu báo cáo và kiến trúc
  scripts/                Script phụ trợ phân tích thống kê, tạo GIF preview
  examples/               Ví dụ kiểm thử sprite riêng
  tests/                  Test tự động
```

## 3. Luồng chạy chính từ `main`

Luồng tổng quát:

```text
python game.py
  -> parse_args()
  -> main()
  -> tạo GameSettings
  -> áp dụng --map, --algorithm, --debug nếu có
  -> tạo GameManager(settings)
  -> GameManager.__init__()
       -> pygame.init()
       -> tạo cửa sổ, clock, font
       -> tạo loader, pathfinder, order generator
       -> load assets
       -> load map đang chọn
       -> reset game
  -> GameManager.run()
       -> while running:
            dt = clock.tick(fps) / 1000
            _handle_commands()
            _update(dt)
            _draw()
       -> pygame.quit()
```

Điểm cần nhớ khi giảng viên hỏi:

- `game.py` là entry point duy nhất.
- `GameManager` không tự viết toàn bộ logic trong một file, mà kế thừa nhiều `Mixin`.
- Mỗi frame game có 3 bước: xử lý sự kiện, cập nhật trạng thái, vẽ giao diện.
- `dt` là delta time tính bằng giây, giúp chuyển động mượt và không phụ thuộc tuyệt đối vào tốc độ máy.

## 4. Giải thích `game.py`

Vai trò: đọc tham số dòng lệnh, chuẩn bị môi trường import, khởi tạo `GameManager` và bắt lỗi thân thiện.

Các dòng quan trọng:

- `PROJECT_ROOT = Path(__file__).resolve().parent`: lấy thư mục gốc dự án.
- `LOCAL_VENDOR_DIR = PROJECT_ROOT / ".vendor"`: thư mục phụ nếu có thư viện cài cục bộ.
- `if importlib.util.find_spec("pygame") is None ...`: chỉ thêm `.vendor` vào `sys.path` nếu Python chưa tìm thấy pygame.
- `parse_args()`: định nghĩa các tham số:
  - `--map`: chọn map 1, 2 hoặc 3.
  - `--algorithm`: chọn thuật toán.
  - `--debug`: bật traceback chi tiết.
- `main()`: cấu hình UTF-8 cho stdout/stderr, tạo `GameSettings`, set map/algorithm/debug, tạo `GameManager`, gọi `game.run()`.
- `except Exception`: nếu game lỗi, in thông báo tiếng Việt; nếu có `--debug` thì in traceback.
- `if __name__ == "__main__"`: đảm bảo chỉ chạy `main()` khi file được chạy trực tiếp.

## 5. Kiến trúc `GameManager` và Mixin

File chính: `src/core/game_manager.py`.

`GameManager` kế thừa nhiều lớp mixin:

```python
class GameManager(
    ViewportMixin,
    MenuMixin,
    ButtonMixin,
    PopupMixin,
    GameRendererMixin,
    HudMixin,
    PauseMenuMixin,
    ResultScreenMixin,
    TextRendererMixin,
    CommandHandlerMixin,
    StateUpdaterMixin,
    PlayModeMixin,
    AutoModeMixin,
    MovementServiceMixin,
    DeliveryManagerMixin,
    GameFlowMixin,
    GameplayControllerMixin,
    MapManagerMixin,
    AssetManagerMixin,
):
```

Ý nghĩa:

- `GameManager` là lớp trung tâm giữ toàn bộ state runtime.
- Mixin giúp chia logic theo chức năng thay vì để một file khổng lồ.
- Các mixin cùng dùng `self`, vì vậy thuộc tính tạo trong `GameManager.__init__` được các module khác truy cập.

Các thuộc tính quan trọng trong `__init__`:

- `self.settings`: cấu hình game.
- `self.screen`: màn hình Pygame.
- `self.clock`: giới hạn FPS.
- `self.event_handler`: chuyển sự kiện Pygame thành command.
- `self.state`: trạng thái hiện tại, ban đầu là `GameState.MENU`.
- `self.sprite_loader`, `self.matrix_loader`, `self.tmx_loader`: các loader.
- `self.stats_logger`: ghi kết quả vào `stats.csv`.
- `self.order_generator`: sinh đơn giao hàng.
- `self.grid_matrix`, `self.blocked_positions`: dữ liệu map phục vụ pathfinding.
- `self.store_positions`, `self.house_positions`, `self.trap_positions`: vị trí gameplay.
- `self.pathfinder`: đối tượng tìm đường `GamePathfinder`.
- `self.player`, `self.npc_shippers`: shipper người chơi và NPC.
- `self.player_task`, `self.player_tasks`, `self.available_player_tasks`: đơn đang nhận và danh sách đơn có thể chọn.
- `self.elapsed_time`, `self.result_logged`, `self.winner_name`: dữ liệu vòng đời ván chơi.
- `self.simulation_mode`, `self.auto_player_enabled`, `self.hud_mode`: chế độ hiển thị/điều khiển.

Hàm `run()`:

- Chạy vòng lặp đến khi `self.running = False`.
- `_handle_commands()` xử lý input.
- `_update(dt)` cập nhật logic.
- `_draw()` render màn hình.

## 6. Các file trong `src/core`

### `src/core/constants.py`

Chứa hằng số dùng toàn dự án:

- `TILE_SIZE = 32`: kích thước một ô lưới.
- `GRID_COLS = 48`, `GRID_ROWS = 32`: kích thước map mặc định.
- `SCREEN_WIDTH`, `SCREEN_HEIGHT`: kích thước render logic.
- `WINDOW_WIDTH`, `WINDOW_HEIGHT`: kích thước cửa sổ.
- `FPS = 60`: tốc độ khung hình.
- Các thuật toán điều khiển nhanh cho người chơi: `BFS`, `ASTAR`, `BEAM`, `PARTIAL_OBSERVATION`.
- Mã tile: road, block, store, house, trap, water, bridge, roundabout.
- `WALKABLE_TILES`: các loại ô có thể đi qua.
- Màu sắc UI.
- `TARGET_REVENUE = 1500`: doanh thu cần đạt để thắng.

### `src/core/settings.py`

`GameSettings` là dataclass chứa cấu hình runtime:

- Map đang chọn: `selected_map_id`.
- Thuật toán đang chọn: `selected_algorithm`.
- Nhóm thuật toán auto: `selected_algorithm_group_id`.
- Thuật toán đối kháng nhóm 6: `selected_adversarial_algorithm`.
- Các toggle: âm thanh, grid, path hint, debug.
- `set_map()`: chỉ nhận map 1 đến 3.
- `set_algorithm_group()`: chỉ nhận group 1 đến 6.
- `set_adversarial_algorithm()`: chỉ nhận Minimax, Alpha-Beta, Expectimax.
- `set_algorithm()`: chuẩn hóa alias như `A*` thành `ASTAR`.
- `toggle_sound()`, `toggle_grid()`, `toggle_path_hint()`: đổi trạng thái boolean.

### `src/core/game_state.py`

Enum trạng thái màn hình:

- `MENU`: màn hình chính.
- `PLAYING`: chơi thủ công.
- `SIMULATION`: auto mode.
- `PAUSED`: tạm dừng.
- `WIN`: thắng.
- `GAME_OVER`: thua.
- `EXIT`: trạng thái thoát, hiện ít dùng trực tiếp.

### `src/core/event_handler.py`

Chuyển sự kiện Pygame thành command trung lập.

Các lớp:

- `CommandType`: enum các lệnh game.
- `GameCommand`: dataclass gồm `type` và `value`.
- `EventHandler`: đọc queue sự kiện Pygame.

Phím chính:

- `ESC`: pause/resume.
- `Enter`: start.
- `WASD` hoặc mũi tên: di chuyển.
- `Space`: bật/tắt auto player.
- `H`: đổi HUD.
- `G`: bật/tắt grid.
- `P`: bật/tắt path hint.
- `M`: bật/tắt sound.
- `K`, `L`: debug thắng/thua.
- `1`, `2`, `3`: chọn map.
- `F1` đến `F5`: chọn thuật toán nhanh.

Điểm thiết kế tốt: UI/input không gọi trực tiếp logic gameplay, mà phát ra `GameCommand`. Nhờ vậy command handler xử lý tập trung.

### `src/core/command_handler.py`

`CommandHandlerMixin` có 2 hàm chính:

- `_handle_commands()`: lấy danh sách command từ event handler.
- `_execute_command(command)`: thực thi từng command.

Logic quan trọng:

- `QUIT`: đặt `self.running = False`.
- `MOUSE_CLICK`: gọi `_handle_mouse_click`.
- `START_GAME`: nếu đang menu/win/game over thì vào play mode; nếu pause thì resume.
- `PAUSE_GAME`: pause hoặc resume tùy trạng thái.
- `SELECT_MAP`: set map, load lại map, reset game.
- `SELECT_ALGORITHM`: đổi thuật toán và refresh đường gợi ý.
- `TOGGLE_*`: bật/tắt grid/path/sound/auto/HUD.
- `MOVE_*`: gọi `_request_player_step`.
- `DEBUG_WIN`, `DEBUG_LOSE`: kết thúc game phục vụ test/debug.
- `SCROLL`: nếu class có `_handle_scroll_event` thì xử lý cuộn UI.

### `src/core/state_updater.py`

`StateUpdaterMixin._update(dt)` quyết định frame hiện tại cập nhật gì:

- Nếu đang `MENU`: cập nhật hiệu ứng mây rồi return.
- Nếu không phải `PLAYING` hoặc `SIMULATION`: không cập nhật gameplay.
- Nếu đang chơi: cập nhật chuyển động mượt, tăng thời gian, sau đó gọi:
  - `_update_play_mode(dt)` nếu `PLAYING`.
  - `_update_auto_mode(dt)` nếu `SIMULATION`.

## 7. Các file gameplay thường

### `src/gameplay/delivery_task.py`

Dataclass biểu diễn một đơn giao hàng.

Thuộc tính chính:

- `store_pos`: vị trí cửa hàng.
- `house_pos`: vị trí khách/nhà.
- `reward`: tiền nhận được khi giao thành công.
- `holder_name`: shipper đang giữ đơn.
- `picked_up`: đã lấy hàng chưa.
- `delivered`: đã giao chưa.
- `order_id`: mã đơn.
- `created_at`, `expires_in`: thời điểm tạo và thời gian tồn tại.
- `delivery_time_limit`: thời hạn giao sau khi pickup.
- `stolen_by`: NPC lấy mất đơn.
- `lost`: đơn đã mất.
- `pickup_started_at`, `delivery_started_at`: mốc thời gian.

Hàm quan trọng:

- `target_pos`: nếu đã pickup thì mục tiêu là nhà, ngược lại là shop.
- `assign_to(shipper_name)`: gán đơn cho shipper nếu đơn chưa mất và chưa bị người khác giữ.
- `try_pickup(shipper_name, pos)`: pickup thành công nếu đúng shipper và đúng vị trí shop.
- `try_deliver(shipper_name, pos)`: giao thành công nếu đã pickup và đang ở đúng nhà.

### `src/gameplay/order_generator.py`

Sinh đơn mới.

Luồng tạo đơn:

1. Chọn ngẫu nhiên một khách hàng từ `houses`.
2. Dùng `StoreSelector` chọn cửa hàng phù hợp.
3. Nếu có pathfinder, tính chi phí đường đi từ shop tới khách.
4. Tính reward bằng `base_reward + distance_bonus + random`.
5. Trả về `DeliveryTask`.

### `src/gameplay/store_selector.py`

Chọn cửa hàng bằng chiến lược local search đơn giản:

- Đánh giá mỗi cửa hàng dựa trên chi phí đường đi tới khách.
- Lặp tối đa một số vòng để chọn store có cost tốt.
- Trả về `StoreSelectionResult` gồm store được chọn, cost và số vòng lặp.

### `src/gameplay/delivery_manager.py`

Quản lý danh sách đơn cho người chơi.

Hằng số quan trọng:

- `PLAYER_OFFER_COUNT = 5`: màn hình hiển thị 5 đơn.
- `PLAYER_CARGO_LIMIT = 3`: người chơi tối đa giữ 3 đơn.
- `PLAYER_DELIVERY_BASE_SECONDS = 30.0`: thời gian giao cơ bản.
- `PLAYER_DELIVERY_SECONDS_PER_STEP = 1.2`: cộng thời gian theo độ dài đường đi.
- `PLAYER_MIN_DELIVERY_TIME_LIMIT = 45.0`, `PLAYER_MAX_DELIVERY_TIME_LIMIT = 150.0`: giới hạn thời gian giao.
- Trễ giờ bị phạt theo tỉ lệ reward.

Các hàm chính:

- `_new_task()`: sinh đơn mới và cố gắng đảm bảo đơn có đường đi.
- `_task_is_reachable()`: kiểm tra từ shipper tới shop và từ shop tới nhà có path không.
- `_create_player_order_offer()`: tạo đơn hiển thị cho người chơi, gán mã `A01`, `A02`, ...
- `_delivery_time_limit_for_task()`: tính deadline dựa vào độ dài path shop -> house.
- `_delivery_remaining_seconds()`: còn bao nhiêu giây để giao.
- `_late_delivery_penalty()`: tính tiền phạt khi giao trễ.
- `_expire_player_delivery()`: xử lý đơn quá giờ, trừ tiền, xóa đơn, hiện thông báo.
- `_generate_player_order_offers()`: sinh 5 đơn ban đầu.
- `_replenish_player_order_offers()`: bù đơn mới sau khi giao/mất đơn.
- `_select_player_order(index)`: người chơi chọn một đơn, kiểm tra giới hạn 3 đơn.
- `_drop_player_task(task)`: bỏ đơn khỏi danh sách đang giữ.
- `_confirm_player_delivery()`: xác nhận giao hàng khi đã tick checkbox và đang ở đúng nhà.

### `src/gameplay/play/controller.py`

Điều khiển Play Mode.

Luồng `_start_play_mode()`:

- Tắt simulation.
- Reset game.
- Đổi state sang `PLAYING`.

Luồng `_update_play_mode(dt)`:

1. Nếu đang bị trap hoặc popup xác nhận giao hàng mở, không cho di chuyển.
2. Nếu không auto player, đọc bàn phím.
3. Mỗi `0.065` giây cho player đi một bước.
4. Mỗi `0.065` giây cập nhật NPC.
5. Mỗi `0.8` giây refresh path hint.
6. Kiểm tra đơn giao bị timeout.
7. Nếu player đạt doanh thu mục tiêu thì thắng.
8. Nếu quá 300 giây thì kết thúc vì hết giờ.

Luồng di chuyển player:

- `_request_player_step(dx, dy)`: nhận yêu cầu từ command.
- `_poll_keyboard_movement()`: đọc phím đang giữ để set `move_dir`.
- `_move_player()`: gọi `_try_move_shipper_delta`, sau đó kiểm tra pickup/delivery/trap.
- `_handle_player_task_at_current_pos()`: nếu đứng tại shop thì pickup, nếu đứng tại nhà thì mở logic giao, nếu dẫm trap thì trừ tiền và chờ.

### `src/gameplay/movement_service.py`

Chứa logic di chuyển dùng chung:

- `_update_smooth_entities(dt)`: cập nhật animation/chuyển động mượt cho player và NPC.
- `_movement_base_pos(shipper)`: nếu shipper đang đi thì tính từ target cell, tránh queue sai.
- `_try_move_shipper_delta(shipper, dx, dy, allow_queue)`: kiểm tra bước đi hợp lệ, map boundary, pathfinder `can_step`, sau đó gọi `shipper.move_grid`.

### `src/gameplay/game_flow.py`

Quản lý reset và kết thúc game.

- `_finish_game(winner_name)`: nếu chưa log kết quả, set người thắng, đổi state `WIN` hoặc `GAME_OVER`, ghi stats.
- `_log_result()`: gom dữ liệu player/NPC thành `GameStatsRecord` và ghi CSV.
- `_reset_game()`: reset thời gian, trạng thái UI, tạo lại shipper, reset tiền/đơn, sinh đơn ban đầu nếu không phải simulation.

### `src/gameplay/gameplay_controller.py`

Tạo player và NPC:

- Load sprite theo hướng cho player.
- Tạo `DirectionalShipper("Player", self.player_spawn, ...)`.
- Cấu hình diagonal movement và roundabout.
- Tạo 3 NPC theo nhóm thuật toán đang chọn ở menu `LEVEL`; ví dụ level 2 tạo `GREEDY`, `ASTAR`, `IDA_STAR`.
- Nếu map có spawn NPC thì dùng, không thì fallback vị trí mặc định.

### `src/gameplay/roundabout_geometry.py`

Xử lý hình học vòng xuyến:

- Tạo đường cong khi shipper đi qua vòng xuyến.
- Tính điểm trên đường cong theo thời gian.
- Giúp chuyển động ở map 2 mượt và đúng hướng thay vì đi thẳng cứng.

### File placeholder trong `src/gameplay`

Các file `level_manager.py`, `order_manager.py`, `score_manager.py`, `win_condition.py` hiện rỗng. Có thể trả lời giảng viên: đây là file khung để mở rộng sau, logic thật hiện nằm trong các mixin như `DeliveryManagerMixin`, `GameFlowMixin`, `PlayModeMixin`.

## 8. Entity chính: `DirectionalShipper`

File: `src/entities/directional_shipper.py`.

Vai trò: biểu diễn player/NPC có sprite theo hướng và chuyển động mượt trên lưới.

Thuộc tính chính:

- `name`: tên shipper.
- `sprites`: dict sprite theo hướng `up/down/left/right/idle`.
- `tile_size`: kích thước ô.
- `color`: màu fallback nếu không có sprite.
- `algorithm`: thuật toán NPC đang dùng.
- `speed_px`: tốc độ pixel/giây.
- `_grid_pos`: vị trí logic trên grid.
- `target_grid_pos`: ô đang đi tới.
- `queued_grid_pos`: ô kế tiếp được queue khi shipper chưa đi xong ô hiện tại.
- `pixel_x`, `pixel_y`: vị trí render thật theo pixel.
- `direction`: hướng nhìn.
- `is_moving`: có đang di chuyển không.
- `allow_diagonal`: map có cho đi chéo không.
- `roundabout_*`: thông tin vòng xuyến.
- `money`, `orders`, `expanded_nodes`: thống kê gameplay.

Các nhóm hàm:

- Property vị trí: `grid_pos`, `grid_x`, `grid_y`, `render_pos`, `pixel_pos`.
- Hướng: `set_direction_from_delta`.
- Set vị trí: `set_grid_position`, `teleport_to_grid`, `snap_to_grid`, `stop`.
- Vòng xuyến: `configure_roundabout`, `_make_roundabout_curve`.
- Di chuyển: `move_grid`, `move_to_grid`, `_begin_motion`, `_begin_queued_move_if_any`.
- Update: `update(dt)` nội suy pixel theo thời gian.
- Vẽ: `draw(screen)` chọn sprite đúng hướng, fallback vẽ ellipse nếu thiếu sprite.

Điểm đáng giải thích:

- Game lưu hai loại vị trí: `grid_pos` cho logic, `pixel_x/y` cho render mượt.
- Queue bước kế tiếp giúp NPC không bị khựng khi path gửi liên tục.
- Khi đi qua vòng xuyến, chuyển động có thể dùng curve thay vì đường thẳng.

Các file entity rỗng như `entity.py`, `npc_shipper.py`, `order.py`, `player.py`, `store.py`, `trap.py` là placeholder.

## 9. Hệ thống map

### `src/maps/map_manager.py`

Mixin điều phối load map cho game.

Luồng `_load_map_for_selected_map()`:

1. Lấy `map_id` từ settings.
2. Tìm file TMX bằng `_tmx_path(map_id)`.
3. Nếu TMX tồn tại, dùng `TmxMapLoader.load`.
4. Gán grid, kích thước map, ảnh nền, store/house/trap/spawn.
5. Tính `blocked_positions`.
6. Tạo lại `GamePathfinder` với blocked, diagonal và roundabout.
7. Nếu TMX lỗi, fallback sang CSV matrix.

Map 2 có vòng xuyến:

- `_roundabout_center()`: tâm vòng xuyến.
- `_roundabout_ring()`: danh sách ô tạo vòng.
- `_roundabout_connections()`: các cạnh cho phép vào/ra vòng.

Map 2 và 3 cho đi chéo:

```python
return self.settings.selected_map_id in (2, 3)
```

### `src/maps/tmx_loader.py`

Đọc file TMX từ Tiled.

`TmxMapData` lưu:

- Kích thước grid và tile.
- Surface ảnh nền.
- Ma trận grid.
- Vị trí store, house, player spawn, npc spawn, trap.
- Tên store, reward, id.

`TmxMapLoader.load(path)`:

- Parse XML bằng `ElementTree`.
- Đọc width/height/tilewidth/tileheight.
- Đọc layer road/collision.
- Quy đổi về grid game:
  - road: đi được.
  - block: không đi được.
  - trap: đi được nhưng bị phạt.
- Load background surface từ image layer hoặc fallback ảnh.
- Parse object layer để lấy store, house, player, npc, trap.
- Nếu thiếu spawn thì chọn ô đi được gần nhất.

Các helper:

- `blocked_positions(grid)`: trả về tập ô không đi được.
- `_parse_csv_layer`: đọc dữ liệu layer CSV trong TMX.
- `_load_background_surface`: tìm và load ảnh nền.
- `_parse_objects`: đọc object shop/house/spawn/trap.
- `_nearest_walkable`: BFS tìm ô gần nhất có thể đi.

### `src/maps/matrix_loader.py`

Đọc/ghi map dạng CSV đơn giản:

- Dùng khi TMX không load được.
- Tạo demo matrix.
- Load matrix từ `assets/maps/map_X_matrix.csv`.
- Trích xuất store/house/trap từ mã tile.
- Tính blocked positions.

Các file `collision.py`, `grid_map.py`, `map_loader.py`, `tile.py` hiện là placeholder.

## 10. Pathfinding realtime trong game

File: `src/ai/game_pathfinder.py`.

Vai trò: tìm đường cho player path hint, auto player và NPC trong game realtime.

`PathResult` gồm:

- `path`: danh sách ô từ start tới goal.
- `expanded_nodes`: số node đã mở rộng.
- `success`: có tìm được không.
- `algorithm`: tên thuật toán.

`GamePathfinder.__init__` nhận:

- `cols`, `rows`: kích thước map.
- `blocked`: tập ô bị chặn.
- `allow_diagonal`: có cho đi chéo không.
- `roundabout_ring`, `roundabout_connections`: luật vòng xuyến.

`find_path(start, goal, algorithm)` là adapter gameplay:

- Tự kiểm tra map runtime: ô bị chặn, đường chéo, vòng xuyến, chi phí bước đi.
- Tạo hàm `get_neighbors` phù hợp với map game.
- Gọi lại thuật toán chuẩn trong `src/ai/pathfinding` như BFS, DFS, UCS, Greedy, A*, IDA*, Hill Climbing và Local Beam.
- Đổi kết quả `SearchResult`/`LocalPathResult` thành `PathResult` để Play Mode dùng thống nhất.

Một số nhãn thuật toán cấp cao như `BACKTRACKING`, `MINIMAX`, `ALPHA_BETA` trong Play Mode vẫn cần một đoạn đường cụ thể tới mục tiêu hiện tại; `GamePathfinder` dùng thuật toán tìm đường phù hợp làm chiến lược realtime và giữ nhãn để HUD/báo cáo hiển thị đúng level.

Luật di chuyển:

- `neighbors(pos)`: sinh các ô kế cận hợp lệ.
- `is_walkable(pos)`: trong map và không bị block.
- `distance(a, b)`: Manhattan nếu không đi chéo, octile-like nếu đi chéo.
- `move_cost(a, b)`: đi chéo tốn `1.414`, đi thẳng tốn `1`.
- `can_step(start, end)`: kiểm tra ô đi được, luật vòng xuyến, luật chéo.
- `_roundabout_transition_allowed`: chỉ cho đi đúng chiều trong vòng xuyến và đúng cổng vào/ra.
- `_build_diagonal_edges`: phát hiện corridor chéo đủ dài.
- `reconstruct`: dựng lại path từ dict parent.

Điểm cần nói:

- A* thường là mặc định vì cân bằng tốc độ và chất lượng đường đi.
- Pathfinding không chỉ kiểm tra ô trống, mà còn kiểm tra luật đặc biệt như vòng xuyến và đường chéo.

## 11. Bộ thuật toán AI chuẩn trong `src/ai/pathfinding`

Nhóm 1, tìm kiếm không thông tin:

- `uninformed_search/bfs.py`: BFS dùng queue FIFO, tìm đường ít bước nếu mọi cạnh bằng nhau.
- `uninformed_search/dfs.py`: DFS dùng stack, đi sâu trước, có `max_depth`.
- `uninformed_search/ucs.py`: Uniform Cost Search dùng heap theo cost, tối ưu khi cạnh có trọng số.

Nhóm 2, tìm kiếm có thông tin:

- `informed_search/greedy.py`: Greedy Best First Search ưu tiên heuristic nhỏ nhất.
- `informed_search/astar.py`: A* ưu tiên `cost_so_far + heuristic`.
- `informed_search/ida_star.py`: IDA* kết hợp DFS và ngưỡng f-cost, tiết kiệm bộ nhớ hơn A*.

File dùng chung:

- `search_common.py`: định nghĩa `SearchResult`, `reconstruct_path`, `calculate_path_cost`.

Nhóm 3, local search:

- `local_search/route_state.py`: biểu diễn thứ tự pickup/delivery, kiểm tra hợp lệ, tính cost.
- `local_search/simple_hill.py`: hill climbing chọn neighbor tốt hơn đầu tiên.
- `local_search/steepest_hill.py`: chọn neighbor tốt nhất trong toàn bộ lân cận.
- `local_search/local_beam.py`: giữ nhiều candidate tốt cùng lúc.

Nhóm 4, môi trường phức tạp:

- `complex_search/no_observation.py`: lập kế hoạch khi không biết chính xác bẫy.
- `complex_search/partial_observation.py`: lập kế hoạch với thông tin quan sát một phần.
- `complex_search/and_or_graph.py`: AND-OR search cho các trường hợp bất định.

Nhóm 5, CSP:

- `csp/csp_model.py`: mô hình route như bài toán ràng buộc, pickup phải trước delivery.
- `csp/backtracking.py`: quay lui thuần.
- `csp/forward_checking.py`: quay lui có kiểm tra miền còn lại.
- `csp/ac3_backtracking.py`: tiền xử lý AC3 rồi backtracking.

Nhóm 6, đối kháng:

- `adversarial/game_state.py`: trạng thái game hai người chơi, utility, action, transition.
- `adversarial/minimax.py`: tối đa hóa điểm mình, giả sử đối thủ tối ưu.
- `adversarial/alpha_beta.py`: Minimax có cắt tỉa alpha-beta để giảm node.
- `adversarial/expectimax.py`: dùng kỳ vọng khi đối thủ/môi trường có tính xác suất.

File `src/ai/ai_controller.py` hiện rỗng. File `src/ai/local_search/store_selector.py` là local search riêng để chọn store khi sinh đơn.

## 12. Auto Mode và benchmark

### `src/gameplay/auto/algorithm_groups.py`

Khai báo 6 nhóm thuật toán:

- Group 1: `BFS`, `DFS`, `UCS`.
- Group 2: `GREEDY`, `ASTAR`, `IDA_STAR`.
- Group 3: `SIMPLE_HILL`, `STEEPEST_HILL`, `LOCAL_BEAM`.
- Group 4: `NO_OBSERVATION`, `PARTIAL_OBSERVATION`, `AND_OR_SEARCH`.
- Group 5: `BACKTRACKING`, `FORWARD_CHECKING`, `AC3_BACKTRACKING`.
- Group 6: `MINIMAX`, `ALPHA_BETA`, `EXPECTIMAX`.

`REPRESENTATIVE_ALGORITHMS` chọn đại diện mỗi nhóm để so sánh tổng hợp.

### `src/gameplay/auto/models.py`

Dataclass cho Auto Mode:

- `AutoOrder`: đơn trong auto mode.
- `AlgorithmStats`: số node, runtime, memory, số lần replan.
- `AutoShipperState`: trạng thái shipper AI.
- `ExperimentConfig`: cấu hình thí nghiệm.
- `RunResult`: kết quả chạy benchmark.
- `AutoModeType`: BENCHMARK hoặc COMPETITION.
- `OrderStatus`: waiting, picked, delivered, locked.

### `src/gameplay/auto/planner.py`

Planner cơ bản cho nhóm 1 và 2:

- Load map auto và đơn hàng.
- Duyệt đơn theo thứ tự cố định.
- Với mỗi đơn: tìm path từ vị trí hiện tại tới shop, sau đó shop tới customer.
- Gom tổng cost, tổng bước, expanded nodes, generated nodes, runtime.

### `src/gameplay/auto/controller.py`

Mixin điều khiển auto/simulation trong game.

Các trách nhiệm chính:

- `_start_simulation_mode`: vào chế độ simulation.
- `_update_auto_mode`: cập nhật auto visual mỗi frame.
- `_init_auto_visual_demo`: dựng dữ liệu mô phỏng trực quan.
- `_expand_auto_visual_render_path`: xử lý đường chéo để render tránh cắt qua trap.
- `_advance_auto_visual_target`: cho NPC đi tới target tiếp theo.
- `_and_or_replan_if_trap_ahead`: nếu thuật toán AND-OR phát hiện trap thì lập lại kế hoạch.
- `_check_auto_visual_hidden_trap`: xử lý bẫy ẩn.
- `_auto_visual_replan_around_revealed_traps`: replan quanh trap đã lộ.
- `_draw_auto_visual_locations`, `_draw_auto_visual_hidden_traps`, `_draw_auto_visual_current_targets`: vẽ các điểm quan trọng trong auto mode.
- `_handle_auto_visual_mouse_click`: xử lý click trong màn hình auto.
- `_move_player_auto`: player tự đi theo path hint.
- `_refresh_player_path_hint`: tính lại đường gợi ý tới shop/house.
- `_update_npcs`: cập nhật NPC trong play mode.

### `src/gameplay/auto/delivery_search.py`

Tìm kế hoạch giao nhiều đơn trong auto mode:

- `DeliveryNode`: node trạng thái gồm vị trí, đơn đã pickup, đã delivered, path, cost.
- `DeliverySearchResult`: kết quả tìm kiếm.
- `DeliverySearch`: lớp giải bài toán theo thuật toán được chọn.
- Có các segment search: BFS, DFS, best-first, hill climbing, local beam.
- `choose_order`: chọn đơn tiếp theo.
- `solve`: giải toàn bộ route.

### `src/gameplay/auto/visualizer.py`

Chuyển kết quả thuật toán thành plan để vẽ:

- Build plan cho pathfinding, local search, complex search, CSP, adversarial.
- Với nhóm 6, có thể dựng duel giữa thuật toán đối kháng và Greedy.
- Tạo danh sách path/action để Auto Controller render.

### Các file auto khác

- `benchmark_runner.py`: chạy benchmark cho từng nhóm thuật toán, trả `RunResult`.
- `representative_runner.py`: chạy thuật toán đại diện mỗi nhóm trên nhiều map.
- `route_cost_matrix.py`: tạo ma trận chi phí giữa start, pickup, delivery.
- `order_factory.py`: tạo đơn từ TMX auto map hoặc clone đơn cho benchmark.
- `pathfinder_adapter.py`: chuẩn hóa tên thuật toán và gọi hàm pathfinding phù hợp.
- `complex_traps.py`: tạo bẫy ẩn/phức tạp cho nhóm môi trường bất định.
- `scoring.py`: tính điểm, phạt trễ, rank bonus.
- `stats_adapter.py`: chuyển `RunResult` thành row CSV.
- `plot_benchmark_charts.py`: vẽ biểu đồ từ CSV.
- `report_summary_generator.py`: tạo báo cáo markdown từ kết quả CSV.
- `config.py`: cấu hình map auto.
- `maps/tmx_loader.py`: loader TMX riêng cho auto.
- `maps/graph_adapter.py`: biến map auto thành graph cho thuật toán.
- `maps/registry.py`, `map1.py`, `map2.py`, `map3.py`, `map_profile.py`: metadata auto map.
- `maps/tmx_validator.py`, `path_connectivity_test.py`: kiểm tra TMX và connectivity.
- Các file `test_*.py` trong `src/gameplay/auto`: script kiểm tra từng nhóm thuật toán.
- `competition_runner.py`, `runtime.py` hiện rỗng hoặc chưa dùng.

## 13. UI và render

### `src/ui/game_renderer.py`

Render màn hình chính:

- `_draw()`: dispatch theo state.
- `_draw_menu()`: vẽ menu.
- `_draw_game()`: vẽ map, path, location, shipper, HUD.
- `_draw_active_locations()`: vẽ cửa hàng/nhà đang liên quan tới đơn.
- `_draw_paths()`, `_draw_path()`: vẽ đường đi gợi ý/NPC.
- `_draw_static_icons()`: vẽ icon shop/house/trap.
- `_draw_grid()`: vẽ lưới khi bật debug grid.
- `_draw_algorithm_label()`: hiện tên thuật toán cạnh NPC.

### `src/ui/menu.py`

Vẽ và xử lý menu chính:

- Preview map.
- Chọn map.
- Chọn nhóm thuật toán.
- Chọn thuật toán đối kháng nếu group 6.
- Nút Play, Simulation, sound, menu dropdown, rules/window popup.
- `_handle_mouse_click`: xử lý click menu và gameplay.

### `src/ui/hud.py`

Vẽ HUD khi chơi:

- Điểm, tiền, số đơn, thời gian.
- Panel đơn hàng bên trái.
- Thông báo timeout.
- HUD auto visual.
- Nút pause/menu.
- Xử lý click trong gameplay như chọn đơn, xác nhận giao.

### Các file UI khác

- `button.py`: helper vẽ nút và kiểm tra click.
- `popup.py`: popup luật chơi/cửa sổ.
- `pause_menu.py`: màn hình pause.
- `result_screen.py`: màn hình thắng/thua.
- `text_renderer.py`: helper render text.
- `viewport.py`: xử lý letterbox/scaling khi cửa sổ không đúng tỉ lệ.
- `left_order_card.py`: vẽ card đơn hàng.
- `left_information_card.py`: vẽ card thông tin.
- `left_active_delivery_card.py`: vẽ card đơn đang giao.

## 14. Systems

### `src/systems/asset_paths.py`

Quy định đường dẫn tài nguyên:

- `PROJECT_ROOT`, `ASSETS_DIR`, `CHARACTERS_DIR`, `ICONS_DIR`, `IMAGES_DIR`, `UI_DIR`, ...
- `get_map_image_path(map_id)`: tìm ảnh map theo nhiều quy ước tên.
- `get_icon_path(name)`: tìm icon theo tên logic.
- `get_ui_asset_path(name)`: tìm ảnh UI.
- `get_player_sprite_paths()`: trả dict path sprite player theo hướng.
- `get_npc_sprite_paths(npc_id)`: trả dict path sprite NPC.

### `src/systems/asset_manager.py`

Load ảnh UI, icon, map, shop card:

- `_load_ui_image`: load một file UI với resize/fallback.
- `_load_assets`: load toàn bộ icon, button, background, logo.
- `_load_shop_card_images`: load ảnh shop theo map.

### `src/systems/sprite_loader.py`

Load sprite Pygame:

- Load ảnh từ path.
- Scale về size.
- Cache để tránh load lặp.
- Fallback bằng surface màu và chữ nếu thiếu file.
- Load bộ sprite theo hướng.

### `src/systems/stats_logger.py`

Ghi kết quả một ván chơi:

- `GameStatsRecord`: dataclass chứa thông tin player/NPC, map, thời gian, thuật toán.
- `StatsLogger.write_record`: append CSV, tự ghi header nếu file chưa tồn tại.
- `now_text`: tạo timestamp.

### `src/systems/stats_analyzer.py`

Đọc `stats.csv`, tính tổng hợp và có thể tạo chart/báo cáo.

Các file `animation.py`, `camera.py`, `sound_manager.py` hiện là placeholder.

## 15. Scripts, examples, tests

### `scripts/analyze_stats.py`

CLI đọc `stats.csv` và in phân tích thống kê.

### `scripts/create_readme_gif_previews.py`

Tạo GIF preview nhẹ hơn từ GIF gốc để dùng trong README.

### `examples/sprite_integration_example.py`

Ví dụ chạy riêng để kiểm tra sprite và di chuyển.

### `tests/test_game_smoke.py`

Smoke test đảm bảo game import/khởi tạo được ở mức cơ bản.

### `tests/test_project_architecture.py`

Kiểm tra cấu trúc dự án, file quan trọng, import hoặc quy ước kiến trúc.

### `tests/test_roundabout.py`

Kiểm tra luật vòng xuyến và di chuyển chéo.

### `tests/test_auto_visual_render_path.py`

Kiểm tra path render trong auto visual, đặc biệt với đường chéo và trap.

## 16. Dữ liệu và tài nguyên

### `assets/`

- `characters/player`: sprite shipper người chơi theo 4 hướng.
- `characters/npc`: sprite NPC theo 4 hướng.
- `icons`: icon trap, tick, star, sound, location, menu, pause.
- `images/map`: ảnh nền map 1, 2, 3.
- `images/shop_mapX`: ảnh shop theo từng map.
- `sounds`: âm thanh pickup, delivery, win, gameover, trap, background music.
- `ui`: card UI, popup, background, logo.
- `maps`: matrix CSV runtime.

### `maps/`

Chứa file nguồn Tiled:

- `.tmx`: layout map.
- `.tsx`: tileset.
- `.tiled-project`: project Tiled.
- `maps/auto`: bản map riêng cho benchmark/auto.

### `data/`

- `auto_benchmark_results.csv`: kết quả benchmark đầy đủ.
- `representative_comparison.csv`: so sánh thuật toán đại diện.
- `AUTO_MODE_RESULTS_SUMMARY.md`: báo cáo tổng hợp.
- `charts/`: ảnh biểu đồ.
- `gif/`: GIF mô phỏng thuật toán.

## 17. Giải thích một vòng chơi thủ công

Luồng từ lúc người chơi bấm Play:

1. Click Play hoặc nhấn Enter.
2. `EventHandler` tạo `START_GAME`.
3. `CommandHandlerMixin` gọi `_start_play_mode()`.
4. `_start_play_mode` reset game và set state `PLAYING`.
5. `_reset_game` tạo player/NPC, reset tiền, sinh 5 đơn.
6. Người chơi chọn đơn trong HUD.
7. `_select_player_order` thêm đơn vào `player_tasks` nếu chưa quá 3 đơn.
8. Người chơi di chuyển tới `store_pos`.
9. `_handle_player_task_at_current_pos` gọi `try_pickup`.
10. Sau pickup, target đổi sang `house_pos`.
11. Người chơi tới nhà, tick xác nhận giao.
12. `_confirm_player_delivery` gọi `try_deliver`, cộng tiền, tăng số đơn, bù đơn mới.
13. Nếu tiền >= `target_revenue`, `_finish_game("Player")`.
14. `_log_result` ghi CSV.

## 18. Giải thích một vòng Auto Mode

Luồng khái quát:

1. Người dùng chọn map và nhóm thuật toán.
2. Bấm Simulation.
3. `_start_simulation_mode` reset và khởi tạo auto visual.
4. Auto code load map auto, đơn hàng, thuật toán.
5. `visualizer` xây plan/path/action cho từng shipper.
6. `_update_auto_visual_demo` mỗi frame cho shipper đi theo path.
7. Nếu gặp trap ẩn, một số thuật toán có thể replan.
8. HUD hiển thị score, expanded nodes, runtime, trạng thái đơn.

## 19. Các điểm mạnh kiến trúc

- Có entry point rõ ràng.
- Game loop tách input, update, draw.
- State được quản lý bằng enum.
- Pathfinding tách khỏi render.
- Map loader tách khỏi gameplay.
- Auto mode tách khỏi play mode.
- Dữ liệu thuật toán được biểu diễn bằng dataclass.
- Có test cho logic đặc biệt như vòng xuyến và auto visual.
- Có fallback khi thiếu TMX hoặc thiếu asset.

## 20. Các hạn chế có thể nói thật khi bị hỏi

- Một số file placeholder còn rỗng, ví dụ `score_manager.py`, `sound_manager.py`, `camera.py`.
- `GameManager` dùng nhiều mixin nên dễ chia file, nhưng cũng làm nhiều module phụ thuộc cùng `self`; cần kỷ luật đặt tên thuộc tính.
- Một số import trong mixin còn dư do tách file từ code lớn.
- Auto benchmark và realtime gameplay dùng hai tầng thuật toán khác nhau, cần giải thích rõ để tránh nhầm.
- Sound manager hiện chưa hoàn thiện dù có asset âm thanh.

## 21. Câu hỏi giảng viên có thể hỏi và gợi ý trả lời

### Chương trình bắt đầu chạy từ đâu?

Từ `game.py`. Hàm `main()` parse tham số dòng lệnh, tạo `GameSettings`, tạo `GameManager`, rồi gọi `game.run()`.

### Game loop gồm những bước nào?

Mỗi frame gồm 3 bước: `_handle_commands()` xử lý input, `_update(dt)` cập nhật logic, `_draw()` vẽ màn hình.

### Vì sao dùng `dt`?

`dt` là thời gian giữa hai frame. Dùng `dt` giúp chuyển động mượt và ít phụ thuộc vào FPS thực tế của máy.

### Vì sao dùng Mixin?

Mixin giúp tách một lớp game lớn thành nhiều file theo chức năng: menu, render, gameplay, auto, map, asset. Nhược điểm là các mixin dùng chung `self`, nên phải quản lý thuộc tính cẩn thận.

### `GameState` dùng để làm gì?

Để biết game đang ở màn hình nào: menu, đang chơi, simulation, pause, thắng, thua. Từ đó update/draw đúng logic.

### Input được xử lý thế nào?

Pygame tạo event. `EventHandler` chuyển event thành `GameCommand`. `CommandHandlerMixin` đọc command và gọi hàm gameplay tương ứng.

### Đơn hàng được biểu diễn bằng gì?

Bằng dataclass `DeliveryTask`, có vị trí shop, vị trí nhà, reward, trạng thái pickup/delivered/lost, holder và deadline.

### Khi nào người chơi thắng?

Trong `_update_play_mode`, nếu `player.money >= settings.target_revenue` thì gọi `_finish_game("Player")`.

### Khi nào thua hoặc kết thúc vì hết giờ?

Nếu `elapsed_time >= 300.0`, game gọi `_finish_game("Time Up")`, state thành `GAME_OVER`.

### Bẫy hoạt động thế nào?

Nếu player đứng vào vị trí trong `trap_positions`, game trừ tối đa 100 tiền, dừng shipper và đặt `player_trap_wait_until = elapsed_time + 5.0`.

### Tại sao có `grid_pos` và `pixel_pos`?

`grid_pos` dùng cho logic như pathfinding, pickup, collision. `pixel_pos` dùng để vẽ chuyển động mượt giữa hai ô.

### Pathfinding kiểm tra ô đi được ở đâu?

Trong `GamePathfinder.is_walkable` và `GamePathfinder.can_step`. `can_step` còn kiểm tra luật đi chéo và vòng xuyến.

### A* trong dự án hoạt động thế nào?

A* dùng `g_score` là chi phí từ start tới node hiện tại, heuristic là khoảng cách tới goal, priority là `g_score + heuristic`.

### BFS khác UCS thế nào?

BFS tối ưu số bước khi mọi cạnh có chi phí bằng nhau. UCS tối ưu tổng chi phí khi cạnh có trọng số khác nhau.

### Greedy khác A* thế nào?

Greedy chỉ ưu tiên heuristic tới goal. A* cộng cả chi phí đã đi và heuristic, nên thường ổn định hơn.

### Vì sao map 2 có logic riêng?

Map 2 có vòng xuyến. Code giới hạn hướng đi trong vòng xuyến và dùng curve để shipper đi mượt qua vòng.

### TMX loader đọc gì từ bản đồ?

Đọc layer road/collision để tạo grid, đọc object layer để lấy store, house, player spawn, npc spawn và trap.

### Nếu TMX lỗi thì sao?

`MapManagerMixin` fallback sang CSV matrix trong `assets/maps`.

### Auto mode khác play mode thế nào?

Play mode xử lý input người chơi trực tiếp. Auto mode dùng thuật toán tạo plan/path rồi tự di chuyển shipper để mô phỏng và benchmark.

### Group 6 đối kháng nghĩa là gì?

Hai shipper cạnh tranh đơn. Thuật toán như Minimax/Alpha-Beta/Expectimax chọn chiến lược dựa trên điểm của mình và đối thủ.

### Alpha-Beta cải thiện Minimax như thế nào?

Alpha-Beta giữ nguyên kết quả Minimax trong trường hợp sắp xếp tốt, nhưng cắt các nhánh không thể ảnh hưởng tới quyết định cuối, giảm số node duyệt.

### Expectimax dùng khi nào?

Khi có yếu tố xác suất hoặc đối thủ không hoàn toàn tối ưu. Nó tính kỳ vọng thay vì chỉ max/min cứng.

### CSP trong dự án biểu diễn ràng buộc gì?

Pickup phải xảy ra trước delivery của cùng đơn, route phải hợp lệ, capacity và thứ tự hành động phải thỏa ràng buộc.

### Local search dùng để làm gì?

Dùng để tối ưu thứ tự nhận/giao nhiều đơn, không chỉ tìm đường giữa hai điểm.

### Dữ liệu benchmark ghi những gì?

Score, tổng distance/cost, finish time, expanded nodes, runtime, số lần replan, trap hits, số đơn hoàn thành.

### Tại sao cần test?

Test giúp đảm bảo các logic khó như vòng xuyến, render path chéo và kiến trúc import không bị lỗi khi chỉnh code.

## 22. Cách thuyết trình ngắn gọn trong 1 đến 2 phút

Em xây dựng game giao hàng bằng Python/Pygame. Chương trình bắt đầu từ `game.py`, tạo cấu hình, khởi tạo `GameManager` và chạy game loop gồm xử lý input, cập nhật logic và render. Dự án chia theo module: `core` quản lý vòng đời game, `gameplay` xử lý đơn hàng và luật chơi, `maps` đọc TMX/CSV, `ai` chứa thuật toán tìm đường/lập kế hoạch, `ui` vẽ giao diện, `systems` load tài nguyên và ghi thống kê.

Trong Play Mode, người chơi chọn đơn, đi tới cửa hàng để lấy hàng, sau đó giao tới khách. Nếu giao đúng hạn thì nhận tiền, nếu trễ thì bị phạt, nếu đạp bẫy thì bị trừ tiền và chờ. Khi đạt doanh thu mục tiêu thì thắng. Trong Auto Mode, dự án mô phỏng 6 nhóm thuật toán AI như BFS/DFS/UCS, A*/Greedy/IDA*, Local Search, AND-OR, CSP và Minimax/Alpha-Beta/Expectimax. Kết quả được benchmark bằng score, thời gian chạy và số node mở rộng.

## 23. Nên mở file nào khi demo code?

Thứ tự mở file đề xuất:

1. `game.py`: chứng minh entry point.
2. `src/core/game_manager.py`: giải thích game loop và kiến trúc mixin.
3. `src/core/event_handler.py`: input thành command.
4. `src/core/state_updater.py`: update theo state.
5. `src/gameplay/play/controller.py`: luật chơi thủ công.
6. `src/gameplay/delivery_task.py`: model đơn hàng.
7. `src/gameplay/delivery_manager.py`: chọn/nhận/giao đơn.
8. `src/ai/game_pathfinder.py`: tìm đường realtime.
9. `src/maps/tmx_loader.py`: đọc map.
10. `src/gameplay/auto/algorithm_groups.py`: 6 nhóm thuật toán AI.
11. `src/gameplay/auto/models.py`: dữ liệu benchmark.
12. `src/ui/game_renderer.py`: render màn hình.

## 24. Checklist trước khi báo cáo

- Chạy được `python game.py`.
- Biết giải thích `game.py -> GameManager -> run`.
- Biết `GameState` có những trạng thái nào.
- Biết player thắng bằng doanh thu mục tiêu.
- Biết đơn hàng pickup ở shop và delivery ở house.
- Biết bẫy trừ tiền và delay.
- Biết A* dùng `g + h`.
- Biết 6 nhóm thuật toán AI và đại diện mỗi nhóm.
- Biết TMX/CSV map được load ra grid.
- Biết một số file rỗng là placeholder để phát triển sau.

## 25. Phụ lục chức năng nhanh từng file mã nguồn

Bảng này dùng khi giảng viên mở bất kỳ file Python nào và hỏi file đó để làm gì.

### File gốc

| File | Chức năng |
|---|---|
| `game.py` | Entry point, parse tham số dòng lệnh, tạo `GameSettings`, tạo `GameManager`, chạy game loop. |
| `requirements.txt` | Liệt kê dependency cần cài như pygame/matplotlib. |

### `src/core`

| File | Chức năng |
|---|---|
| `src/core/__init__.py` | Đánh dấu package `core`. |
| `src/core/constants.py` | Hằng số màn hình, tile, màu, mã tile, thuật toán mặc định. |
| `src/core/settings.py` | Dataclass cấu hình runtime, map, thuật toán, debug, toggle UI. |
| `src/core/game_state.py` | Enum các trạng thái menu, playing, simulation, pause, win, game over. |
| `src/core/event_handler.py` | Đọc event Pygame và chuyển thành `GameCommand`. |
| `src/core/command_handler.py` | Thực thi command: start, pause, chọn map, chọn thuật toán, di chuyển. |
| `src/core/state_updater.py` | Dispatch update theo state hiện tại. |
| `src/core/game_manager.py` | Composition root, khởi tạo Pygame, loader, map, player/NPC và vòng lặp chính. |

### `src/entities`

| File | Chức năng |
|---|---|
| `src/entities/__init__.py` | Đánh dấu package `entities`. |
| `src/entities/directional_shipper.py` | Entity shipper có sprite theo hướng, vị trí grid/pixel, queue chuyển động, vòng xuyến. |
| `src/entities/entity.py` | Placeholder cho base entity sau này. |
| `src/entities/player.py` | Placeholder cho player entity nếu tách riêng khỏi `DirectionalShipper`. |
| `src/entities/npc_shipper.py` | Placeholder cho NPC shipper nếu mở rộng. |
| `src/entities/order.py` | Placeholder cho model order cũ, hiện dùng `DeliveryTask` và `AutoOrder`. |
| `src/entities/store.py` | Placeholder cho entity cửa hàng. |
| `src/entities/trap.py` | Placeholder cho entity bẫy. |

### `src/gameplay`

| File | Chức năng |
|---|---|
| `src/gameplay/__init__.py` | Đánh dấu package `gameplay`. |
| `src/gameplay/delivery_task.py` | Dataclass đơn hàng thủ công: shop, house, reward, pickup, delivery, deadline. |
| `src/gameplay/order_generator.py` | Sinh đơn hàng mới, chọn customer, chọn store, tính reward. |
| `src/gameplay/store_selector.py` | Chọn store tốt bằng local search/chi phí đường đi. |
| `src/gameplay/delivery_manager.py` | Quản lý đơn người chơi: tạo offer, chọn đơn, pickup, giao, phạt trễ. |
| `src/gameplay/play/controller.py` | Điều khiển Play Mode: input, di chuyển player, trap, thắng/thua theo thời gian. |
| `src/gameplay/movement_service.py` | Di chuyển dùng chung cho player/NPC, kiểm tra can_step và queue. |
| `src/gameplay/game_flow.py` | Reset game, kết thúc game, ghi thống kê. |
| `src/gameplay/gameplay_controller.py` | Tạo player/NPC, load sprite, cấu hình thuật toán NPC. |
| `src/gameplay/roundabout_geometry.py` | Tính đường cong và luật hình học cho vòng xuyến. |
| `src/gameplay/level_manager.py` | Placeholder quản lý level. |
| `src/gameplay/order_manager.py` | Placeholder quản lý order. |
| `src/gameplay/score_manager.py` | Placeholder quản lý điểm. |
| `src/gameplay/win_condition.py` | Placeholder điều kiện thắng riêng. |

### `src/gameplay/auto`

| File | Chức năng |
|---|---|
| `src/gameplay/auto/__init__.py` | Đánh dấu package auto mode. |
| `src/gameplay/auto/algorithm_groups.py` | Khai báo 6 nhóm thuật toán và thuật toán đại diện. |
| `src/gameplay/auto/models.py` | Dataclass auto mode: order, shipper state, config, run result. |
| `src/gameplay/auto/config.py` | Cấu hình map auto. |
| `src/gameplay/auto/controller.py` | Điều khiển simulation/auto visual, replan, path hint, NPC update. |
| `src/gameplay/auto/planner.py` | Planner tuần tự cho pathfinding: start -> pickup -> delivery. |
| `src/gameplay/auto/delivery_search.py` | Search tổng hợp cho bài toán giao nhiều đơn. |
| `src/gameplay/auto/visualizer.py` | Chuyển kết quả thuật toán thành plan/path để vẽ trong auto mode. |
| `src/gameplay/auto/pathfinder_adapter.py` | Adapter gọi đúng thuật toán pathfinding theo tên. |
| `src/gameplay/auto/order_factory.py` | Tạo `AutoOrder` từ map, clone order cho benchmark. |
| `src/gameplay/auto/route_cost_matrix.py` | Tạo ma trận chi phí giữa start, pickup, delivery. |
| `src/gameplay/auto/complex_traps.py` | Tạo và xử lý bẫy ẩn cho môi trường phức tạp. |
| `src/gameplay/auto/scoring.py` | Tính điểm, phạt trễ, rank bonus cho benchmark. |
| `src/gameplay/auto/benchmark_runner.py` | Chạy benchmark cho từng thuật toán/nhóm thuật toán. |
| `src/gameplay/auto/representative_runner.py` | Chạy thuật toán đại diện của từng nhóm trên các map. |
| `src/gameplay/auto/stats_adapter.py` | Chuyển `RunResult` thành row CSV và ghi file. |
| `src/gameplay/auto/plot_benchmark_charts.py` | Vẽ biểu đồ benchmark từ CSV. |
| `src/gameplay/auto/report_summary_generator.py` | Sinh báo cáo tổng hợp benchmark dạng markdown. |
| `src/gameplay/auto/competition_runner.py` | Placeholder cho competition runner. |
| `src/gameplay/auto/runtime.py` | Placeholder runtime auto. |
| `src/gameplay/auto/test_*.py` | Script test nhanh từng nhóm thuật toán auto. |

### `src/gameplay/auto/maps`

| File | Chức năng |
|---|---|
| `src/gameplay/auto/maps/__init__.py` | Đánh dấu package auto maps. |
| `src/gameplay/auto/maps/map_profile.py` | Dataclass metadata map auto. |
| `src/gameplay/auto/maps/map1.py` | Profile map 1 auto. |
| `src/gameplay/auto/maps/map2.py` | Profile map 2 auto. |
| `src/gameplay/auto/maps/map3.py` | Profile map 3 auto. |
| `src/gameplay/auto/maps/registry.py` | Registry lấy profile map theo id. |
| `src/gameplay/auto/maps/tmx_loader.py` | Loader TMX riêng cho auto benchmark. |
| `src/gameplay/auto/maps/tmx_validator.py` | Kiểm tra file TMX auto có hợp lệ không. |
| `src/gameplay/auto/maps/graph_adapter.py` | Biến map auto thành graph cho thuật toán. |
| `src/gameplay/auto/maps/path_connectivity_test.py` | Kiểm tra các điểm quan trọng trên map có nối được không. |

### `src/ai`

| File | Chức năng |
|---|---|
| `src/ai/__init__.py` | Đánh dấu package `ai`. |
| `src/ai/game_pathfinder.py` | Adapter pathfinding realtime cho Play Mode; giữ luật map game và gọi thuật toán trong `src/ai/pathfinding`. |
| `src/ai/ai_controller.py` | Placeholder controller AI. |
| `src/ai/local_search/__init__.py` | Đánh dấu package local search cũ. |
| `src/ai/local_search/store_selector.py` | Chọn store bằng local search, tương tự gameplay store selector. |

### `src/ai/pathfinding`

| File | Chức năng |
|---|---|
| `src/ai/pathfinding/__init__.py` | Export hoặc đánh dấu package pathfinding. |
| `src/ai/pathfinding/search_common.py` | `SearchResult`, dựng lại path, tính cost path. |
| `src/ai/pathfinding/uninformed_search/bfs.py` | BFS dùng queue. |
| `src/ai/pathfinding/uninformed_search/dfs.py` | DFS dùng stack và max depth. |
| `src/ai/pathfinding/uninformed_search/ucs.py` | Uniform Cost Search dùng priority queue theo cost. |
| `src/ai/pathfinding/informed_search/greedy.py` | Greedy Best First Search theo heuristic. |
| `src/ai/pathfinding/informed_search/astar.py` | A* theo `g + h`. |
| `src/ai/pathfinding/informed_search/ida_star.py` | IDA* dùng ngưỡng f-cost. |
| `src/ai/pathfinding/local_search/route_state.py` | Model route nhiều đơn, validate pickup trước delivery, evaluate cost. |
| `src/ai/pathfinding/local_search/simple_hill.py` | Simple hill climbing. |
| `src/ai/pathfinding/local_search/steepest_hill.py` | Steepest-ascent hill climbing. |
| `src/ai/pathfinding/local_search/local_beam.py` | Local beam search giữ nhiều candidate. |
| `src/ai/pathfinding/complex_search/no_observation.py` | Tìm kiếm khi không quan sát được trap đầy đủ. |
| `src/ai/pathfinding/complex_search/partial_observation.py` | Tìm kiếm với quan sát một phần. |
| `src/ai/pathfinding/complex_search/and_or_graph.py` | AND-OR search cho môi trường bất định. |
| `src/ai/pathfinding/csp/csp_model.py` | Mô hình CSP cho route giao hàng. |
| `src/ai/pathfinding/csp/backtracking.py` | Backtracking search. |
| `src/ai/pathfinding/csp/forward_checking.py` | Forward checking search. |
| `src/ai/pathfinding/csp/ac3_backtracking.py` | AC3 precheck kết hợp backtracking. |
| `src/ai/pathfinding/adversarial/game_state.py` | State/action/utility cho game đối kháng. |
| `src/ai/pathfinding/adversarial/minimax.py` | Minimax search. |
| `src/ai/pathfinding/adversarial/alpha_beta.py` | Minimax có alpha-beta pruning. |
| `src/ai/pathfinding/adversarial/expectimax.py` | Expectimax search. |

### `src/maps`

| File | Chức năng |
|---|---|
| `src/maps/__init__.py` | Đánh dấu package maps. |
| `src/maps/map_manager.py` | Load map theo settings, fallback TMX/CSV/PNG, tạo pathfinder. |
| `src/maps/tmx_loader.py` | Đọc TMX runtime, parse layer/object, tạo grid và surface. |
| `src/maps/matrix_loader.py` | Đọc/ghi matrix CSV và trích xuất store/house/trap. |
| `src/maps/collision.py` | Placeholder collision. |
| `src/maps/grid_map.py` | Placeholder grid map. |
| `src/maps/map_loader.py` | Placeholder map loader. |
| `src/maps/tile.py` | Placeholder tile model. |

### `src/systems`

| File | Chức năng |
|---|---|
| `src/systems/__init__.py` | Đánh dấu package systems. |
| `src/systems/asset_paths.py` | Quy ước và tìm path tài nguyên asset. |
| `src/systems/asset_manager.py` | Load ảnh UI, icon, background, shop card. |
| `src/systems/sprite_loader.py` | Load/cache/scale sprite Pygame, fallback sprite nếu thiếu ảnh. |
| `src/systems/stats_logger.py` | Ghi kết quả game vào CSV. |
| `src/systems/stats_analyzer.py` | Phân tích thống kê từ CSV. |
| `src/systems/animation.py` | Placeholder animation system. |
| `src/systems/camera.py` | Placeholder camera system. |
| `src/systems/sound_manager.py` | Placeholder sound system. |

### `src/ui`

| File | Chức năng |
|---|---|
| `src/ui/button.py` | Helper/mixin vẽ nút và kiểm tra tương tác. |
| `src/ui/game_renderer.py` | Render game, map, path, icon, shipper, grid. |
| `src/ui/hud.py` | HUD gameplay và auto visual, panel thông tin, xử lý click gameplay. |
| `src/ui/menu.py` | Menu chính, chọn map, chọn nhóm thuật toán, popup menu. |
| `src/ui/popup.py` | Popup luật chơi/cửa sổ. |
| `src/ui/pause_menu.py` | Vẽ màn hình pause. |
| `src/ui/result_screen.py` | Vẽ màn hình kết quả thắng/thua. |
| `src/ui/text_renderer.py` | Helper render text. |
| `src/ui/viewport.py` | Xử lý viewport/letterbox khi render. |
| `src/ui/left_order_card.py` | Vẽ card danh sách đơn hàng bên trái. |
| `src/ui/left_information_card.py` | Vẽ card thông tin player/game. |
| `src/ui/left_active_delivery_card.py` | Vẽ card đơn đang giao. |

### `src/utils`

| File | Chức năng |
|---|---|
| `src/utils/__init__.py` | Đánh dấu package utils. |
| `src/utils/csv_utils.py` | Placeholder tiện ích CSV. |
| `src/utils/debug.py` | Placeholder tiện ích debug. |
| `src/utils/math_utils.py` | Placeholder tiện ích toán học. |
| `src/utils/priority_queue.py` | Placeholder priority queue. |

### Scripts, examples, tests

| File | Chức năng |
|---|---|
| `scripts/analyze_stats.py` | Script phân tích `stats.csv`. |
| `scripts/create_readme_gif_previews.py` | Script resize/tạo GIF preview cho README. |
| `examples/sprite_integration_example.py` | Demo kiểm tra sprite và di chuyển độc lập. |
| `tests/__init__.py` | Đánh dấu package tests. |
| `tests/test_game_smoke.py` | Smoke test import/khởi tạo game cơ bản. |
| `tests/test_project_architecture.py` | Test cấu trúc dự án và các file quan trọng. |
| `tests/test_roundabout.py` | Test luật vòng xuyến và di chuyển chéo. |
| `tests/test_auto_visual_render_path.py` | Test render path auto visual với diagonal/trap/replan. |
