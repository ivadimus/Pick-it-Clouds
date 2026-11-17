"""Generate PWA / home-screen icons (sky blue + cloud)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CLOUD_SRC = ROOT / "Assets" / "cloud11.png"
OUT_DIR = ROOT / "icons"


def sky_background(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)
    top = (142, 210, 248)  # #8ed2f8
    mid = (126, 200, 240)  # #7ec8f0 — как в игре
    bottom = (58, 152, 210)  # #3a98d2
    for y in range(size):
        t = y / max(size - 1, 1)
        if t < 0.55:
            k = t / 0.55
            r = int(top[0] + (mid[0] - top[0]) * k)
            g = int(top[1] + (mid[1] - top[1]) * k)
            b = int(top[2] + (mid[2] - top[2]) * k)
        else:
            k = (t - 0.55) / 0.45
            r = int(mid[0] + (bottom[0] - mid[0]) * k)
            g = int(mid[1] + (bottom[1] - mid[1]) * k)
            b = int(mid[2] + (bottom[2] - mid[2]) * k)
        draw.line([(0, y), (size, y)], fill=(r, g, b))

    # мягкое «солнышко» сверху
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    cx, cy = int(size * 0.5), int(size * 0.22)
    radius = int(size * 0.55)
    for i in range(radius, 0, -4):
        alpha = int(28 * (1 - i / radius))
        gdraw.ellipse(
            (cx - i, cy - i, cx + i, cy + i),
            fill=(255, 255, 255, alpha),
        )
    base = img.convert("RGBA")
    base.alpha_composite(glow)
    return base.convert("RGB")


def cloud_rgba(cloud_path: Path) -> Image.Image:
    cloud = Image.open(cloud_path).convert("RGBA")
    pixels = cloud.load()
    w, h = cloud.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            lum = (r + g + b) / 3
            if lum < 28 and max(r, g, b) < 35:
                pixels[x, y] = (r, g, b, 0)
            elif lum < 55 and max(r, g, b) < 60:
                # полупрозрачная кайма чёрного фона ассета
                fade = int(255 * (lum - 28) / 27)
                pixels[x, y] = (r, g, b, min(a, fade))
    return cloud


def compose_icon(size: int, cloud: Image.Image) -> Image.Image:
    bg = sky_background(size)
    canvas = bg.convert("RGBA")
    cw, ch = cloud.size
    target_w = int(size * 0.68)
    scale = target_w / cw
    target_h = max(1, int(ch * scale))
    scaled = cloud.resize((target_w, target_h), Image.Resampling.LANCZOS)
    x = (size - target_w) // 2
    y = (size - target_h) // 2 - int(size * 0.04)
    canvas.paste(scaled, (x, y), scaled)
    return canvas.convert("RGB")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cloud = cloud_rgba(CLOUD_SRC)

    sizes = {
        "apple-touch-icon.png": 180,
        "icon-192.png": 192,
        "icon-512.png": 512,
        "favicon-32x32.png": 32,
        "favicon-16x16.png": 16,
    }
    generated: dict[str, Image.Image] = {}
    for name, px in sizes.items():
        img = compose_icon(px, cloud)
        path = OUT_DIR / name
        img.save(path, "PNG", optimize=True)
        generated[name] = img
        print("wrote", path)

    ico_path = OUT_DIR / "favicon.ico"
    generated["favicon-16x16.png"].save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (32, 32)],
        append_images=[generated["favicon-32x32.png"]],
    )
    print("wrote", ico_path)


if __name__ == "__main__":
    main()