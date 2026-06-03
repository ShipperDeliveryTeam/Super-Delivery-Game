
from pathlib import Path
import shutil
import sys

try:
    from PIL import Image
except ImportError:
    print("[ERROR] Thieu thu vien Pillow.")
    print("Chay lenh:")
    print("pip install pillow")
    sys.exit(1)

ROOT = Path.cwd()

# Logo chính đang dùng trong menu
shipper_path = ROOT / "assets" / "ui" / "shipper.png"

# Phòng trường hợp bạn để logo ở assets/images
fallback_paths = [
    ROOT / "assets" / "images" / "shipper.png",
    ROOT / "assets" / "shipper.png",
]

if not shipper_path.exists():
    for p in fallback_paths:
        if p.exists():
            logo_path = p
            break

if not shipper_path.exists():
    print("[ERROR] Khong tim thay shipper.png.")
    print("Hay dat shipper vao:")
    print("assets/ui/shipper.png")
    sys.exit(1)

backup_path = shipper_path.with_name(shipper_path.stem + "_backup_before_flip" + shipper_path.suffix)

if not backup_path.exists():
    shutil.copy2(shipper_path, backup_path)
    print(f"[OK] Backup shipper goc: {backup_path}")

img = Image.open(shipper_path).convert("RGBA")

# Lật ngang shipper. Dùng khi ảnh đang bị ngược trái/phải.
flipped = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

flipped.save(shipper_path)
print(f"[OK] Da lat ngang shipper va ghi de vao: {shipper_path}")

print()
print("Chay game:")
print("python game.py --debug")
print()
print("Neu muon quay lai shipper goc:")
print(f"copy \"{backup_path}\" \"{shipper_path}\"")
