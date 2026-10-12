#!/usr/bin/env python3
"""Stage 4 of the edit: the furniture.

Persistent banner, progress bar, handle, statement plates, captions, emoji.

The banner owns BANNER_ZONE and nothing else. Content is laid out starting at
CONTENT_TOP, underneath it. A banner that hides the thing it is describing is
worse than no banner, and that one sat over an install command for weeks.

Apple emoji only. Glyphs are rendered out of the system Apple Color Emoji font
into assets/emoji/ once, then loaded as PNGs. If one is missing the build throws.
"""
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from lib.util import need, lint_text
from lib.ease import window, out_back


# ------------------------------------------------------------------ fonts ---
@lru_cache(maxsize=64)
def font(path, size):
    return ImageFont.truetype(str(need(path, "font")), size)


def bold(size):
    return font(C.FONT_BOLD, size)


def reg(size):
    return font(C.FONT_REG, size)


def mono(size):
    return font(C.FONT_MONO, size)


# ------------------------------------------------------------------ emoji ---
# Apple Color Emoji is a bitmap font. It only accepts these strike sizes on this
# machine, verified with a probe. Asking for any other size raises
# "invalid pixel size", so we always bake at 160 and resample down.
EMOJI_STRIKES = (20, 26, 32, 40, 48, 52, 64, 96, 160)


def bake_emoji(char, name, px=160):
    """Render one Apple emoji to assets/emoji/<name>.png. Run once per glyph."""
    C.EMOJI.mkdir(parents=True, exist_ok=True)
    out = C.EMOJI / f"{name}.png"
    f = ImageFont.truetype(str(need(C.APPLE_EMOJI_TTC, "Apple Color Emoji")),
                           EMOJI_STRIKES[-1])
    img = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((120, 120), char, font=f, anchor="mm",
                             embedded_color=True)
    box = img.getbbox()
    if box is None:
        raise RuntimeError(f"emoji {char!r} rendered nothing, no silent fallback")
    img.crop(box).resize((px, px), Image.LANCZOS).save(out)
    return out


@lru_cache(maxsize=64)
def emoji(name, px=110):
    """Load a baked Apple emoji. Missing -> raise. Never a system font fallback."""
    p = need(C.EMOJI / f"{name}.png",
             f"Apple emoji '{name}' (bake it: theme.bake_emoji('X','{name}'))")
    return Image.open(p).convert("RGBA").resize((px, px), Image.LANCZOS)


def glass(name, px=110, pad=0.34):
    """An emoji sitting inside a transparent glass bubble.

    A bare emoji on a dark plate reads as a coloured smudge at phone size, and
    the shield in particular stopped reading as a shield at all. A bubble gives
    it a hard round silhouette to sit in, so the eye resolves the container
    first and the symbol second.

    Built the way real glassmorphism is: a low-alpha white fill, a brighter rim,
    a specular arc in the upper left, and a soft shadow under the lower right.
    Returns RGBA sized (px, px) with the emoji inset by `pad`, so callers can
    swap emoji() for glass() without moving anything.
    """
    from PIL import ImageFilter
    inner = int(px * (1 - pad))
    img = Image.new("RGBA", (px * 4, px * 4), (0, 0, 0, 0))   # 4x, downsampled
    d = ImageDraw.Draw(img)
    S = px * 4
    # drop shadow, offset down-right, so the bubble sits ON the background
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([S * 0.10, S * 0.13, S * 0.97, S * 1.00],
                               fill=(0, 0, 0, 120))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(S * 0.035)))
    # the glass body
    d.ellipse([S * 0.04, S * 0.04, S * 0.96, S * 0.96], fill=(214, 232, 250, 58))
    # rim, brighter at the top where light would catch it
    d.ellipse([S * 0.04, S * 0.04, S * 0.96, S * 0.96],
              outline=(232, 242, 252, 132), width=int(S * 0.017))
    d.arc([S * 0.04, S * 0.04, S * 0.96, S * 0.96], 185, 340,
          fill=(255, 255, 255, 205), width=int(S * 0.022))
    # specular highlight, upper left
    hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([S * 0.15, S * 0.11, S * 0.55, S * 0.36],
                               fill=(255, 255, 255, 120))
    img.alpha_composite(hl.filter(ImageFilter.GaussianBlur(S * 0.020)))
    img = img.resize((px, px), Image.LANCZOS)
    g = emoji(name, inner)
    img.alpha_composite(g, ((px - inner) // 2, (px - inner) // 2))
    return img


# --------------------------------------------------------------- primitives -
def rounded(size, radius, fill):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1],
                                          radius=radius, fill=fill)
    return img


def fit_text(draw, text, f, max_w):
    """Shrink until it fits. Never let a plate overflow its own box."""
    size = f.size
    while size > 18:
        ff = font(f.path, size)
        if draw.textlength(text, font=ff) <= max_w:
            return ff
        size -= 2
    return font(f.path, 18)


