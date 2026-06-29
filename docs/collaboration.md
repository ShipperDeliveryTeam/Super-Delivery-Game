# Phân chia phát triển Play và Auto

## Phạm vi sở hữu

- Người làm Play sở hữu `src/gameplay/play/` và các test Play.
- Người làm Auto sở hữu `src/gameplay/auto/` và các test Auto.
- `movement_service.py`, `delivery_manager.py`, `game_flow.py`, `GameManager`,
  `StateUpdater` và renderer là phần dùng chung; chỉ sửa sau khi hai bên thống nhất.

## Nhánh Git

```powershell
# Người làm Play
git switch -c feature/play-mode

# Người làm Auto
git switch -c feature/auto-mode
```

Mỗi người chỉ stage thư mục mình sở hữu. Trước khi merge, chạy:

```powershell
git fetch origin
git rebase origin/main
python -m unittest discover -v
```

Merge một nhánh trước; người còn lại rebase lên `main` mới rồi mới merge nhánh
thứ hai. Cách này giữ xung đột ở phần tích hợp thay vì trộn lẫn code hai mode.
