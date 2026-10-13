#!/usr/bin/env python3
"""Preflight for the reel pipeline. Run it before stage 0 on any new machine.

Every check is something that otherwise fails halfway through a build, after
the keyword is already burned. Exits 0 when the whole pipeline can run.

  python scripts/doctor.py
"""
import importlib.util
import shutil
import sys
from pathlib import Path

RS = Path(__file__).resolve().parent.parent / "reel-system"
sys.path.insert(0, str(RS))
import config as C  # noqa: E402

bad = 0


def check(ok, what, fix=""):
    global bad
    print(f"  {'ok  ' if ok else 'MISS'}  {what}" + ("" if ok else f"\n        fix: {fix}"))
    bad += not ok


print(f"python {sys.version.split()[0]} on {sys.platform}\n")
print("python packages")
for mod, pip, stage in [("PIL", "Pillow", "every graphic"), ("numpy", "numpy", "matte"),
                        ("faster_whisper", "faster-whisper", "stt.py"),
                        ("playwright", "playwright", "screenrec.py"),
                        ("yt_dlp", "yt-dlp", "pull_reference.py"),
                        ("yt_dlp_ejs", "yt-dlp-ejs", "YouTube 403 fix"),
                        ("gallery_dl", "gallery-dl", "pull_reference.py, instagram"),
                        ("kokoro_onnx", "kokoro-onnx", "voice.py, the local voice"),
                        ("soundfile", "soundfile", "voice.py")]:
    check(importlib.util.find_spec(mod), f"{pip:<15} {stage}", f"pip install {pip}")

try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ok = Path(p.chromium.executable_path).exists()
except Exception:
    ok = False
check(ok, "playwright chromium browser", "python -m playwright install chromium")

print("\nbinaries on PATH")
win = sys.platform == "win32"
ff = ("winget install Gyan.FFmpeg, or unzip github.com/BtbN/FFmpeg-Builds and add bin to PATH"
      if win else "brew install ffmpeg | apt install ffmpeg")
for exe, fix in [("ffmpeg", ff), ("ffprobe", ff), ("node", "install Node.js, yt-dlp's YouTube JS runtime")]:
    check(shutil.which(exe), exe, fix)

print("\nassets")
for name in ("FONT_BOLD", "FONT_REG", "FONT_MONO"):
    p = Path(getattr(C, name))
    check(p.exists(), f"{name:<10} {p}", f"set REEL_{name} to a .ttf that exists")
n = len(list(C.EMOJI.glob("*.png"))) if C.EMOJI.exists() else 0
# Not counted: only plates with an emoji need them, and they are baked on a Mac.
print(f"  {'ok  ' if n else 'note'}  {n} baked emoji in {C.EMOJI}"
      + ("" if n else "  (only emoji plates need them: see assets/emoji/README.md)"))
check((C.ASSETS / "three" / "build" / "three.module.min.js").exists(),
      "three.js for scene3d.py", "restore reel-system/assets/three from the bundle")
import voice  # noqa: E402
have = all((voice.MODELS / f).exists() for f in voice.FILES)
check(have, f"voice model in {voice.MODELS}", "python reel-system/voice.py --download")
check(C.BURNED_KEYWORDS.exists(), f"keyword ledger {C.BURNED_KEYWORDS}",
      "copy reel-system/keywords_burned.template.txt to keywords_burned.txt and "
      "seed it with every keyword the account has ever used")
# Not counted: matte.py is optional (final.py shows the presenter as a window)
for mod in ("torch", "torchvision"):
    print(f"  {'ok  ' if importlib.util.find_spec(mod) else 'note'}  {mod:<15} "
          f"optional, matte.py only (several GB)")
# Not counted: only needed to bake a NEW emoji, which needs a Mac anyway.
print(f"  {'ok  ' if Path(C.APPLE_EMOJI_TTC).exists() else 'note'}  "
      f"Apple Color Emoji (only to bake new glyphs): {C.APPLE_EMOJI_TTC}")
print(f"  info  delivery folder: {C.DELIVERY}  (override with REEL_DELIVERY)")

print(f"\n{'ready' if not bad else f'{bad} missing. Fix these before newreel.py burns a keyword.'}")
sys.exit(1 if bad else 0)
