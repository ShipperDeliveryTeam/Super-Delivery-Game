# Super Delivery Game

Super Delivery Game là trò chơi mô phỏng giao hàng được xây dựng bằng Python và Pygame. Người chơi điều khiển shipper để nhận đơn, lấy hàng, giao hàng, tránh bẫy và cạnh tranh với các shipper AI. Dự án đồng thời có chế độ Auto Mode để trực quan hóa, benchmark và so sánh nhiều nhóm thuật toán AI trên cùng bài toán giao hàng.

## Demo

### Gameplay

| Chế độ | GIF | Mô tả |
|---|---|---|
| Play Mode 1 | ![Play mode 1](docs/readme-gifs/play1.gif) | Người chơi nhận đơn, di chuyển trên bản đồ và giao hàng để đạt mục tiêu điểm. |
| Play Mode 2 | ![Play mode 2](docs/readme-gifs/play2.gif) | Minh họa tương tác trong game, HUD đơn hàng, shipper và các điểm giao/nhận. |
| Map 2 | ![Map 2](docs/readme-gifs/map2.gif) | Bản đồ có độ khó trung bình, đường đi và chướng ngại phức tạp hơn. |
| Map 3 | ![Map 3](docs/readme-gifs/map3.gif) | Bản đồ khó với nhiều tuyến đường, chi phí và tình huống di chuyển đa dạng. |

### Mô Phỏng Thuật Toán Bằng GIF

Phần này dùng các GIF preview nhẹ trong `docs/readme-gifs` để mô phỏng cách từng nhóm thuật toán ra quyết định trước khi xem bảng so sánh benchmark. Các GIF gốc chất lượng cao nằm trong `data/gif`.

| Nhóm | GIF mô phỏng | Thuật toán | Ý nghĩa trong dự án |
|---:|---|---|---|
| 1 | ![Nhóm 1](docs/readme-gifs/nhom1.gif) | BFS, DFS, UCS | Tìm đường từ điểm hiện tại đến điểm nhận/giao bằng không gian trạng thái rõ ràng, không dùng heuristic. |
| 2 | ![Nhóm 2](docs/readme-gifs/nhom2.gif) | Greedy, A*, IDA* | Ưu tiên hướng đi có vẻ gần đích hơn bằng heuristic khoảng cách/chi phí. |
| 3 | ![Nhóm 3](docs/readme-gifs/nhom3.gif) | Simple Hill, Steepest Hill, Local Beam | Tối ưu thứ tự nhận/giao đơn dựa trên trạng thái lân cận và giá trị lợi ích. |
| 4 | ![Nhóm 4](docs/readme-gifs/nhom4.gif) | No Observation, Partial Observation, AND-OR Search | Lập kế hoạch trong môi trường có bẫy, bất định hoặc thông tin không đầy đủ. |
| 5 | ![Nhóm 5](docs/readme-gifs/nhom5.gif) | Backtracking, Forward Checking, AC3 Backtracking | Giải bài toán ràng buộc giữa đơn hàng, điểm nhận, điểm giao, thời gian và khả năng di chuyển. |
| 6 | ![Nhóm 6](docs/readme-gifs/nhom6.gif) | Minimax, Alpha-Beta, Expectimax | Mô phỏng cạnh tranh giữa shipper thuật toán và shipper đối thủ dùng Greedy. |

## Tính Năng Chính

- Play Mode: người chơi tự giao hàng trên 3 bản đồ.
- Auto Mode: mô phỏng shipper AI chạy theo từng nhóm thuật toán.
- Benchmark Mode: đo score, tổng chi phí, số node mở rộng, tỉ lệ thành công và thời gian chạy.
- Visual hóa bẫy, điểm nhận hàng, điểm giao hàng, đường đi và trạng thái shipper.
- Nhóm 6 hỗ trợ chọn 1 trong 3 thuật toán đối kháng để đấu với Greedy.
- Tạo biểu đồ so sánh bằng matplotlib từ dữ liệu CSV.

## Cài Đặt Và Chạy

Yêu cầu Python 3.10 trở lên.

```powershell
python -m pip install -r requirements.txt
python game.py
```

Một số lệnh hữu ích:

```powershell
python game.py --map 1 --algorithm ASTAR
python game.py --algorithm BFS --debug
python src/gameplay/auto/representative_runner.py
python src/gameplay/auto/plot_benchmark_charts.py
python src/gameplay/auto/report_summary_generator.py
```

## Cách Chơi

1. Chọn bản đồ ở màn hình chính.
2. Chọn Level để xem nhóm thuật toán trong Auto Mode.
3. Bấm Play để chơi thủ công hoặc Simulation/Auto để xem AI chạy.
4. Trong Play Mode, nhận đơn, đi đến cửa hàng, lấy hàng và giao đến khách.
5. Trong Auto Mode, quan sát các shipper AI so sánh đường đi, chi phí và tốc độ.

