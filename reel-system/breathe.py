#!/usr/bin/env python3
"""Stage 2a: cap the pauses instead of deleting them.

trim.py removes every pause, which is what kept a six line script under the old
20 second ceiling. The cost is that the take then has no rhythm anywhere: 10.03s
of silence came out of a 30.47s take and the read lands at one relentless pitch,
which is why the reel kept coming back as "too fast" no matter what the speed
multipliers were set to. The multipliers were never the problem.

This keeps a breath at every boundary and only trims what is longer than a
breath. A pause after a full stop is worth more than one mid sentence, so the
two get different caps.

    python3 breathe.py projects/<slug>
    -> take_paced_src.mp4  words_paced_src.json   (pace.py then runs on these)
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from lib.util import ffmpeg, run, need, duration

SENTENCE_CAP = 0.46      # after . ? !
CLAUSE_CAP = 0.26        # after , or mid phrase
HEAD_KEEP = 0.16         # silence kept before the first word
TAIL_KEEP = 0.34         # and after the last one
ENDS_SENTENCE = re.compile(r"[.!?]$")


def build(project):
    project = Path(project)
    src = need(project / "take.mp4", "raw take")
    wj = json.loads(need(project / "words.json", "words.json").read_text())
    words = wj["words"]
    total = duration(src)

    # keep spans: everything except the excess part of each over long pause
    keep, t = [], max(0.0, words[0]["start"] - HEAD_KEEP)
    for a, b in zip(words, words[1:]):
        gap = b["start"] - a["end"]
        cap = SENTENCE_CAP if ENDS_SENTENCE.search(a["w"]) else CLAUSE_CAP
        if gap > cap + 0.06:
            cut_from = a["end"] + cap / 2
            cut_to = b["start"] - cap / 2
            keep.append((t, cut_from))
            t = cut_to
    keep.append((t, min(total, words[-1]["end"] + TAIL_KEEP)))
    keep = [(round(s, 3), round(e, 3)) for s, e in keep if e - s > 0.02]

    kept = sum(e - s for s, e in keep)
    print(f"[breathe] {total:.2f}s raw -> {kept:.2f}s, "
          f"{len(keep) - 1} pauses capped at {SENTENCE_CAP}/{CLAUSE_CAP}s")

    work = project / "_breathe"
    work.mkdir(exist_ok=True)
    for f in work.glob("*"):
        f.unlink()
    vparts, aparts = [], []
    for i, (s, e) in enumerate(keep):
        pv, pa = work / f"v{i:03d}.mp4", work / f"a{i:03d}.wav"
        run([ffmpeg(), "-y", "-loglevel", "error", "-ss", f"{s:.3f}", "-to", f"{e:.3f}",
             "-i", str(src), "-an", "-c:v", "libx264", "-crf", "16",
             "-preset", "veryfast", "-pix_fmt", "yuv420p", str(pv)])
        run([ffmpeg(), "-y", "-loglevel", "error", "-ss", f"{s:.3f}", "-to", f"{e:.3f}",
             "-i", str(src), "-vn", "-ar", str(C.SAMPLE_RATE), "-ac", str(C.CHANNELS),
             "-c:a", "pcm_s16le", str(pa)])
        vparts.append(pv)
        aparts.append(pa)

    (work / "v.txt").write_text("".join(f"file '{p.name}'\n" for p in vparts))
    (work / "a.txt").write_text("".join(f"file '{p.name}'\n" for p in aparts))
    silent, joined = work / "v.mp4", work / "a.wav"
    run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", "v.txt", "-c", "copy", str(silent.resolve())], cwd=work)
    run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", "a.txt", "-c", "copy", str(joined.resolve())], cwd=work)
    out = (project / "take_paced_src.mp4").resolve()
    run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(silent), "-i", str(joined),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-ar", str(C.SAMPLE_RATE), str(out)])

    # re-time the words onto the kept timeline, using measured part lengths
    real = [duration(p) for p in vparts]
    new_words, t0 = [], 0.0
    for (s, e), rd in zip(keep, real):
        k = rd / max(1e-6, e - s)
        for w in words:
            if s <= w["start"] < e:
                new_words.append({**w,
                                  "start": round(t0 + (w["start"] - s) * k, 3),
                                  "end": round(t0 + (min(w["end"], e) - s) * k, 3)})
        t0 += rd
    (project / "words_paced_src.json").write_text(json.dumps(
        {**wj, "duration": round(t0, 3), "words": new_words}, indent=1))
    print(f"[breathe] delivered {duration(out):.2f}s, {len(new_words)} words re-timed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    build(ap.parse_args().project)
