#!/usr/bin/env python3
"""B-roll renderer C: the per-seat cost burn.

Built for beat 1 of the formula, "a named paid thing loses". A row of seats
fills up one at a time and a live counter multiplies the published per seat
price by the seats on screen, so the viewer watches their own bill assemble
itself. Then the whole thing drops to zero.

Why this exists as its own renderer rather than a plate: the artifact rule is
"no dead frames". A static price card is a wasted second. This is the same
information with something happening in every frame.

Rules this file follows, same as graphic.py:

  * Every beat is a FRACTION of the shot, never a typed timecode, so a change
    to the trim speed retimes it instead of desyncing it.
  * NO INVENTED NUMBERS. The only input is the published per seat price. The
    monthly and annual figures are arithmetic on it and the arithmetic is
    printed on completion so it can be checked against the source.
  * The word "free" never appears. Zero is drawn as $0.
  * Seeded shuffle for the seat fill order, never i*97+13.

    python3 renderers/seatcost.py out.mp4 --seconds 5 --palette money \
        --price 16 --seats 10
"""
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as C
from lib.util import ffmpeg, need, shuffled
from lib.ease import window, in_out_cubic

GW, GH = 1080, 1240
COLS = 5


def _font(path, size):
    return ImageFont.truetype(str(need(path, "font")), size)


def _centre(d, text, f, cx, y, fill):
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f)
    d.text((cx - (x1 - x0) / 2 - x0, y - y0), text, font=f, fill=fill)
    return y1 - y0


def _seat(d, x, y, w, h, col, filled, edge):
    """A seat glyph. Deliberately not an emoji: it has to tint per state."""
    d.rounded_rectangle([x, y + h * 0.34, x + w, y + h], 14,
                        fill=col if filled else None,
                        outline=edge, width=4)
    r = w * 0.20
    cx = x + w / 2
    cy = y + h * 0.20
    d.ellipse([cx - r, cy - r, cx + r, cy + r],
              fill=col if filled else None, outline=edge, width=4)


def seat_cost(out, seconds=5.0, palette="money", price=16, seats=10, seed=11,
              beats=(0.05, 0.50, 0.66, 0.84)):
    """beats: start filling, monthly locked, flip to annual, drop to zero."""
    pal = C.PALETTES[palette]
    out = Path(out)
    monthly = price * seats
    annual = monthly * 12
    order = shuffled(range(seats), seed)
    frames = int(seconds * C.FPS)
    b0, b1, b2, b3 = beats

    f_huge = _font(C.FONT_BOLD, 190)
    f_mid = _font(C.FONT_BOLD, 74)
    f_lab = _font(C.FONT_REG, 40)

    sw, sh = 150, 170
    gap = 26
    grid_w = COLS * sw + (COLS - 1) * gap
    x0 = (GW - grid_w) // 2
    y0 = 806

    enc = subprocess.Popen(
        [ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{GW}x{GH}", "-r", str(C.FPS), "-i", "-",
         "-an", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE)

    for fr in range(frames):
        t = fr / max(frames - 1, 1)
        img = Image.new("RGB", (GW, GH), pal["bg"])
        d = ImageDraw.Draw(img)

        fill_p = in_out_cubic(window(t, b0, b1))
        lit = int(round(seats * fill_p))
        zeroing = t >= b3

        # counter. counts up with the seats, flips to annual, then falls to zero.
        if zeroing:
            z = in_out_cubic(window(t, b3, 1.0))
            value = int(round(annual * (1.0 - z)))
            label = "on your own server"
            col = pal["accent2"]
        elif t >= b2:
            value = annual
            label = "a year"
            col = pal["accent"]
        else:
            value = int(round(price * seats * fill_p))  # lands exactly on monthly
            label = "a month"
            col = pal["accent"]

        _centre(d, f"${value:,}", f_huge, GW // 2, 300, col)
        _centre(d, label, f_lab, GW // 2, 520, pal["dim"])
        _centre(d, f"{lit} on the team" if not zeroing else "as many as you want",
                f_mid, GW // 2, 620, pal["fg"])

        # the seats
        for rank, idx in enumerate(order):
            r, c = divmod(idx, COLS)
            x = x0 + c * (sw + gap)
            y = y0 + r * (sh + gap)
            on = rank < lit
            col_s = pal["accent2"] if zeroing else (pal["accent"] if on else pal["dim"])
            _seat(d, x, y, sw, sh, col_s, on or zeroing, pal["dim"])

        # a moving edge so no frame is a dead plate
        sx = int(GW * ((t * 1.4) % 1.0))
        d.rectangle([sx, 0, sx + 4, GH], fill=pal["dim"])

        enc.stdin.write(img.tobytes())

    enc.stdin.close()
    enc.wait()
    print(f"[seatcost] {frames} frames, {seats} seats @ ${price} "
          f"= ${monthly}/mo = ${annual}/yr -> {out.name}")
    print(f"[seatcost] ARITHMETIC ONLY. ${price} is the published per seat price, "
          f"verify it the day you shoot.")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--palette", default="money")
    ap.add_argument("--price", type=int, required=True,
                    help="published per seat monthly price, no default on purpose")
    ap.add_argument("--seats", type=int, default=10)
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    seat_cost(a.out, a.seconds, a.palette, a.price, a.seats, a.seed)
