#!/usr/bin/env python3
"""B-roll renderer D: the typographic statement plate.

This is the shape that carries the FACELESS cut. Decoded off the Mars Rover
reel, which has no presenter at all and is held together entirely by these:

    W H A T   I T   A C T U A L L Y   T A K E S      <- small, letterspaced, dim
    $1,600      in parts                             <- big accent value + label
    100+        hours to build
    6           wheels, all independently driven

and the single value variant:

    T H E   P A R T   N O B O D Y   E X P E C T S
    Apache 2.0                                       <- big accent
    Build it. Sell it. Nobody stops you.             <- supporting lines

Rules kept from graphic.py: beats are FRACTIONS of the shot, never timecodes,
and there is always something moving so no frame is a dead plate. Here the
motion is the rows arriving one at a time and a rule that draws itself under
each one.

    python3 renderers/plate.py out.mp4 --seconds 4 --palette money \
        --label "what it costs you" \
        --row '$16|a month, per person' --row '$1,920|a year, for ten of you'
"""
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as C
from lib.util import ffmpeg, need
from lib.ease import out_cubic, in_out_cubic

GW, GH = 1080, 1240
PAD = 70


def _f(path, size):
    return ImageFont.truetype(str(need(path, "font")), size)


def _rgb(hexs):
    hexs = hexs.lstrip("#")
    return tuple(int(hexs[i:i + 2], 16) for i in (0, 2, 4))


def _spaced(s):
    return "  ".join(s.upper())


def plate(out, seconds=4.0, palette="money", label="", rows=(), sub=(), seed=3,
          beats=(0.06, 0.72)):
    """beats: first row lands, last row settled. Rows arrive evenly between."""
    pal = C.PALETTES[palette]
    bg, fg, accent, dim = (_rgb(pal["bg"]), _rgb(pal["fg"]),
                           _rgb(pal["accent"]), _rgb(pal["dim"]))
    out = Path(out)
    frames = int(seconds * C.FPS)
    b0, b1 = beats

    f_lab = _f(C.FONT_REG, 30)
    f_big = _f(C.FONT_BOLD, 108)
    f_val = _f(C.FONT_REG, 34)
    f_sub = _f(C.FONT_REG, 38)

    enc = subprocess.Popen(
        [ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{GW}x{GH}", "-r", str(C.FPS), "-i", "-",
         "-an", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE)

    n = max(len(rows), 1)
    for fr in range(frames):
        t = fr / max(frames - 1, 1)
        img = Image.new("RGB", (GW, GH), bg)
        d = ImageDraw.Draw(img)

        if label:
            d.text((PAD, 60), _spaced(label), font=f_lab, fill=dim)

        y = 150
        for i, row in enumerate(rows):
            # each row has its own slice of the window between the two beats
            start = b0 + (b1 - b0) * (i / n)
            p = max(0.0, min(1.0, (t - start) / max((b1 - b0) / n * 0.9, 1e-6)))
            if p <= 0:
                y += 190
                continue
            big, lab = (row.split("|", 1) + [""])[:2]
            slide = int((1 - out_cubic(p)) * 70)
            d.text((PAD, y + slide), big, font=f_big, fill=accent)
            bx = d.textbbox((0, 0), big, font=f_big)
            if lab:
                d.text((PAD + (bx[2] - bx[0]) + 34, y + 62 + slide), lab.strip(),
                       font=f_val, fill=fg)
            # the rule draws itself left to right under the row
            d.rectangle([PAD, y + 148, PAD + int((GW - PAD * 2) * in_out_cubic(p)), y + 150],
                        fill=dim)
            y += 190

        sy = y + 24
        for i, s in enumerate(sub):
            p = max(0.0, min(1.0, (t - (b1 - 0.04) - i * 0.05) / 0.14))
            if p <= 0:
                continue
            d.text((PAD, sy + int((1 - out_cubic(p)) * 40)), s, font=f_sub,
                   fill=fg if i == 0 else dim)
            sy += 52

        enc.stdin.write(img.tobytes())

    enc.stdin.close()
    enc.wait()
    print(f"[plate] {frames} frames, label={label!r}, {len(rows)} row(s) -> {out.name}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--palette", default="money")
    ap.add_argument("--label", default="")
    ap.add_argument("--row", action="append", default=[],
                    help="'BIG|small label', repeatable")
    ap.add_argument("--sub", action="append", default=[])
    a = ap.parse_args()
    plate(a.out, a.seconds, a.palette, a.label, a.row, a.sub)
