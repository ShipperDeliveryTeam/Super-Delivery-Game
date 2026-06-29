from pathlib import Path

from PIL import Image


SOURCE_DIR = Path("data/gif")
OUTPUT_DIR = Path("docs/readme-gifs")
GIF_NAMES = [
    "play1.gif",
    "play2.gif",
    "map2.gif",
    "map3.gif",
    "nhom1.gif",
    "nhom2.gif",
    "nhom3.gif",
    "nhom4.gif",
    "nhom5.gif",
    "nhom6.gif",
]

MAX_WIDTH = 420
MAX_FRAMES = 48
MAX_SOURCE_FRAMES = 260
FRAME_DURATION_MS = 110
COLORS = 96


def resize_frame(frame: Image.Image) -> Image.Image:
    frame = frame.convert("RGB")
    width, height = frame.size
    if width <= MAX_WIDTH:
        return frame
    new_height = round(height * MAX_WIDTH / width)
    return frame.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)


def create_preview(source: Path, output: Path) -> None:
    image = Image.open(source)
    total_frames = min(image.n_frames, MAX_SOURCE_FRAMES)
    step = max(1, total_frames // MAX_FRAMES)
    frames = []

    for index in range(0, total_frames, step):
        image.seek(index)
        frames.append(resize_frame(image.copy()))
        if len(frames) >= MAX_FRAMES:
            break

    output.parent.mkdir(parents=True, exist_ok=True)
    first, *rest = frames
    first.save(
        output,
        save_all=True,
        append_images=rest,
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=True,
        colors=COLORS,
    )


def main() -> None:
    for name in GIF_NAMES:
        source = SOURCE_DIR / name
        output = OUTPUT_DIR / name
        create_preview(source, output)
        size_mb = output.stat().st_size / 1024 / 1024
        print(f"{output}: {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
