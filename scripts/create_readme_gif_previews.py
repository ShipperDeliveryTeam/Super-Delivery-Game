from pathlib import Path

from PIL import Image


SOURCE_DIR = Path("data/gif")
OUTPUT_DIR = Path("docs/readme-gifs")
GIF_NAMES = [
    "play1.gif",
    "play2.gif",
    "play3.gif",
    "nhom1.gif",
    "nhom2.gif",
    "nhom3.gif",
    "nhom4.gif",
    "nhom5.gif",
    "nhom6.gif",
    "2_nhom1.gif",
    "2_nhom2.gif",
    "2_nhom3.gif",
    "2_nhom4.gif",
    "2_nhom5.gif",
    "2_nhom6.gif",
    "3_nhom1.gif",
    "3_nhom2.gif",
    "3_nhom3.gif",
    "3_nhom4.gif",
    "3_nhom5.gif",
    "3_nhom6.gif",
]


MAX_WIDTH = 560
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
        if not source.exists():
            print(f"{source}: skipped, file not found")
            continue
        create_preview(source, output)
        size_mb = output.stat().st_size / 1024 / 1024
        print(f"{output}: {size_mb:.2f} MB")

    for output_name, source_pattern in EXTRA_PREVIEW_PATTERNS:
        output = OUTPUT_DIR / output_name
        sources = [
            path
            for path in SOURCE_DIR.glob(source_pattern)
            if path.name not in GIF_NAMES
        ]
        if not sources:
            print(f"{source_pattern}: skipped, file not found")
            continue

        create_preview(sources[0], output)
        size_mb = output.stat().st_size / 1024 / 1024
        print(f"{output}: {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
