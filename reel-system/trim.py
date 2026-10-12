#!/usr/bin/env python3
"""Stage 2 of the edit: cut every pause, then speed the whole take up slightly.

Two independent sources of truth, unioned:
  1. gaps between word end and next word start, from words.json
  2. silencedetect on the actual waveform

Whisper word boundaries are loose by up to 0.2s. A trim built only from them
looks clean in the transcript while the audio still holds seven tenths of a
second of dead air before the first word. So we intersect: a region is cut only
if BOTH agree it is silence, and we take the tighter inner edge of the two.

Audio and video are retimed together with the same factor so the mouth stays on
the words. Output is a new words.json with retimed word times, because every
downstream stage derives its cut from that file.

    python3 trim.py projects/<slug>/take.mp4 --speed 1.06
    -> take_trim.mp4  words_trim.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from lib.util import ffmpeg, run, need, detect_silence, duration, audio_duration

HEAD_PAD = 0.06   # keep this much of the breath before a word
TAIL_PAD = 0.10   # and after it
MIN_CUT = 0.18    # do not bother cutting anything shorter


def _overlap(a, b):
    """Intersection of two (start, end) span lists."""
    out = []
    for s1, e1 in a:
        for s2, e2 in b:
            s, e = max(s1, s2), min(e1, e2)
            if e - s > 0:
                out.append((s, e))
    return sorted(out)


def plan_cuts(words, total, silences):
    """Regions to REMOVE. Union logic described in the module docstring."""
    if not words:
        return []
    gaps = []
    if words[0]["start"] > 0:
        gaps.append((0.0, words[0]["start"]))
    for a, b in zip(words, words[1:]):
        if b["start"] - a["end"] > 0:
            gaps.append((a["end"], b["start"]))
    if words[-1]["end"] < total:
        gaps.append((words[-1]["end"], total))

    cuts = []
    for s, e in _overlap(gaps, silences):
        s2 = s + (0 if s <= 0.001 else TAIL_PAD)
        e2 = e - (0 if e >= total - 0.001 else HEAD_PAD)
        if e2 - s2 >= MIN_CUT:
            cuts.append((round(s2, 3), round(e2, 3)))
    return cuts


def keep_spans(cuts, total):
    keeps, t = [], 0.0
    for s, e in cuts:
        if s > t:
            keeps.append((t, s))
        t = e
    if t < total:
        keeps.append((t, total))
    return [(a, b) for a, b in keeps if b - a > 0.02]


def retime_words(words, keeps, speed):
    """Map original word times onto the trimmed and sped up timeline."""
    out, elapsed = [], 0.0
    bounds = []
    for a, b in keeps:
        bounds.append((a, b, elapsed))
        elapsed += b - a
    for w in words:
        for a, b, off in bounds:
            if a - 1e-6 <= w["start"] < b:
                out.append({**w,
                            "start": round((off + w["start"] - a) / speed, 3),
                            "end": round((off + min(w["end"], b) - a) / speed, 3)})
                break
    return out, elapsed / speed


def trim(take, words_json=None, speed=1.06):
    take = need(take, "take")
    words_json = Path(words_json) if words_json else take.with_name("words.json")
    data = json.loads(need(words_json, "words.json").read_text())
    total = audio_duration(take)  # not the container: a video tail past the voice is dead air

    wav = take.with_name(take.stem + "_16k.wav")
    if not wav.exists():
        run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(take),
             "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    silences = detect_silence(wav)

    cuts = plan_cuts(data["words"], total, silences)
    # Snap to the frame grid. Off-grid pieces round their video up a frame while
    # the audio stays exact, and the error stacks per cut into lip-sync drift.
    keeps = [(round(a * C.FPS) / C.FPS, round(b * C.FPS) / C.FPS)
             for a, b in keep_spans(cuts, total)]
    keeps = [(a, b) for a, b in keeps if b > a]
    removed = sum(e - s for s, e in cuts)
    print(f"[trim] {len(cuts)} cuts, removing {removed:.2f}s of {total:.2f}s, "
          f"then x{speed} speed")

    # Build one concat of trimmed pieces, then a single retime pass.
    work = take.parent / "_trim_parts"
    work.mkdir(exist_ok=True)
    for f in work.glob("*.mp4"):
        f.unlink()
    parts = []
    for i, (a, b) in enumerate(keeps):
        p = work / f"p{i:03d}.mp4"
        n = round((b - a) * C.FPS)  # exact frame count: -to lets one extra frame through
        run([ffmpeg(), "-y", "-loglevel", "error", "-ss", f"{a:.3f}",
             "-i", str(take), "-frames:v", str(n), "-t", f"{n / C.FPS:.6f}",
             "-c:v", "libx264", "-crf", "16", "-preset", "veryfast",
             "-pix_fmt", "yuv420p", "-r", str(C.FPS),
             "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(p)])
        parts.append(p)

    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    joined = take.with_name(take.stem + "_joined.mp4").resolve()
    run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", lst.name, "-c", "copy", str(joined)], cwd=work)

    out = take.with_name(take.stem.replace("take", "take_trim") + ".mp4")
    # -vf and -af only. No filter_complex: two independent chains in one
    # filter_complex once dropped 3.2 seconds of voice with no error.
    n = round(duration(joined) / speed * C.FPS)  # setpts + -r overshoots by a frame or two
    run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(joined),
         "-vf", f"setpts=PTS/{speed}",
         "-af", f"atempo={speed}", "-frames:v", str(n), "-t", f"{n / C.FPS:.6f}",
         "-c:v", "libx264", "-crf", "16", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-r", "30",
         "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(out)])

    rw, newdur = retime_words(data["words"], keeps, speed)
    outj = words_json.with_name("words_trim.json")
    outj.write_text(json.dumps({**data, "source": str(out), "words": rw,
                                "duration": round(newdur, 3),
                                "cuts": cuts, "speed": speed}, indent=1))
    real = duration(out)
    print(f"[trim] -> {out.name}  {real:.2f}s (predicted {newdur:.2f}s)  -> {outj.name}")
    spec = take.parent / "reel.json"
    ceiling = float(json.loads(spec.read_text(encoding="utf-8")).get("max_seconds", C.MAX_SECONDS)
                    if spec.exists() else C.MAX_SECONDS)
    if real > ceiling + 0.5:
        print(f"[trim] WARNING {real:.2f}s is over the {ceiling}s ceiling. Tighten "
              f"pauses or raise max_seconds in reel.json; never cut a real-world beat.")
    return out, outj


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("take")
    ap.add_argument("--words")
    ap.add_argument("--speed", type=float, default=1.06)
    a = ap.parse_args()
    trim(a.take, a.words, a.speed)
