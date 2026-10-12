#!/usr/bin/env python3
"""Stage 6: check the DELIVERED file, not the build log.

A build can report success while the folder still holds an older render. We have
reported a reel as fixed while the shipped file still had a repo name visible on
it. So this reads the mp4 that is actually sitting in the delivery folder and
proves things about it:

  * container: 1080x1920, 30fps, under 20s, has an audio stream
  * loudness: re-measured off the delivered file, not off the intermediate
  * audio content: the delivered audio is transcribed again and diffed against
    the script, so a silently dropped sentence cannot ship
  * gate: the transcript is scanned for the tool name and any banned words
  * frames: 16 stills pulled out for eyes on, plus the contact sheet

    python3 verify.py ~/Documents/Notes/video-assets/<slug>.mp4 --project projects/<slug>
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from lib.util import (ffmpeg, run, need, probe, duration, audio_duration, measure_loudness,
                      has_audio)

FAIL, WARN, OK = "FAIL", "WARN", "ok  "


def verify(mp4, project=None, forbidden=(), max_seconds=None):
    mp4 = need(mp4, "delivered mp4")
    rows, fails = [], 0

    info = probe(mp4)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    w, h = int(v["width"]), int(v["height"])
    fps = round(eval(v["r_frame_rate"]), 2)
    d = duration(mp4)

    def chk(cond, label, detail):
        nonlocal fails
        st = OK if cond else FAIL
        if not cond:
            fails += 1
        rows.append((st, label, detail))

    chk((w, h) == (C.W, C.H), "frame", f"{w}x{h} (want {C.W}x{C.H})")
    chk(abs(fps - C.FPS) < 0.51, "fps", f"{fps} (want {C.FPS})")
    # the ceiling is a per reel number now; 20s is the house default
    ceiling = float(max_seconds or C.MAX_SECONDS)
    chk(d <= ceiling + 0.6, "length", f"{d:.2f}s (ceiling {ceiling}s)")
    chk(has_audio(mp4), "audio stream", "present" if has_audio(mp4) else "MISSING")
    if has_audio(mp4):
        vd = float(v.get("duration") or d)
        ad = audio_duration(mp4)
        # a mismatch means -shortest chopped one side: lost voice or a cut-off ending
        chk(abs(vd - ad) <= 0.15, "a/v length", f"video {vd:.2f}s, audio {ad:.2f}s")

    if has_audio(mp4):
        m = measure_loudness(mp4)
        li, tp = float(m["input_i"]), float(m["input_tp"])
        chk(abs(li - C.LUFS_TARGET) <= 1.0, "loudness",
            f"{li:.2f} LUFS (target {C.LUFS_TARGET})")
        chk(tp <= C.TRUE_PEAK_MAX + 0.3, "true peak",
            f"{tp:.2f} dBTP (max {C.TRUE_PEAK_MAX})")

        from stt import transcribe
        got = transcribe(mp4, mp4.parent / f"{mp4.stem}_delivered_words.json")
        (mp4.parent / f"{mp4.stem}_16k.wav").unlink(missing_ok=True)  # stt scratch, not a deliverable
        heard = got["text"]
        # a guide track or music bed is not a voice; a brisk script runs ~2.5 words/s
        wps = len(got["words"]) / max(d, 0.1)
        chk(wps >= 1.0, "voice", f"{len(got['words'])} words, {wps:.1f}/s"
            + ("" if wps >= 1.0 else ". NO VOICE: record the take or run voice.py"))

        if project:
            wj = Path(project) / "words_trim.json"
            if wj.exists():
                want = json.loads(wj.read_text())["text"]
                ratio = difflib.SequenceMatcher(
                    None, re.sub(r"\W+", " ", want.lower()),
                    re.sub(r"\W+", " ", heard.lower())).ratio()
                chk(ratio >= 0.90, "audio vs script",
                    f"{ratio*100:.1f}% match (a dropped sentence shows up here)")

        low = heard.lower()
        for bad in forbidden:
            chk(bad.lower() not in low, f"gate: {bad}",
                "not spoken" if bad.lower() not in low else "SPOKEN ON THE TAKE")
        for ch in C.BANNED_CHARS:
            chk(ch not in heard, f"dash {ch!r}", "clean" if ch not in heard else "found")

    sheet = mp4.with_name(mp4.stem + "_SB.jpg")
    chk(sheet.exists(), "contact sheet", sheet.name if sheet.exists() else "MISSING")

    frames = mp4.parent / f"_frames_{mp4.stem}"
    frames.mkdir(exist_ok=True)
    for f in frames.glob("*.png"):
        f.unlink()
    for i in range(16):
        t = d * (i + 0.5) / 16
        run([ffmpeg(), "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(mp4),
             "-frames:v", "1", str(frames / f"t{t:05.2f}.png")])
    rows.append((OK, "frames pulled", f"16 -> {frames}"))

    print(f"\nVERIFY {mp4}")
    print("-" * 68)
    for st, label, detail in rows:
        print(f"  [{st}] {label:<18} {detail}")
    print("-" * 68)
    print(f"  {'PASS' if fails == 0 else str(fails) + ' FAILURE(S)'}\n")
    print("  Now LOOK at the contact sheet. One question: does anything overlap")
    print("  anything else. Banner over caption, caption over presenter,")
    print("  presenter over the one graphic that matters.\n")
    return fails == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4")
    ap.add_argument("--project")
    ap.add_argument("--forbid", nargs="*", default=[],
                    help="tool name / repo name that must never be spoken")
    ap.add_argument("--max-seconds", type=float, default=None,
                    help="override the house 20s ceiling for this reel")
    a = ap.parse_args()
    sys.exit(0 if verify(a.mp4, a.project, a.forbid, a.max_seconds) else 1)
