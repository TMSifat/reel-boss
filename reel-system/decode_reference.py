#!/usr/bin/env python3
"""Stage 0: MEASURE a reference reel instead of describing it.

When someone says "make it like this one" and hands you a file, the first job is
not editing. It is decoding. This was done by hand three times in one session
before it became a script, and every single design decision that followed came
out of a number this produces, not out of watching the video.

    python3 decode_reference.py "path/to/reference.mp4" [more.mp4 ...]

What it reports, and why each one changed a build:

  container       runtime, frame, fps. Sets the ceiling you are working to.
  loudness        their integrated LUFS and true peak. Tells you what the
                  account actually masters to, which may not be the spec.
  cuts            scene change timestamps. Cuts per second is the single best
                  proxy for how fast the edit feels.
  palette         the accent colour SAMPLED FROM PIXELS. Never eyeball a colour
                  off a contact sheet; a reference read as gold turned out to be
                  #f6971c orange, which changed what could legally be copied.
  bands           the horizontal content bands. This is how a stacked split
                  screen gives up its exact geometry: top panel y264..862,
                  gutter 24, bottom y886..1267. Measured, not guessed.
  transcript      their script. Word count over runtime gives words per second,
                  which is the real pacing constraint on your own script.

It also writes a contact sheet and full resolution frames at the cut points,
because a 300px tile lies in both directions and layout has to be judged at 1:1.

Nothing here is destructive and nothing touches the reference file.
"""
import collections
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.util import ffmpeg, ffprobe  # noqa: E402

OUT = Path(tempfile.gettempdir()) / "decode_reference"


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def container(f):
    j = json.loads(sh([ffprobe(), "-v", "error", "-print_format", "json",
                       "-show_format", "-show_streams", str(f)]))
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    num, den = v["r_frame_rate"].split("/")
    return {
        "dur": float(j["format"]["duration"]),
        "size": int(j["format"]["size"]),
        "w": int(v["width"]), "h": int(v["height"]),
        "fps": round(int(num) / int(den), 2),
        "vkbps": round(int(v.get("bit_rate", 0)) / 1000),
        "ach": a["channels"] if a else 0,
        "asr": a["sample_rate"] if a else 0,
    }


def loudness(f):
    err = subprocess.run([ffmpeg(), "-hide_banner", "-nostats", "-i", str(f),
                          "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stderr
    blob = err[err.rfind("{"):err.rfind("}") + 1]
    try:
        d = json.loads(blob)
        return float(d["input_i"]), float(d["input_tp"]), float(d["input_lra"])
    except Exception:
        return None, None, None


def cuts(f, thresh=0.25):
    err = subprocess.run([ffmpeg(), "-hide_banner", "-nostats", "-i", str(f),
                          "-vf", f"select='gt(scene,{thresh})',showinfo",
                          "-f", "null", "-"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stderr
    ts = [float(x.split(":")[1]) for x in err.split() if x.startswith("pts_time:")]
    # collapse bursts: a dissolve fires the detector on consecutive frames
    keep = []
    for t in ts:
        if not keep or t - keep[-1] > 0.25:
            keep.append(t)
    return keep


def palette(f, at):
    """Sample the real pixels. The accent is the most common SATURATED colour."""
    png = OUT / "_pal.png"
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-ss", str(at), "-i", str(f),
                    "-frames:v", "1", str(png)], check=True)
    im = Image.open(png).convert("RGB").resize((216, 384))
    px = list(im.getdata())
    c = collections.Counter(px)
    bg = c.most_common(1)[0][0]
    sat = [(v, p) for p, v in c.items()
           if max(p) - min(p) > 60 and max(p) > 90]
    sat.sort(reverse=True)
    return {
        "bg": "#%02x%02x%02x" % bg,
        "accents": ["#%02x%02x%02x" % p for _, p in sat[:4]],
    }


def bands(f, at, dark=12, min_h=25):
    """Horizontal content bands. This is how a stacked layout gives up its
    geometry: rows whose mean luminance is above `dark` are content."""
    png = OUT / "_band.png"
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-ss", str(at), "-i", str(f),
                    "-frames:v", "1", str(png)], check=True)
    a = np.array(Image.open(png).convert("L"))
    row = a.mean(axis=1)
    out, s = [], None
    for i, d in enumerate(row < dark):
        if not d and s is None:
            s = i
        if d and s is not None:
            if i - s > min_h:
                out.append((s, i, i - s))
            s = None
    if s is not None and len(row) - s > min_h:
        out.append((s, len(row), len(row) - s))
    return out