## Các Nhóm Thuật Toán

| Nhóm | Tên nhóm | Thuật toán | Vai trò trong game |
|---:|---|---|---|
| 1 | Tìm kiếm không có thông tin | BFS, DFS, UCS | Tìm đường không dùng heuristic. |
| 2 | Tìm kiếm có thông tin | Greedy, A*, IDA* | Tìm đường có heuristic để ưu tiên hướng đi tốt. |
| 3 | Tìm kiếm cục bộ | Simple Hill, Steepest Hill, Local Beam | Tối ưu thứ tự nhận/giao đơn theo trạng thái lân cận. |
| 4 | Môi trường phức tạp | No Observation, Partial Observation, AND-OR Search | Lập kế hoạch khi có bẫy và thông tin không chắc chắn. |
| 5 | Tìm kiếm ràng buộc | Backtracking, Forward Checking, AC3 Backtracking | Mô hình hóa đơn hàng như bài toán CSP. |
| 6 | Tìm kiếm đối kháng | Minimax, Alpha-Beta, Expectimax | Chọn chiến lược trong trận đấu với AI Greedy. |

## PEAS Cho Từng Nhóm Thuật Toán

PEAS giúp mô tả tác nhân AI trong dự án theo 4 thành phần: Performance measure, Environment, Actuators và Sensors.

| Nhóm | Performance Measure | Environment | Actuators | Sensors |
|---:|---|---|---|---|
| 1 | Đến đúng điểm nhận/giao, chi phí di chuyển thấp, mở rộng node hợp lý. | Bản đồ lưới/TMX đã biết, vật cản, đường đi có trọng số, đơn hàng hiện có. | Chọn ô tiếp theo, lập route từ điểm hiện tại đến mục tiêu, cập nhật đường đi. | Vị trí shipper, ma trận map, danh sách điểm có thể đi, điểm nhận/giao. |
| 2 | Route ngắn hơn, thời gian tính nhanh, score cao hơn nhờ heuristic tốt. | Bản đồ đã biết kèm ước lượng khoảng cách/chi phí đến mục tiêu. | Ưu tiên node có heuristic tốt, chọn đường đi tới điểm nhận/giao. | Vị trí hiện tại, mục tiêu, heuristic khoảng cách, chi phí cạnh, vật cản. |
| 3 | Thứ tự đơn hàng tốt, tổng chi phí giảm, score tăng, hạn chế kết quả cục bộ xấu. | Tập đơn hàng nhiều mục tiêu, trạng thái thay đổi sau mỗi lần nhận/giao. | Đổi thứ tự đơn, chọn lân cận tốt hơn, giữ nhiều ứng viên với Local Beam. | Score hiện tại, chi phí route, đơn chưa giao, vị trí cửa hàng/khách. |
| 4 | An toàn trước bẫy/rủi ro, thành công khi thông tin thiếu, hạn chế route nguy hiểm. | Môi trường có bất định, bẫy, khu vực chưa quan sát hoặc trạng thái không đầy đủ. | Lập kế hoạch điều kiện, re-plan khi có thông tin mới, chọn hành động theo AND-OR. | Thông tin quan sát được, vị trí bẫy đã biết, trạng thái an/toàn, kết quả sau mỗi bước. |
| 5 | Thỏa ràng buộc đơn hàng, giảm vi phạm, cắt nhanh nhánh sai, tìm nghiệm hợp lệ. | Bài toán CSP gồm đơn hàng, điểm nhận, điểm giao, ràng buộc thứ tự và khả năng di chuyển. | Gán biến, quay lui, forward checking, AC3 để lọc miền giá trị. | Tập ràng buộc, miền giá trị còn lại, đơn đã gán, xung đột ràng buộc. |
| 6 | Điểm cao hơn đối thủ, lấy đơn có lợi, giảm lợi thế của Greedy, quyết định tốt trong đối kháng. | Hai shipper cạnh tranh trên cùng bản đồ và tập đơn hàng còn lại. | Chọn nước đi/route/chiến lược bằng Minimax, Alpha-Beta hoặc Expectimax. | Score hai bên, vị trí đối thủ, đơn còn lại, trạng thái game, utility ước lượng. |

## Auto Mode Nhóm 6

Nhóm 6 là chế độ đối kháng. Người dùng có thể chọn một trong ba thuật toán:

- `MINIMAX`
- `ALPHA_BETA`
- `EXPECTIMAX`

Thuật toán được chọn sẽ điều khiển một shipper, shipper còn lại dùng `GREEDY`. Hai shipper cùng tranh các đơn còn lại. Visual sẽ hiển thị score, số node mở rộng, thời gian chạy và trạng thái của từng shipper.

