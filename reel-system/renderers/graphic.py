#!/usr/bin/env python3
"""B-roll renderer B: animated graphics drawn frame by frame with Pillow.

The scan grid. N tiles light up over the run, a share of them flagged. Used for
"somebody checked forty two thousand of them, one in four had a hole in it".

Two rules this file exists to demonstrate:

  * Every animation beat is expressed as a FRACTION of the shot, never as a
    typed timecode. A grid that had its colour changes typed in at 1.91s and
    3.53s silently desyncs the moment the trim speed changes.
  * The tile order is a seeded shuffle. (i * 97 + 13) % N draws visible
    diagonal stripes, which reads as fake.

    python3 renderers/graphic.py out.mp4 --seconds 5 --palette security
"""
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as C
from lib.util import ffmpeg, shuffled
from lib.ease import window, in_out_cubic

COLS, ROWS = 12, 16
GW, GH = 1080, 1240


def scan_grid(out, seconds=5.0, palette="security", flagged=0.25, seed=7,
              beats=(0.10, 0.55, 0.88)):
    """beats are FRACTIONS of the shot: start scanning, start flagging, settle."""
    pal = C.PALETTES[palette]
    out = Path(out)
    n = COLS * ROWS
    order = shuffled(range(n), seed)
    flags = set(shuffled(range(n), seed + 1)[:int(n * flagged)])
    cw, ch = GW // COLS, GH // ROWS
    frames = int(seconds * C.FPS)
    b0, b1, b2 = beats

    enc = subprocess.Popen(
        [ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{GW}x{GH}", "-r", str(C.FPS), "-i", "-",
         "-an", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE)

    for f in range(frames):
        t = f / max(frames - 1, 1)          # 0..1 across the shot
        img = Image.new("RGB", (GW, GH), pal["bg"])
        d = ImageDraw.Draw(img)
        lit = int(n * in_out_cubic(window(t, b0, b1)))
        flag_on = t > b1
        for rank, idx in enumerate(order):
            r, c = divmod(idx, COLS)
            x, y = c * cw, r * ch
            if rank < lit:
                col = pal["accent"] if (flag_on and idx in flags) else pal["accent2"]
            else:
                col = pal["dim"]
            d.rounded_rectangle([x + 4, y + 4, x + cw - 6, y + ch - 6], 8, fill=col)
        # sweep line, so no frame is a dead plate
        sy = int(GH * ((t * 1.6) % 1.0))
        d.rectangle([0, sy, GW, sy + 3], fill=pal["fg"])
        enc.stdin.write(img.tobytes())

    enc.stdin.close()
    enc.wait()
    print(f"[graphic] scan_grid {frames} frames, {len(flags)}/{n} flagged -> {out.name}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--palette", default="security")
    ap.add_argument("--flagged", type=float, default=0.25)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    scan_grid(a.out, a.seconds, a.palette, a.flagged, a.seed)