def transcript(f):
    wav = OUT / (Path(f).stem.replace(" ", "_") + ".wav")
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-i", str(f),
                    "-ar", "16000", "-ac", "1", str(wav)], check=True)
    # same engine as stt.py, so it runs anywhere pip does (was a Mac whisper-cli path)
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return "(faster-whisper not installed: pip install faster-whisper)"
    segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(str(wav))
    return " ".join(s.text.strip() for s in segs)


def sheet(f, stem, cols=5, rows=5):
    p = OUT / f"{stem}_sheet.jpg"
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-i", str(f),
                    "-vf", f"fps=1,scale=360:-1,tile={cols}x{rows}",
                    "-frames:v", "1", str(p)], check=True)
    return p


def frame0(f):
    """Audio level in the opening moments, in dBFS RMS.

    Added 2026-08-22. This is the metric that separated @billy.coder's two hits
    from its nine flops: both hits sit at about -17 dBFS at 0.1s, the 89 view
    reel was at -64.6. Silence on frame 0 is the loudest predictor of a dead
    post the account has produced. ffmpeg's own volumedetect prints nothing on
    this build, so the PCM is decoded and measured here directly.
    """
    out = {}
    r = subprocess.run(
        [ffmpeg(), "-v", "error", "-i", str(f), "-t", "1.0",
         "-ac", "1", "-ar", "48000", "-f", "s16le", "-"],
        capture_output=True)
    a = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float64) / 32768.0
    if a.size == 0:
        return None
    for label, n in (("0.1s", 4800), ("0.3s", 14400), ("1.0s", 48000)):
        seg = a[:n]
        if seg.size == 0:
            continue
        rms = float(np.sqrt(np.mean(seg ** 2)))
        out[label] = 20 * np.log10(rms) if rms > 0 else -99.0
    return out


def decode(f):
    f = Path(f)
    stem = f.stem.replace(" ", "_")[:28]
    print("=" * 70)
    print(f.name)
    print("=" * 70)

    c = container(f)
    print(f"  {c['dur']:.2f}s   {c['w']}x{c['h']} @ {c['fps']}fps   "
          f"{c['vkbps']}kbps video   {c['size']:,} bytes")
    if c["ach"]:
        print(f"  audio {c['ach']}ch {c['asr']}Hz")

    f0 = frame0(f)
    if f0:
        parts = "   ".join(f"{k} {v:6.1f}" for k, v in f0.items())
        verdict = "LOUD, good" if f0.get("0.1s", -99) > -30 else "SILENT OPENER, this is the dead-post signature"
        print(f"  frame 0   dBFS RMS  {parts}   <- {verdict}")

    i, tp, lra = loudness(f)
    if i is not None:
        print(f"  loudness  {i:.2f} LUFS   true peak {tp:.2f} dBTP   LRA {lra:.2f}")

    ct = cuts(f)
    if ct:
        print(f"  cuts      {len(ct)} in {c['dur']:.1f}s "
              f"= {len(ct) / c['dur']:.2f}/s")
        print(f"            {', '.join(f'{t:.2f}' for t in ct[:14])}")

    mid = c["dur"] * 0.55
    p = palette(f, mid)
    print(f"  palette   bg {p['bg']}   accents {' '.join(p['accents'])}")
    print("            (sampled from pixels; do NOT eyeball this off a sheet)")

    b = bands(f, mid)
    if b:
        print(f"  bands @ {mid:.1f}s   (y0, y1, height)")
        for y0, y1, h in b:
            print(f"            {y0:5d} .. {y1:5d}   {h:5d}")
        for k in range(len(b) - 1):
            print(f"            gutter {b[k][1]} -> {b[k + 1][0]} "
                  f"= {b[k + 1][0] - b[k][1]}px")

    t = transcript(f)
    words = len(t.split())
    print(f"  script    {words} words, {words / c['dur']:.2f} words/s")
    print(f"            {t[:320]}")

    s = sheet(f, stem)
    print(f"  sheet     {s}")
    for n, at in enumerate(ct[:6] or [mid]):
        fr = OUT / f"{stem}_cut{n}.png"
        subprocess.run([ffmpeg(), "-y", "-v", "error", "-ss", str(at + 0.15),
                        "-i", str(f), "-frames:v", "1", str(fr)], check=True)
    print(f"  frames    {stem}_cut*.png  (LOOK at these at full size)")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sys.argv[1:]:
        decode(f)
    print(f"everything written to {OUT}")