## Benchmark Và Biểu Đồ

Dữ liệu benchmark nằm trong:

- `data/auto_benchmark_results.csv`
- `data/representative_comparison.csv`
- `data/AUTO_MODE_RESULTS_SUMMARY.md`

Script vẽ biểu đồ:

```powershell
python src/gameplay/auto/plot_benchmark_charts.py
```

Ảnh biểu đồ được lưu trong `data/charts`.

### So Sánh Tổng Hợp Trên Tất Cả Map

| Tiêu chí | Biểu đồ mới |
|---|---|
| Score | ![All maps representative score](data/charts/all_maps_representative_score.png) |
| Runtime | ![All maps representative runtime](data/charts/all_maps_representative_runtime.png) |
| Expanded nodes | ![All maps representative expanded nodes](data/charts/all_maps_representative_expanded_nodes.png) |
| Distance/cost | ![All maps representative distance](data/charts/all_maps_representative_distance.png) |
| Success rate | ![All maps representative success rate](data/charts/all_maps_representative_success_rate.png) |

### So Sánh Theo Từng Nhóm Và Từng Map

#### Map 1

| Nhóm | Score | Runtime | Expanded Nodes |
|---:|---|---|---|
| 1 | ![Map 1 group 1 score](data/charts/map_1_group_1_score.png) | ![Map 1 group 1 runtime](data/charts/map_1_group_1_runtime.png) | ![Map 1 group 1 expanded nodes](data/charts/map_1_group_1_expanded_nodes.png) |
| 2 | ![Map 1 group 2 score](data/charts/map_1_group_2_score.png) | ![Map 1 group 2 runtime](data/charts/map_1_group_2_runtime.png) | ![Map 1 group 2 expanded nodes](data/charts/map_1_group_2_expanded_nodes.png) |
| 3 | ![Map 1 group 3 score](data/charts/map_1_group_3_score.png) | ![Map 1 group 3 runtime](data/charts/map_1_group_3_runtime.png) | ![Map 1 group 3 expanded nodes](data/charts/map_1_group_3_expanded_nodes.png) |
| 4 | ![Map 1 group 4 score](data/charts/map_1_group_4_score.png) | ![Map 1 group 4 runtime](data/charts/map_1_group_4_runtime.png) | ![Map 1 group 4 expanded nodes](data/charts/map_1_group_4_expanded_nodes.png) |
| 5 | ![Map 1 group 5 score](data/charts/map_1_group_5_score.png) | ![Map 1 group 5 runtime](data/charts/map_1_group_5_runtime.png) | ![Map 1 group 5 expanded nodes](data/charts/map_1_group_5_expanded_nodes.png) |
| 6 | ![Map 1 group 6 score](data/charts/map_1_group_6_score.png) | ![Map 1 group 6 runtime](data/charts/map_1_group_6_runtime.png) | ![Map 1 group 6 expanded nodes](data/charts/map_1_group_6_expanded_nodes.png) |

#### Map 2

| Nhóm | Score | Runtime | Expanded Nodes |
|---:|---|---|---|
| 1 | ![Map 2 group 1 score](data/charts/map_2_group_1_score.png) | ![Map 2 group 1 runtime](data/charts/map_2_group_1_runtime.png) | ![Map 2 group 1 expanded nodes](data/charts/map_2_group_1_expanded_nodes.png) |
| 2 | ![Map 2 group 2 score](data/charts/map_2_group_2_score.png) | ![Map 2 group 2 runtime](data/charts/map_2_group_2_runtime.png) | ![Map 2 group 2 expanded nodes](data/charts/map_2_group_2_expanded_nodes.png) |
| 3 | ![Map 2 group 3 score](data/charts/map_2_group_3_score.png) | ![Map 2 group 3 runtime](data/charts/map_2_group_3_runtime.png) | ![Map 2 group 3 expanded nodes](data/charts/map_2_group_3_expanded_nodes.png) |
| 4 | ![Map 2 group 4 score](data/charts/map_2_group_4_score.png) | ![Map 2 group 4 runtime](data/charts/map_2_group_4_runtime.png) | ![Map 2 group 4 expanded nodes](data/charts/map_2_group_4_expanded_nodes.png) |
| 5 | ![Map 2 group 5 score](data/charts/map_2_group_5_score.png) | ![Map 2 group 5 runtime](data/charts/map_2_group_5_runtime.png) | ![Map 2 group 5 expanded nodes](data/charts/map_2_group_5_expanded_nodes.png) |
| 6 | ![Map 2 group 6 score](data/charts/map_2_group_6_score.png) | ![Map 2 group 6 runtime](data/charts/map_2_group_6_runtime.png) | ![Map 2 group 6 expanded nodes](data/charts/map_2_group_6_expanded_nodes.png) |

