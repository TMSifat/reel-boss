#!/usr/bin/env python3
"""Stage 0b: no phone take? Read the script with a local AI voice.

Kokoro v1.0 (Apache 2.0) via kokoro-onnx, on the CPU. Free, offline after the
one time model download, no account, no credits. It writes the same take.mp4
a phone take would be, so stt, trim, final and verify run unchanged. The reel
goes faceless: reel.json gets an empty presenter_track and the b-roll carries
every frame, the way the 6,683 view Mars Rover reel did with no presenter.

    python3 voice.py projects/<slug>                    reads reel.json "script"
    python3 voice.py projects/<slug> --voice af_heart --speed 1.1
    python3 voice.py --download                         fetch the model only
    python3 voice.py --list                             show the voices

The voice is synthetic. Post it with Instagram's AI label switched on.
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from lib.util import ffmpeg, run, need

MODELS = Path(os.environ.get("REEL_VOICE_MODELS", Path.home() / ".cache" / "reel-boss" / "kokoro"))
RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
# Pinned on first download from the official release, 2026-10-13. A mismatch
# means a corrupt or swapped file, and an unknown model file never gets loaded.
FILES = {
    "kokoro-v1.0.onnx": "7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5",
    "voices-v1.0.bin": "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d",
}
DEFAULT_VOICE = "am_michael"   # warm, clear US male. af_heart is the female pick
GAP = 0.10                     # seconds between lines: brisk, trim removes the rest


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def models():
    """Download once, verify every time. Returns the two model paths."""
    MODELS.mkdir(parents=True, exist_ok=True)
    out = []
    for name, want in FILES.items():
        p = MODELS / name
        if not p.exists():
            print(f"[voice] downloading {name} (one time) -> {MODELS}")
            tmp = p.with_suffix(".part")
            try:
                urllib.request.urlretrieve(RELEASE + name, tmp)
            except Exception as e:
                raise RuntimeError(f"could not download {name}: {e}\n"
                                   f"fetch {RELEASE}{name} by hand into {MODELS}") from None
            tmp.replace(p)
        if _sha(p) != want:
            raise RuntimeError(f"{p} failed its checksum. Delete it and rerun.")
        out.append(p)
    return out


def engine():
    try:
        from kokoro_onnx import Kokoro
    except ImportError:
        raise RuntimeError("pip install kokoro-onnx soundfile") from None
    return Kokoro(*map(str, models()))


def script_lines(spec):
    """The script in order, empty lines dropped. The keys sort as 1_hook..6_cta."""
    s = spec.get("script") or {}
    lines = [s[k].strip() for k in sorted(s) if str(s[k]).strip()] if isinstance(s, dict) \
        else [str(x).strip() for x in s if str(x).strip()]
    if not lines:
        raise ValueError("reel.json has no script lines. Write the six lines first.")
    return lines


def speak(project, voice=DEFAULT_VOICE, speed=1.05):
    import numpy as np
    import soundfile as sf

    project = Path(project)
    spec_p = need(project / "reel.json", "reel.json")
    spec = json.loads(spec_p.read_text(encoding="utf-8"))
    lines = script_lines(spec)

    k = engine()
    if voice not in k.get_voices():
        raise ValueError(f"unknown voice {voice!r}. python voice.py --list")
    parts, sr = [], 24000
    for i, line in enumerate(lines, 1):
        a, sr = k.create(line, voice=voice, speed=speed, lang="en-gb" if voice[:1] == "b" else "en-us")
        parts += [a, np.zeros(int(GAP * sr), dtype=a.dtype)]
        print(f"[voice] line {i}: {len(a) / sr:.2f}s  {line}")
    wav = project / "voice_raw.wav"
    sf.write(str(wav), np.concatenate(parts[:-1]), sr)

    # A take is video + audio. Faceless, so the video is a plate the b-roll
    # covers; it exists only so every later stage gets the file it expects.
    take = project / "take.mp4"
    run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(wav),
         "-f", "lavfi", "-i", f"color=c={C.PALETTES[spec['palette']]['bg']}:s={C.W}x{C.H}:r={C.FPS}",
         "-map", "1:v", "-map", "0:a", "-shortest",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "pcm_s16le", "-ar", str(C.SAMPLE_RATE), "-ac", str(C.CHANNELS), str(take)])

    # derive_spans() cuts at the longest pauses, and a synthetic read pauses
    # evenly, so one shot ate 12s of a 16s reel. Anchor shots to line starts.
    n = len(spec.get("shots", []))
    if n > 1 and not spec.get("shot_anchors") and len(lines) >= n:
        spec["shot_anchors"] = [" ".join(lines[round(i * len(lines) / n)].split()[:2])
                                for i in range(1, n)]
        print(f"[voice] shot_anchors {spec['shot_anchors']} (one shot per block of lines)")
    spec["presenter_track"] = []
    spec["voice"] = {"engine": "kokoro-v1.0", "voice": voice, "speed": speed, "synthetic": True}
    spec_p.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    total = sum(len(p) for p in parts[:-1]) / sr
    print(f"[voice] {len(lines)} lines, {total:.2f}s, voice {voice} -> {take}")
    print("[voice] faceless: presenter_track set to []. Next: python stt.py "
          f"{take}  (then trim, final, verify as usual)")
    print("[voice] synthetic voice: switch on Instagram's AI label when posting.")
    return take


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--speed", type=float, default=1.05)
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.download:
        print("\n".join(map(str, models())))
    elif a.list:
        print(" ".join(v for v in engine().get_voices() if v[:2] in ("am", "af", "bm", "bf")))
    elif a.project:
        speak(a.project, a.voice, a.speed)
    else:
        ap.error("give a project folder, or --download / --list")
