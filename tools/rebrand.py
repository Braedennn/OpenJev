"""Rebrand the DeepSeek Harness fork to OpenJev.

- Renames user-visible product strings in source, docs, and configs.
- Replaces brand images (favicons, wordmark, desktop icons, installer art, badge)
  with generated OpenJev assets.
- Leaves upstream license/attribution and internal package ids untouched.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"E:\OpenJev\harness")

SKIP_DIRS = {
    "node_modules", ".git", "snapshots", "tests", "__snapshots__", "fixtures",
    "dist", "lib", "artifacts", "coverage", ".cache", ".turbo", ".pnpm-store",
    "patches", "vendor", ".tmp",
}
SKIP_FILES = {"pnpm-lock.yaml", "THIRD_PARTY_NOTICES.md"}

TEXT_EXTS = {
    ".ts", ".tsx", ".js", ".mjs", ".cjs", ".json", ".md", ".yaml", ".yml",
    ".html", ".css", ".toml", ".xml", ".webmanifest", ".txt",
}

RULES: list[tuple[str, str]] = [
    ("DeepSeek Harness", "OpenJev"),
    ("DSH Local Build", "OpenJev Local Build"),
    ("DSH 本地构建", "OpenJev 本地构建"),
    ("Harness developers", "OpenJev developers"),
    ("Harness developer", "OpenJev developer"),
    ("Harness 开发者", "OpenJev 开发者"),
    ("DSH plugin ecosystem", "OpenJev plugin ecosystem"),
    ("加入 DSH 插件生态", "加入 OpenJev 插件生态"),
    ("powered by dsh", "powered by OpenJev"),
    (".description('dsh: boot", ".description('openjev: boot"),
    ("deepseek-harness-${version}", "openjev-${version}"),
    ('"short_name": "DSH"', '"short_name": "OpenJev"'),
]


def iter_text_files() -> "list[Path]":
    out: list[Path] = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXTS:
            continue
        if p.name in SKIP_FILES:
            continue
        parts = set(p.relative_to(ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        out.append(p)
    return out


def apply_text_rules() -> "dict[str, int]":
    counts = {old: 0 for old, _ in RULES}
    changed = 0
    for path in iter_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        original = text
        for old, new in RULES:
            n = text.count(old)
            if n:
                text = text.replace(old, new)
                counts[old] += n
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed += 1
    print(f"text files rewritten: {changed}")
    for old, n in counts.items():
        print(f"  {n:5d}  {old!r}")
    return counts


def load_font(size: int):
    from PIL import ImageFont

    for name in ("segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"):
        p = Path(r"C:\Windows\Fonts") / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


A_TOP = (6, 182, 212)      # cyan-500
A_BOTTOM = (99, 102, 241)  # indigo-500


def gradient_tile(size: int, radius_ratio: float = 0.22):
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad = Image.new("RGBA", (size, size))
    for y in range(size):
        t = y / max(1, size - 1)
        grad.putpixel((0, y), (*[round(a + (b - a) * t) for a, b in zip(A_TOP, A_BOTTOM)], 255))
    grad = grad.resize((size, size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * radius_ratio), fill=255)
    img.paste(grad, (0, 0), mask)
    return img


def draw_j(img, size: int, color=(255, 255, 255, 255)):
    from PIL import ImageDraw

    d = ImageDraw.Draw(img)
    s = size
    w = max(2, int(s * 0.085))
    cap = w // 2
    x_stem = s * 0.635
    y_top, y_mid = s * 0.30, s * 0.575
    cy, r = y_mid, s * 0.145
    left, right = x_stem - r, x_stem + r
    d.arc((left, cy - r, right, cy + r), start=0, end=180, fill=color, width=w)
    d.line((x_stem, y_top, x_stem, y_mid), fill=color, width=w)
    d.ellipse((x_stem - cap, y_top - cap, x_stem + cap, y_top + cap), fill=color)
    d.line((left, cy, left, cy - s * 0.105), fill=color, width=w)
    d.ellipse((left - cap, cy - s * 0.105 - cap, left + cap, cy - s * 0.105 + cap), fill=color)
    dot_r = s * 0.055
    cx, cyy = s * 0.315, s * 0.325
    d.ellipse((cx - dot_r, cyy - dot_r, cx + dot_r, cyy + dot_r), fill=color)
    return img


def icon_png(size: int, path: Path):
    img = draw_j(gradient_tile(size), size)
    img.save(path)


def icon_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <defs>
    <linearGradient id="openjev" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
      <stop stop-color="#06B6D4"/>
      <stop offset="1" stop-color="#6366F1"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="15" fill="url(#openjev)"/>
  <path d="M40.6 19v17.4a9.3 9.3 0 0 1-18.6 0" stroke="#fff" stroke-width="5.4" stroke-linecap="round" fill="none"/>
  <path d="M22 36.4v-6.2" stroke="#fff" stroke-width="5.4" stroke-linecap="round"/>
  <circle cx="20.2" cy="20.8" r="3.5" fill="#fff"/>
</svg>
"""


