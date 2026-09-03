#!/usr/bin/env python3
"""Compose hero (no consulting copy) and 実績 section PNGs from existing LP art + ads-LP screenshots."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PROOF = Path("/tmp/ads-proof")
ORIG_HERO = Path("/tmp/orig-hero.png")
# Dense gold/purple hero before consulting copy was stripped from the top.
HERO_BASE_REV = "1886575a04407536b44f6e87e4c4394d2ef5e7b2"
FONT_CANDIDATES = [
    ROOT / "tools/fonts/NotoSansJP-Black.otf",
    Path("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"),
    Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
]


def font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def orig() -> Image.Image:
    if not ORIG_HERO.exists():
        raise SystemExit("missing /tmp/orig-hero.png — restore original hero first")
    return load(ORIG_HERO)


def fit_width(im: Image.Image, width: int, max_height: int | None = None, max_scale: float = 2.4) -> Image.Image:
    w, h = im.size
    if w <= 0 or h <= 0:
        return im
    scale = width / w
    if scale > max_scale:
        scale = max_scale
        width = max(1, round(w * scale))
    nh = max(1, round(h * scale))
    out = im.resize((width, nh), Image.Resampling.LANCZOS)
    if max_height and out.size[1] > max_height:
        nw = max(1, round(out.size[0] * (max_height / out.size[1])))
        out = out.resize((nw, max_height), Image.Resampling.LANCZOS)
    return out


def gold_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int, anchor: str = "mm") -> None:
    f = font(size)
    x, y = xy
    for i in range(7, 0, -1):
        draw.text((x + i, y + i + 1), text, font=f, fill=(58, 28, 2, 255), anchor=anchor)
    draw.text((x + 1, y + 1), text, font=f, fill=(90, 48, 6, 255), anchor=anchor)
    draw.text((x, y), text, font=f, fill=(236, 196, 72, 255), anchor=anchor)
    draw.text((x, y - 2), text, font=f, fill=(255, 236, 160, 210), anchor=anchor)


def feather_box(size: tuple[int, int], edge: int = 22) -> Image.Image:
    w, h = size
    mask = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(mask)
    for i in range(edge):
        a = int(255 * (i + 1) / edge)
        d.rectangle((i, i, w - 1 - i, h - 1 - i), outline=a)
    return mask.filter(ImageFilter.GaussianBlur(3))


def blend_patch(base: Image.Image, box: tuple[int, int, int, int], patch: Image.Image, edge: int = 22) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    patch = patch.resize((w, h), Image.Resampling.LANCZOS)
    if patch.mode != "RGBA":
        patch = patch.convert("RGBA")
    mask = feather_box((w, h), edge)
    base.paste(patch, (x0, y0), mask)


def circular_paste(base: Image.Image, src: Image.Image, center: tuple[int, int], radius: int) -> None:
    d = radius * 2
    src = src.convert("RGBA")
    # cover-fit into square
    w, h = src.size
    scale = max(d / w, d / h)
    src = src.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.Resampling.LANCZOS)
    w, h = src.size
    left = (w - d) // 2
    top = (h - d) // 2
    src = src.crop((left, top, left + d, top + d))
    mask = Image.new("L", (d, d), 0)
    ImageDraw.Draw(mask).ellipse((1, 1, d - 2, d - 2), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.4))
    x, y = center[0] - radius, center[1] - radius
    base.paste(src, (x, y), mask)


def erase_ribbon(hero: Image.Image) -> None:
    """Remove the leftover maroon ribbon with nearby lightning/starfield."""
    y0, y1 = 528, 678
    x0, x1 = 70, 1010
    left = hero.crop((48, y0, 168, y1))
    right = hero.crop((912, y0, 1032, y1))
    w, h = x1 - x0, y1 - y0
    left = left.resize((w, h), Image.Resampling.LANCZOS)
    right = right.resize((w, h), Image.Resampling.LANCZOS)
    grad = Image.new("L", (w, h))
    gd = ImageDraw.Draw(grad)
    for x in range(w):
        gd.line([(x, 0), (x, h)], fill=int(255 * x / max(1, w - 1)))
    mixed = Image.composite(right, left, grad)
    # add a little sparkle from the starfield just above the ribbon sides
    spark = hero.crop((48, 500, 200, 534)).resize((w, h), Image.Resampling.LANCZOS)
    mixed = Image.blend(mixed, spark, 0.28)
    blend_patch(hero, (x0, y0, x1, y1), mixed, edge=26)


def replace_consult_icon(hero: Image.Image) -> None:
    # Treasure chest now lives on the hero itself; do not require a consult plate.
    chest_src = ASSETS / "section-hero.png"
    if not chest_src.exists():
        return
    chest = load(chest_src).crop((140, 1100, 400, 1360))
    circular_paste(hero, chest, center=(268, 1286), radius=122)

    # Copy the matching right-plaque inner field, then paint 稼がせる.
    # Flatten leftover gold lettering on the donor plaque field.
    src_field = orig().crop((668, 1418, 952, 1490))
    field = src_field.resize((340, 72), Image.Resampling.LANCZOS)
    # flatten any leftover gold lettering on the donor too
    px = field.load()
    for yy in range(field.size[1]):
        for xx in range(field.size[0]):
            r, g, b, a = px[xx, yy]
            if r > 70 and g > 40 and r > b:
                px[xx, yy] = (16, 5, 0, 255)
    hero.paste(field, (108, 1418))
    # wipe only the inner lettering band (not the gold filigree frame)
    region = hero.crop((128, 1424, 428, 1484))
    px = region.load()
    for yy in range(region.size[1]):
        for xx in range(region.size[0]):
            r, g, b, a = px[xx, yy]
            if r > 70 and g > 40 and r + g > b + 40:
                px[xx, yy] = (16, 5, 0, 255)
            elif r + g + b > 140:
                px[xx, yy] = (16, 5, 0, 255)
    hero.paste(region, (128, 1424))
    draw = ImageDraw.Draw(hero)
    gold_text(draw, (278, 1454), "稼がせる", size=46)


def restore_wreath_crown(hero: Image.Image) -> None:
    """The ribbon wipe can nick the crown; copy gold wreath pixels back from the source."""
    src = orig()
    x0, y0, x1, y1 = 300, 658, 780, 760
    dst = hero.crop((x0, y0, x1, y1))
    src_p = src.crop((x0, y0, x1, y1))
    dp, sp = dst.load(), src_p.load()
    for yy in range(src_p.size[1]):
        for xx in range(src_p.size[0]):
            r, g, b, a = sp[xx, yy]
            # gold / cream wreath and crown, not maroon ribbon cloth
            if r > 140 and g > 90 and b < 120 and r > b + 30:
                dp[xx, yy] = (r, g, b, a)
    hero.paste(dst, (x0, y0))


def build_hero() -> Image.Image:
    hero = orig()
    erase_ribbon(hero)
    restore_wreath_crown(hero)
    replace_consult_icon(hero)
    return hero.convert("RGB")


def tile_fill(canvas: Image.Image, tile: Image.Image, box: tuple[int, int, int, int] | None = None) -> None:
    x0, y0, x1, y1 = box or (0, 0, canvas.size[0], canvas.size[1])
    tw, th = tile.size
    yy = y0
    while yy < y1:
        xx = x0
        while xx < x1:
            canvas.paste(tile, (xx, yy))
            xx += tw
        yy += th


def make_header(title: str) -> Image.Image:
    src = orig()
    h = 220
    band = Image.new("RGBA", (1080, h), (10, 2, 24, 255))
    # dark purple starfield, not the スキルエンジン lettering
    tile = src.crop((70, 12, 260, 88))
    tile_fill(band, tile)
    # gold corner ornaments only
    tl = src.crop((0, 0, 210, 88))
    tr = src.crop((870, 0, 1080, 88))
    band.paste(tl, (0, 0), tl)
    band.paste(tr, (870, 0), tr)
    # center diamond flourish, no Japanese title letters
    jewel = src.crop((470, 72, 610, 148))
    band.paste(jewel, (470, 8), jewel)
    draw = ImageDraw.Draw(band)
    gold_text(draw, (540, 132), title, size=88)
    draw.rectangle((360, 188, 720, 194), fill=(232, 188, 72, 255))
    # thin gold side rails
    sl = src.crop((0, 200, 28, 600)).resize((28, h - 20), Image.Resampling.LANCZOS)
    sr = src.crop((1052, 200, 1080, 600)).resize((28, h - 20), Image.Resampling.LANCZOS)
    band.paste(sl, (0, 20))
    band.paste(sr, (1052, 20))
    return band


def make_footer() -> Image.Image:
    src = orig()
    h = 72
    foot = Image.new("RGBA", (1080, h), (8, 2, 20, 255))
    tile = src.crop((70, 12, 260, 72))
    tile_fill(foot, tile)
    tl = src.crop((0, 0, 210, 72)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    tr = src.crop((870, 0, 1080, 72)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    foot.paste(tl, (0, 0), tl)
    foot.paste(tr, (870, 0), tr)
    return foot


def framed_shot(src: Image.Image, width: int = 992) -> Image.Image:
    fitted = fit_width(src.convert("RGBA"), width, max_height=1320)
    pad = 12
    canvas = Image.new("RGBA", (fitted.size[0] + pad * 2, fitted.size[1] + pad * 2), (16, 6, 2, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (2, 2, canvas.size[0] - 3, canvas.size[1] - 3),
        radius=18,
        outline=(232, 188, 72, 255),
        width=6,
    )
    canvas.paste(fitted, (pad, pad))
    return canvas


def stack_section(title: str, shots: list[Image.Image]) -> Image.Image:
    header = make_header(title)
    footer = make_footer()
    cards = [framed_shot(s) for s in shots]
    gap = 26
    body_h = gap + sum(c.size[1] + gap for c in cards)
    src = orig()
    height = header.size[1] + body_h + footer.size[1]
    canvas = Image.new("RGBA", (1080, height), (8, 2, 22, 255))
    canvas.paste(header, (0, 0))
    # purple lightning body — sides of original hero, no copy and no plaques
    tile = src.crop((48, 1688, 200, 1756))
    tile_fill(canvas, tile, (0, header.size[1], 1080, height - footer.size[1]))
    # extra lightning wash from the right of the original ribbon area
    wash = src.crop((900, 540, 1060, 660)).resize((1080, max(200, body_h)), Image.Resampling.LANCZOS)
    wash = ImageEnhance.Brightness(wash).enhance(0.55)
    wash.putalpha(90)
    canvas.paste(wash, (0, header.size[1]), wash)
    sl = src.crop((0, 400, 30, 1500))
    sr = src.crop((1050, 400, 1080, 1500))
    for yy in range(header.size[1], height - footer.size[1], sl.size[1]):
        canvas.paste(sl, (0, yy))
        canvas.paste(sr, (1050, yy))
    canvas.paste(footer, (0, height - footer.size[1]))

    yy = header.size[1] + gap
    for card in cards:
        x = (1080 - card.size[0]) // 2
        canvas.paste(card, (x, yy), card)
        yy += card.size[1] + gap
    return canvas.convert("RGB")


def build_results() -> dict[str, Image.Image]:
    def p(name: str) -> Image.Image:
        return load(PROOF / name)

    return {
        "section-results-1.png": stack_section(
            "実績",
            [
                p("proof-revenue.png"),
                p("proof-payout.jpg"),
                p("proof-revenue-11375.jpg"),
                p("proof-live-4318.jpg"),
            ],
        ),
        "section-results-2.png": stack_section(
            "実績",
            [
                p("proof-buzzpost-2871.png"),
                p("proof-line-500k.jpg"),
            ],
        ),
        "section-results-3.png": stack_section(
            "実績",
            [
                p("analytics-87m.png"),
                p("analytics-19m.png"),
                p("analytics-8m.png"),
                p("analytics-3m.png"),
            ],
        ),
        "section-results-4.png": stack_section(
            "実績",
            [
                p("agency-grid.png"),
                p("voice-follow.png"),
                p("proof-analytics.jpg"),
                p("voice-analytics.png"),
            ],
        ),
    }


def save_png(im: Image.Image, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(dest, "PNG", optimize=True)
    print(f"wrote {dest} {im.size} {dest.stat().st_size}")


def main() -> None:
    import subprocess

    subprocess.check_call(
        ["git", "-C", str(ROOT), "show", f"{HERO_BASE_REV}:assets/section-hero.png"],
        stdout=open(ORIG_HERO, "wb"),
    )
    save_png(build_hero(), ASSETS / "section-hero.png")
    for name, im in build_results().items():
        save_png(im, ASSETS / name)


if __name__ == "__main__":
    main()
