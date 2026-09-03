#!/usr/bin/env python3
"""Patch 楽稼ぞ / consulting copy and compose portrait perk sections."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SANS = ROOT / "tools/fonts/NotoSansJP-Black.otf"
SERIF = ROOT / "tools/fonts/NotoSerifJP-Black.otf"
BG_A = Path("/opt/cursor/artifacts/assets/perk-bg-portrait.png")
BG_B = Path("/opt/cursor/artifacts/assets/perk-bg-portrait-b.png")

PERKS_1_10 = [
    "一週間SNS投稿カレンダー",
    "バズるフック50選",
    "短形動画の構成テンプレ10本",
    "競合リサーチシート",
    "運用代行ヒアリングシート",
    "コメント返信テンプレ30",
    "プロフィール改善チェックリスト",
    "ハッシュタグ／検索流入の設計シート",
    "SNSのKPIの見方",
    "炎上回避ガイド",
]
PERKS_11_20 = [
    "AI社員の役割設計シート",
    "Cursor/Claude即戦プロンプト15",
    "司令塔×専門Botの組織図テンプレ",
    "OpenClaw自動化導入チェックリスト",
    "日次ルーチン自動化レシピ",
    "ファイル整理ルールブック",
    "動画切り抜き指示テンプレ",
    "LINEエルメ導線設計図",
    "企業AI顧問の初回診断シート",
    "スキルエンジン受講前診断",
]

GOLD = (236, 196, 72, 255)
GOLD_HI = (255, 236, 160, 230)
GOLD_MID = (210, 168, 58, 255)
GOLD_LO = (120, 78, 18, 255)
GOLD_SHADOW = (58, 28, 2, 255)


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def save_png(im: Image.Image, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    rgb = im.convert("RGB")
    rgb.save(dest, "PNG", optimize=True)
    print(f"wrote {dest} {rgb.size} {dest.stat().st_size}")


def gold_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    size: int,
    face: Path = SERIF,
    anchor: str = "mm",
) -> None:
    f = font(face, size)
    x, y = xy
    for i in range(8, 0, -1):
        draw.text((x + i, y + i + 1), text, font=f, fill=GOLD_SHADOW, anchor=anchor)
    draw.text((x + 2, y + 2), text, font=f, fill=GOLD_LO, anchor=anchor)
    draw.text((x + 1, y + 1), text, font=f, fill=(90, 48, 6, 255), anchor=anchor)
    draw.text((x, y), text, font=f, fill=GOLD, anchor=anchor)
    draw.text((x, y - 2), text, font=f, fill=GOLD_HI, anchor=anchor)


def white_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    size: int,
    anchor: str = "lm",
) -> None:
    f = font(SANS, size)
    x, y = xy
    draw.text((x + 1, y + 2), text, font=f, fill=(20, 8, 30, 220), anchor=anchor)
    draw.text((x, y), text, font=f, fill=(255, 252, 245, 255), anchor=anchor)


def fit_text_size(text: str, max_width: int, start: int, face: Path = SANS) -> int:
    size = start
    while size >= 22:
        f = font(face, size)
        if f.getlength(text) <= max_width:
            return size
        size -= 1
    return 22


def cover_box(
    im: Image.Image,
    box: tuple[int, int, int, int],
    color: tuple[int, int, int],
    radius: int = 16,
    feather: int = 1,
) -> None:
    """Paint the inner field so leftover 3D glyphs cannot show through."""
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    if feather:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))
    tint = Image.new("RGBA", im.size, color + (255,))
    im.paste(tint, (0, 0), mask)


def stamp_strip(
    im: Image.Image,
    box: tuple[int, int, int, int],
    donor: tuple[int, int, int, int],
) -> None:
    """Stretch a clean nearby strip across the lettering band to keep texture."""
    x0, y0, x1, y1 = box
    src = im.crop(donor).resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
    im.paste(src, (x0, y0))


def patch_hero(hero: Image.Image) -> Image.Image:
    # fill the whole inner plaque so 楽稼ぞ cannot peek around a smaller bar
    cover_box(hero, (636, 1410, 974, 1510), (12, 7, 2), radius=24, feather=0)
    draw = ImageDraw.Draw(hero)
    gold_text(draw, (805, 1458), "楽稼ぎスキーム", size=40, face=SERIF)
    return hero


def patch_earn(earn: Image.Image) -> Image.Image:
    cover_box(earn, (36, 750, 1044, 880), (6, 3, 16), radius=4, feather=0)
    draw = ImageDraw.Draw(earn)
    gold_text(draw, (540, 812), "楽稼ぎスキームを複数", size=62, face=SERIF)
    return earn


def patch_cta(cta: Image.Image) -> Image.Image:
    cover_box(cta, (168, 1266, 912, 1416), (20, 12, 26), radius=8, feather=0)
    draw = ImageDraw.Draw(cta)
    gold_text(draw, (540, 1340), "楽稼ぎスキーム", size=52, face=SERIF)
    return cta


def resize_cover(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    tw, th = size
    w, h = im.size
    scale = max(tw / w, th / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return im.crop((left, top, left + tw, top + th))


def draw_gold_bar(canvas: Image.Image, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((x0, y0, x1, y1), radius=22, fill=(8, 2, 14, 220))
    d.rounded_rectangle((x0, y0, x1, y1), radius=22, outline=(232, 188, 72, 255), width=5)
    d.rounded_rectangle((x0 + 7, y0 + 7, x1 - 7, y1 - 7), radius=16, outline=(180, 132, 40, 180), width=2)
    # corner ticks
    for cx, cy, sx, sy in (
        (x0 + 18, y0 + 16, 1, 1),
        (x1 - 18, y0 + 16, -1, 1),
        (x0 + 18, y1 - 16, 1, -1),
        (x1 - 18, y1 - 16, -1, -1),
    ):
        d.line((cx, cy, cx + 16 * sx, cy), fill=GOLD, width=2)
        d.line((cx, cy, cx, cy + 16 * sy), fill=GOLD, width=2)
    canvas.alpha_composite(layer)


def draw_number_badge(canvas: Image.Image, center: tuple[int, int], n: int) -> None:
    cx, cy = center
    r = 46
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse((cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6), fill=(40, 22, 4, 255))
    d.ellipse((cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4), outline=GOLD, width=5)
    d.ellipse((cx - r + 4, cy - r + 4, cx + r - 4, cy + r - 4), outline=(255, 230, 140, 200), width=2)
    d.ellipse((cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8), fill=(12, 4, 18, 240))
    canvas.alpha_composite(layer)
    draw = ImageDraw.Draw(canvas)
    gold_text(draw, (cx, cy + 1), str(n), size=42 if n < 10 else 36, face=SERIF)


def compose_perk_sheet(
    bg_path: Path,
    title: str,
    subtitle: str,
    items: list[str],
    start_n: int,
    footer: str,
    dest: Path,
) -> None:
    W, H = 1080, 2200
    bg = resize_cover(load(bg_path), (W, H))
    # slightly darken the lightning so white type stays readable
    bg = ImageEnhance.Brightness(bg).enhance(0.82)
    canvas = bg.convert("RGBA")
    veil = Image.new("RGBA", (W, H), (6, 2, 16, 70))
    canvas.alpha_composite(veil)

    draw = ImageDraw.Draw(canvas)
    gold_text(draw, (540, 168), title, size=78 if len(title) <= 4 else 68, face=SERIF)
    if subtitle:
        f = font(SANS, 30)
        draw.text((541, 249), subtitle, font=f, fill=(30, 10, 40, 200), anchor="mm")
        draw.text((540, 247), subtitle, font=f, fill=(255, 250, 240, 255), anchor="mm")
        # small gold flourishes beside the subtitle
        sw = int(f.getlength(subtitle))
        draw.line((160, 247, 540 - sw // 2 - 24, 247), fill=GOLD_MID, width=2)
        draw.line((540 + sw // 2 + 24, 247, 920, 247), fill=GOLD_MID, width=2)

    top = 310 if subtitle else 280
    bottom = 2040 if footer else 2100
    row_h = 118
    gap = 18
    usable = bottom - top
    need = 10 * row_h + 9 * gap
    if need > usable:
        row_h = 108
        gap = 14
    y = top
    bar_left = 148
    bar_right = 1010
    for i, name in enumerate(items):
        n = start_n + i
        by0, by1 = y, y + row_h
        draw_gold_bar(canvas, (bar_left, by0, bar_right, by1))
        draw_number_badge(canvas, (102, (by0 + by1) // 2), n)
        max_w = bar_right - bar_left - 56
        size = fit_text_size(name, max_w, 38)
        draw = ImageDraw.Draw(canvas)
        white_text(draw, (bar_left + 28, (by0 + by1) // 2), name, size=size)
        y += row_h + gap

    if footer:
        gold_text(draw, (540, 2118), footer, size=52, face=SERIF)
    save_png(canvas, dest)


def patch_existing() -> None:
    hero = load(ASSETS / "section-hero.png")
    save_png(patch_hero(hero), ASSETS / "section-hero.png")
    earn = load(ASSETS / "section-earn.png")
    save_png(patch_earn(earn), ASSETS / "section-earn.png")
    cta = load(ASSETS / "section-cta.png")
    save_png(patch_cta(cta), ASSETS / "section-cta.png")


def build_perks() -> None:
    compose_perk_sheet(
        BG_A,
        "LINE登録特典",
        "公式LINEに登録すると手に入る",
        PERKS_1_10,
        1,
        "",
        ASSETS / "section-perks-1-10.png",
    )
    compose_perk_sheet(
        BG_B,
        "特典",
        "",
        PERKS_11_20,
        11,
        "LINE登録で受け取る",
        ASSETS / "section-perks-11-20.png",
    )


def main() -> None:
    if not SANS.exists() or not SERIF.exists():
        raise SystemExit("missing Japanese fonts in tools/fonts")
    if not BG_A.exists() or not BG_B.exists():
        raise SystemExit("missing generated perk backgrounds")
    patch_existing()
    build_perks()


if __name__ == "__main__":
    main()