def wordmark_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 232 56" fill="none">
  <defs>
    <linearGradient id="openjev-w" x1="4" y1="6" x2="50" y2="52" gradientUnits="userSpaceOnUse">
      <stop stop-color="#06B6D4"/>
      <stop offset="1" stop-color="#6366F1"/>
    </linearGradient>
    <style>
      @media (prefers-color-scheme: dark) { text { fill: #fff; } }
    </style>
  </defs>
  <rect x="4" y="6" width="46" height="46" rx="11" fill="url(#openjev-w)"/>
  <path d="M33.2 20.5v12.6a6.7 6.7 0 0 1-13.4 0" stroke="#fff" stroke-width="3.9" stroke-linecap="round" fill="none"/>
  <path d="M19.8 33.1v-4.5" stroke="#fff" stroke-width="3.9" stroke-linecap="round"/>
  <circle cx="18.5" cy="21.8" r="2.5" fill="#fff"/>
  <text x="62" y="39" font-family="Segoe UI, system-ui, -apple-system, sans-serif" font-size="27" font-weight="700" fill="#0F172A">OpenJev</text>
</svg>
"""


def favicon_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 50 50" fill="none">
  <defs>
    <linearGradient id="openjev-f" x1="0" y1="0" x2="50" y2="50" gradientUnits="userSpaceOnUse">
      <stop stop-color="#06B6D4"/>
      <stop offset="1" stop-color="#6366F1"/>
    </linearGradient>
  </defs>
  <rect width="50" height="50" rx="12" fill="url(#openjev-f)"/>
  <path d="M31.8 15.2v13.5a7.3 7.3 0 0 1-14.6 0" stroke="#fff" stroke-width="4.2" stroke-linecap="round" fill="none"/>
  <path d="M17.2 28.7v-4.9" stroke="#fff" stroke-width="4.2" stroke-linecap="round"/>
  <circle cx="15.8" cy="16.8" r="2.7" fill="#fff"/>
</svg>
"""


def brand_banner(path: Path, size: tuple[int, int], dark: bool):
    from PIL import Image, ImageDraw

    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    tile_h = int(h * 0.62)
    tile = draw_j(gradient_tile(tile_h, 0.24), tile_h)
    x = int(w * 0.03)
    img.paste(tile, (x, (h - tile_h) // 2), tile)
    text = "OpenJev"
    fg = (255, 255, 255, 255) if dark else (15, 23, 42, 255)
    font = load_font(int(h * 0.46))
    d = ImageDraw.Draw(img)
    d.text((x + tile_h + int(w * 0.035), h // 2), text, font=font, fill=fg, anchor="lm")
    img.save(path)


def sidebar_png(path: Path, size: tuple[int, int]):
    from PIL import Image, ImageDraw

    w, h = size
    img = gradient_tile(max(w, h), 0.0).resize(size)
    tile = draw_j(gradient_tile(int(w * 0.62), 0.24), int(w * 0.62))
    img.paste(tile, ((w - tile.width) // 2, int(h * 0.22)), tile)
    font = load_font(int(w * 0.18))
    d = ImageDraw.Draw(img)
    d.text((w // 2, int(h * 0.62)), "OpenJev", font=font, fill=(255, 255, 255, 255), anchor="mm")
    img.save(path)


def badge_png(path: Path, size: tuple[int, int] = (726, 120)):
    from PIL import Image, ImageDraw

    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=(*A_BOTTOM, 255))
    tile_h = int(h * 0.62)
    tile = draw_j(gradient_tile(tile_h, 0.24), tile_h)
    x = int(h * 0.28)
    img.paste(tile, (x, (h - tile_h) // 2), tile)
    font = load_font(int(h * 0.42))
    d.text((x + tile_h + int(h * 0.22), h // 2), "powered by OpenJev", font=font, fill=(255, 255, 255, 255), anchor="lm")
    img.save(path)


def write_assets():
    web = ROOT / "apps" / "web" / "public"
    site = ROOT / "website" / "public"
    (web / "favicon.svg").write_text(favicon_svg(), encoding="utf-8")
    (site / "favicon.svg").write_text(favicon_svg(), encoding="utf-8")
    (site / "wordmark.svg").write_text(wordmark_svg(), encoding="utf-8")

    res = ROOT / "apps" / "desktop" / "resources"
    for name in ("icon.svg", "icon-windows.svg", "icon-macos.svg"):
        (res / name).write_text(icon_svg(), encoding="utf-8")
    icon_png(1024, res / "icon.png")
    icon_png(1024, res / "icon-windows.png")
    icon_png(1024, res / "icon-macos.png")

    inst = ROOT / "apps" / "desktop" / "installer" / "assets"
    brand_banner(inst / "brand.png", (600, 196), dark=False)
    brand_banner(inst / "brand-2x.png", (1200, 392), dark=False)
    brand_banner(inst / "brand-dark.png", (600, 196), dark=True)
    brand_banner(inst / "brand-dark-2x.png", (1200, 392), dark=True)
    sidebar_png(inst / "uninstaller-sidebar.png", (164, 314))

    badge = ROOT / "packages" / "skill" / "skill-badge" / "assets" / "dsh-badge.png"
    if badge.exists():
        badge_png(badge)
    print("assets written: favicons, wordmark, desktop icons, installer art, badge")


if __name__ == "__main__":
    if not ROOT.exists():
        sys.exit(f"missing {ROOT}")
    counts = apply_text_rules()
    write_assets()
    print("done")
