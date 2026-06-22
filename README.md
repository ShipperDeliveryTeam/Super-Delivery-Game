# Super Delivery Game

Trò chơi mô phỏng giao hàng viết bằng Python/Pygame. Người chơi và các shipper
AI tìm đường trên bản đồ, nhận đơn, giao hàng và so sánh hiệu quả của các thuật
toán tìm kiếm.

## Chạy dự án

Yêu cầu Python 3.10 trở lên.

```powershell
python -m pip install -r requirements.txt
python game.py
```

Các tùy chọn thường dùng:

```powershell
python game.py --map 1 --algorithm ASTAR
python game.py --algorithm BFS --debug
```

Thuật toán hợp lệ: `BFS`, `ASTAR`, `BEAM`, `PARTIAL_OBSERVATION`, `Q_LEARNING`.

## Kiểm tra và phân tích kết quả

```powershell
python -m unittest discover -v
python scripts/analyze_stats.py
```

Lệnh thứ hai đọc `stats.csv` và tạo báo cáo/biểu đồ. `matplotlib` chỉ cần thiết
cho chức năng tạo biểu đồ.

## Cấu trúc chính

```text
game.py               Điểm khởi chạy ứng dụng
src/                  Mã nguồn Python
  core/               Game loop, command, cập nhật, cấu hình và sự kiện
  ai/                 Điều phối tìm đường và lựa chọn cửa hàng
  gameplay/           Hai mode play/auto, đơn hàng và luật chơi dùng chung
  maps/               Quản lý map, đọc TMX và ma trận
  entities/           Thực thể có hình ảnh/chuyển động trong game
  systems/            Tải tài nguyên, sprite và thống kê
  ui/                 Menu, HUD, renderer, popup và viewport
assets/               Ảnh, âm thanh, font dùng khi chạy game
maps/                 File nguồn của Tiled để biên tập bản đồ
tests/                Kiểm thử tự động
scripts/              Công cụ chạy độc lập
docs/                 Báo cáo và tài liệu kỹ thuật
examples/             Ví dụ tích hợp riêng lẻ
```

Xem [docs/project_structure.md](docs/project_structure.md) để biết vai trò chi
tiết của từng thư mục và file quan trọng.