# ------------------------------------------------------------------ layers ---
def banner(pal, title, handle):
    """The persistent top strip. Confined to BANNER_ZONE, always."""
    lint_text(title, "banner title")
    x0, y0, x1, y1 = C.BANNER_ZONE
    layer = Image.new("RGBA", (C.W, C.H), (0, 0, 0, 0))
    plate = rounded((x1 - x0 - 96, y1 - y0), 26, pal["accent"] + "e6")
    layer.alpha_composite(plate, (48, y0))
    d = ImageDraw.Draw(layer)
    room = x1 - x0 - 180 - int(d.textlength(handle, font=reg(30))) - 30
    f = fit_text(d, title.upper(), bold(46), room)
    d.text((80, y0 + (y1 - y0) // 2), title.upper(), font=f,
           fill=pal["bg"], anchor="lm")
    d.text((C.W - 80, y0 + (y1 - y0) // 2), handle, font=reg(30),
           fill=pal["bg"], anchor="rm")
    return layer


def progress(pal, t, total):
    """Thin bar pinned to the very top. Always moving, so no frame is dead."""
    layer = Image.new("RGBA", (C.W, C.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = C.TOP_DANGER - 26
    d.rounded_rectangle([48, y, C.W - 48, y + 10], 5, fill=pal["dim"] + "80")
    w = max(10, int((C.W - 96) * min(1.0, t / max(total, 0.01))))
    d.rounded_rectangle([48, y, 48 + w, y + 10], 5, fill=pal["accent"])
    return layer


def plate(pal, text, y, sub=None, emoji_name=None):
    """A statement plate. Sits in the content band, never behind the banner."""
    lint_text(text, "plate")
    if y < C.CONTENT_TOP:
        raise ValueError(f"plate at y={y} is inside the banner zone "
                         f"(content starts at {C.CONTENT_TOP})")
    layer = Image.new("RGBA", (C.W, C.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pad, mw = 40, C.W - 200
    f = fit_text(d, text, bold(72), mw)
    tw = d.textlength(text, font=f)
    h = 132 if not sub else 196
    box = rounded((int(tw) + pad * 2 + (130 if emoji_name else 0), h), 24,
                  pal["bg"] + "e0")
    bx = (C.W - box.width) // 2
    layer.alpha_composite(box, (bx, y))
    tx = bx + pad
    if emoji_name:
        layer.alpha_composite(emoji(emoji_name, 96), (tx, y + (h - 96) // 2))
        tx += 130
    d.text((tx, y + (54 if sub else h // 2)), text, font=f, fill=pal["fg"],
           anchor="lm" if not sub else "lm")
    if sub:
        lint_text(sub, "plate sub")
        d.text((tx, y + 138), sub, font=reg(40), fill=pal["accent2"], anchor="lm")
    return layer


def captions(pal, words, t, max_words=4, pop=True):
    """Burned captions, word window derived from words.json. Never typed times."""
    layer = Image.new("RGBA", (C.W, C.H), (0, 0, 0, 0))
    live = [w for w in words if w["start"] <= t <= w["end"] + 0.12]
    if not live:
        return layer
    i = words.index(live[0])
    lo = max(0, i - (max_words - 1) // 2)
    win = words[lo:lo + max_words]
    d = ImageDraw.Draw(layer)
    f = bold(78)
    parts = [w["w"] for w in win]
    widths = [d.textlength(p + " ", font=f) for p in parts]
    total = sum(widths)
    while total > C.W - 120 and f.size > 40:
        f = bold(f.size - 4)
        widths = [d.textlength(p + " ", font=f) for p in parts]
        total = sum(widths)
    x = (C.W - total) / 2
    y = C.CAPTION_BASELINE
    for p, w, wd in zip(parts, win, widths):
        on = w["start"] <= t <= w["end"] + 0.12
        col = pal["accent"] if on else pal["fg"]
        fw, px = f, x
        if on and pop:
            # pop: 100% -> ~114% -> settle at 108% over the word's first 0.18s
            k = 1 + 0.08 * out_back(window(t, w["start"], w["start"] + 0.18), 3.0)
            fw = bold(int(f.size * k))
            px = x - (d.textlength(p, font=fw) - d.textlength(p, font=f)) / 2
        for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, 3)):
            d.text((px + dx, y + dy), p, font=fw, fill="#000000", anchor="ls")
        d.text((px, y), p, font=fw, fill=col, anchor="ls")
        x += wd
    return layer


if __name__ == "__main__":
    # Bake the emoji set used by the current reels.
    for ch, nm in [("🔒", "lock"), ("💸", "money"), ("⚠️", "warn"), ("✅", "check"),
                   ("🧠", "brain"), ("🔥", "fire"), ("👀", "eyes"), ("🛠️", "tools")]:
        print("baked", bake_emoji(ch, nm))
