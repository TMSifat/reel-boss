#!/usr/bin/env python3
"""Stage 2b: give the delivery a shape instead of one flat speed.

trim.py cuts every pause, which is what keeps a six line script under 20
seconds, but with no pause anywhere the whole read lands at one pitch and the
reel feels rushed end to end. This stage puts the variation back where a person
would put it: the hook goes fast because a hook has to, the line after it sits
at the recorded speed, the middle three alternate, and the licence and the ask
are left alone because the CTA is the one line the viewer has to act on.

The shape is per line, and the lines come from the same phrase anchors the shots
are cut to, so a pacing change and a shot change stay locked to each other.

Speeds are a seeded shuffle, not a coin flip: identical between rebuilds, and
the ceiling is checked before anything is written.

    python3 pace.py projects/<slug>
"""
import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from lib.util import ffmpeg, run, need, duration
from final import find_phrase

FAST, NORMAL, SLOW = 1.15, 1.00, 0.92


def plan(spans, seed):
    """One speed per line. Positions 0, 1, and the last two are fixed by intent."""
    n = len(spans)
    speeds = [NORMAL] * n
    speeds[0] = FAST                      # the hook
    speeds[1] = NORMAL                    # settle
    middle = list(range(2, n - 2))
    pool = [FAST if i % 2 == 0 else SLOW for i in range(len(middle))]
    random.Random(seed).shuffle(pool)     # seeded: same every rebuild
    for i, s in zip(middle, pool):
        speeds[i] = s
    return speeds                         # last two stay NORMAL: outro and CTA


def build(project):
    project = Path(project)
    spec = json.loads(need(project / "reel.json", "reel.json").read_text())
    src = need(project / "take_paced_src.mp4", "unpaced take")
    wj = json.loads(need(project / "words_paced_src.json", "unpaced words").read_text())
    words = wj["words"]
    total = duration(src)

    cuts = [0.0]
    for a in spec["shot_anchors"]:
        s, _ = find_phrase(words, a, after=cuts[-1])
        cuts.append(round(s - 0.10, 3))
    cuts.append(round(total, 3))
    spans = [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]

    # An explicit plan wins over the seeded one. The CTA needed to come down
    # below recorded speed: it already had a 0.40s pause in front of it and
    # still read as rushed, because it is the only line the viewer has to act
    # on. The extra time is funded by taking line 4 faster, so the reel stays
    # under the ceiling without flattening the shape.
    speeds = spec.get("speed_plan") or plan(spans, spec["slug"])
    if len(speeds) != len(spans):
        raise ValueError(f"{len(spans)} lines need {len(spans)} speeds, got {len(speeds)}")
    new_total = sum((b - a) / s for (a, b), s in zip(spans, speeds))
    print(f"[pace] {total:.2f}s -> {new_total:.2f}s")
    for (a, b), s in zip(spans, speeds):
        tag = {FAST: "fast", NORMAL: "normal", SLOW: "slow"}.get(s, f"x{s}")
        print(f"  {a:6.2f}-{b:6.2f}  x{s:.2f} {tag:6s} -> {(b-a)/s:5.2f}s")
    ceiling = float(spec.get("max_seconds", C.MAX_SECONDS))
    if new_total > ceiling:
        raise RuntimeError(f"{new_total:.2f}s is over the {ceiling}s ceiling")

    work = project / "_pace"
    work.mkdir(exist_ok=True)
    for f in work.glob("*.mp4"):
        f.unlink()
    # Video and audio are re-timed and joined on separate paths. Encoding each
    # segment as AAC and concatenating them put the encoder's priming delay at
    # all seven joins, which clipped the onsets: the delivered audio came back
    # as "you drop THEM and add markers" and "IT MIGHT SEE license" instead of
    # "drop zoom" and "MIT License". PCM has no priming, so the joins are clean.
    parts, apart = [], []
    for i, ((a, b), s) in enumerate(zip(spans, speeds)):
        pv = work / f"p{i:02d}.mp4"
        pa = work / f"p{i:02d}.wav"
        run([ffmpeg(), "-y", "-loglevel", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}",
             "-i", str(src), "-an", "-vf", f"setpts={1/s:.6f}*PTS",
             "-c:v", "libx264", "-crf", "16", "-preset", "veryfast",
             "-pix_fmt", "yuv420p", str(pv)])
        # A line left at recorded speed is cut, not resampled. atempo at 1.0 is
        # not a no-op, it still runs the filter over the samples.
        acmd = [ffmpeg(), "-y", "-loglevel", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}",
                "-i", str(src), "-vn"]
        if abs(s - 1.0) > 1e-6:
            acmd += ["-af", f"atempo={s:.6f}"]
        acmd += ["-ar", str(C.SAMPLE_RATE), "-ac", str(C.CHANNELS),
                 "-c:a", "pcm_s16le", str(pa)]
        run(acmd)
        parts.append(pv)
        apart.append(pa)
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    alst = work / "alist.txt"
    alst.write_text("".join(f"file '{p.name}'\n" for p in apart))
    silent = work / "video_only.mp4"
    run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", lst.name, "-c", "copy", str(silent.resolve())], cwd=work)
    joined = work / "audio.wav"
    run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", alst.name, "-c", "copy", str(joined.resolve())], cwd=work)
    out = (project / "take_trim.mp4").resolve()
    run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(silent), "-i", str(joined),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-ar", str(C.SAMPLE_RATE), str(out)])

    # Re-time every word onto the new clock using each part's MEASURED length,
    # not the arithmetic one. Each segment is re-encoded and lands on a frame
    # boundary, so the ideal maths came out 0.32s short across seven parts and
    # the captions would have drifted early by the end of the reel.
    real = [duration(p) for p in parts]
    new_words, new_spans, t0 = [], [], 0.0
    for (a, b), s, rd in zip(spans, speeds, real):
        k = rd / ((b - a) / s)            # how far this part ran from the plan
        new_spans.append((round(t0, 3), round(t0 + rd, 3)))
        for w in words:
            if a <= w["start"] < b:
                new_words.append({**w,
                                  "start": round(t0 + (w["start"] - a) / s * k, 3),
                                  "end": round(t0 + (min(w["end"], b) - a) / s * k, 3)})
        t0 += rd
    (project / "words_trim.json").write_text(json.dumps(
        {**wj, "duration": round(t0, 3), "words": new_words}, indent=1))
    (project / "spans.json").write_text(json.dumps(
        {"spans": new_spans, "speeds": speeds}, indent=1))
    print(f"[pace] delivered {duration(out):.2f}s, {len(new_words)} words re-timed")
    return new_spans, speeds


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    build(ap.parse_args().project)
