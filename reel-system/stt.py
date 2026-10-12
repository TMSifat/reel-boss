#!/usr/bin/env python3
"""Stage 1 of the edit: word level transcript of the take.

faster-whisper small.en on CPU. Local, no API, no key.
Everything downstream (the cut, the captions, the graphics) is derived from
this file. Nothing downstream ever types in a timecode.

    python3 stt.py projects/<slug>/take.mp4
    -> projects/<slug>/words.json
"""
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.util import ffmpeg, run, need

MODEL = "small.en"


def respell(words, script):
    """Whisper hears 'DakuSign' and 'kazook'. The script says DocuSign and KAZOOQ.

    Align the heard words to the script and, where a heard word is a close
    match for the script word in its slot, caption the script's spelling.
    Timings stay whisper's. A word the speaker really changed is left alone.
    """
    norm = lambda s: re.sub(r"\W", "", s.lower())
    want = script.split()
    a, b = [norm(w["w"]) for w in words], [norm(t) for t in want]
    fixed = 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != "replace" or i2 - i1 != j2 - j1:
            continue
        for i, j in zip(range(i1, i2), range(j1, j2)):
            if difflib.SequenceMatcher(None, a[i], b[j]).ratio() >= 0.6:
                print(f"[stt] caption {words[i]['w']!r} -> {want[j]!r} (script spelling)")
                words[i]["w"] = want[j]
                fixed += 1
    return fixed


def transcribe(media, out_json=None):
    media = need(media, "take")
    out_json = Path(out_json) if out_json else media.with_name("words.json")

    wav = media.with_name(media.stem + "_16k.wav")
    run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(media),
         "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)])

    from faster_whisper import WhisperModel
    model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        str(wav), word_timestamps=True, vad_filter=False, beam_size=5)

    words, text = [], []
    for seg in segments:
        for w in (seg.words or []):
            tok = w.word.strip()
            if not tok:
                continue
            if words and tok[0] in ",.!?%:;'" and not w.word.startswith(" "):
                words[-1]["w"] += tok           # a continuation, not a new word
                words[-1]["end"] = round(w.end, 3)
                text[-1] += tok
                continue
            words.append({"w": tok, "start": round(w.start, 3),
                          "end": round(w.end, 3), "prob": round(w.probability, 3)})
            text.append(tok)

    spec = media.parent / "reel.json"
    if spec.exists():
        from voice import script_lines
        try:
            if respell(words, " ".join(script_lines(json.loads(spec.read_text(encoding="utf-8"))))):
                text = [w["w"] for w in words]
        except ValueError:
            pass   # no script written yet: plain transcript

    data = {"source": str(media), "model": MODEL,
            "duration": round(info.duration, 3),
            "text": " ".join(text), "words": words}
    out_json.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"[stt] {len(words)} words, {info.duration:.2f}s -> {out_json}")
    return data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    transcribe(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