#### Map 3

| Nhóm | Score | Runtime | Expanded Nodes |
|---:|---|---|---|
| 1 | ![Map 3 group 1 score](data/charts/map_3_group_1_score.png) | ![Map 3 group 1 runtime](data/charts/map_3_group_1_runtime.png) | ![Map 3 group 1 expanded nodes](data/charts/map_3_group_1_expanded_nodes.png) |
| 2 | ![Map 3 group 2 score](data/charts/map_3_group_2_score.png) | ![Map 3 group 2 runtime](data/charts/map_3_group_2_runtime.png) | ![Map 3 group 2 expanded nodes](data/charts/map_3_group_2_expanded_nodes.png) |
| 3 | ![Map 3 group 3 score](data/charts/map_3_group_3_score.png) | ![Map 3 group 3 runtime](data/charts/map_3_group_3_runtime.png) | ![Map 3 group 3 expanded nodes](data/charts/map_3_group_3_expanded_nodes.png) |
| 4 | ![Map 3 group 4 score](data/charts/map_3_group_4_score.png) | ![Map 3 group 4 runtime](data/charts/map_3_group_4_runtime.png) | ![Map 3 group 4 expanded nodes](data/charts/map_3_group_4_expanded_nodes.png) |
| 5 | ![Map 3 group 5 score](data/charts/map_3_group_5_score.png) | ![Map 3 group 5 runtime](data/charts/map_3_group_5_runtime.png) | ![Map 3 group 5 expanded nodes](data/charts/map_3_group_5_expanded_nodes.png) |
| 6 | ![Map 3 group 6 score](data/charts/map_3_group_6_score.png) | ![Map 3 group 6 runtime](data/charts/map_3_group_6_runtime.png) | ![Map 3 group 6 expanded nodes](data/charts/map_3_group_6_expanded_nodes.png) |

## Nhận Xét Kết Quả

- UCS ổn định hơn BFS và DFS trên bản đồ có trọng số vì ưu tiên chi phí nhỏ.
- A* cân bằng tốt giữa độ tối ưu và số node mở rộng.
- IDA* có thể hiệu quả trên map nhỏ nhưng dễ tốn thời gian khi không gian tìm kiếm lớn.
- Local Beam phù hợp với bài toán chọn thứ tự giao nhiều đơn.
- AND-OR Search phù hợp với môi trường có rủi ro, bẫy hoặc thông tin không đầy đủ.
- Forward Checking giảm nhánh sai tốt hơn Backtracking thuần trong nhóm CSP.
- Alpha-Beta giữ logic Minimax nhưng giảm số node nhờ cắt tỉa.
- Expectimax phù hợp khi đối thủ hoặc môi trường có yếu tố không chắc chắn.

Lưu ý: nhóm 6 dùng utility cạnh tranh nên `distance/cost` không nên so trực tiếp với các nhóm giao hàng tuần tự.

## Cấu Trúc Dự Án

```text
game.py                         Điểm khởi chạy chính
assets/                         Hình ảnh, âm thanh, font
data/                           CSV benchmark, GIF mô phỏng, báo cáo và biểu đồ
docs/                           Tài liệu kỹ thuật và báo cáo
maps/                           File bản đồ Tiled và tile assets
scripts/                        Script phân tích thống kê
src/
  ai/                           Các thuật toán tìm kiếm
  core/                         Cấu hình, trạng thái game, event, game loop
  entities/                     Player, NPC, shipper, store, order, trap
  gameplay/                     Logic Play Mode và Auto Mode
  maps/                         Đọc map, collision, ma trận
  systems/                      Asset, sound, stats, animation
  ui/                           Menu, HUD, renderer, popup
tests/                          Kiểm thử tự động
```

## Tài Liệu Liên Quan

1. Russell, S., & Norvig, P. (2016). Artificial Intelligence: A Modern Approach (3rd ed.). Pearson.
2. Russell, S., & Norvig, P. (2020). Artificial Intelligence: A Modern Approach (4th ed.). Pearson.
3. Scaler Topics. Artificial Intelligence Tutorial.
4. Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow (3rd edition) - Aurélien Géron.
5. Deep Reinforcement Learning Hands-On - Maxim Lapan.

## Công Nghệ Sử Dụng

- Python
- Pygame
- Matplotlib
- Tiled TMX map
- CSV benchmark/report pipeline

## Tác Giả

**Ninh Nguyễn Minh Tuyên**

MSSV: `24110372`

**Nguyễn Lê Huy**

MSSV: `24110221`

**Trần Hải Đạt**

MSSV: `24110197`

**Môn học** `Trí tuệ nhân tạo`

**Giáo viên hướng dẫn** `Phan Thị Huyền Trang`
