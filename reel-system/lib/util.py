"""Shared helpers. The rules that cost a post are enforced here, not in comments."""
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as C

# Windows consoles and pipes default to cp1252, which cannot print the banned
# dashes verify.py reports, or an emoji in a transcript.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- process ----
def run(cmd, **kw):
    """Run a command, raise loudly with real stderr on failure."""
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", **kw)
    if p.returncode != 0:
        raise RuntimeError(f"FAILED: {' '.join(map(str, cmd))}\n{p.stderr[-4000:]}")
    return p.stdout


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        try:
            import imageio_ffmpeg
        except ImportError:
            raise RuntimeError("ffmpeg not found on PATH. Install it: brew install ffmpeg | "
                               "winget install Gyan.FFmpeg | apt install ffmpeg") from None
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    return exe


def ffprobe():
    exe = shutil.which("ffprobe")
    if not exe:
        # imageio-ffmpeg ships ffmpeg only, never ffprobe, so there is no fallback here
        raise RuntimeError("ffprobe not found on PATH. Install full ffmpeg: "
                           "brew install ffmpeg | winget install Gyan.FFmpeg | apt install ffmpeg")
    return exe


# ------------------------------------------------------------- assets/IO ----
def need(path, what="asset"):
    """Missing assets THROW. They never silently fall back to a system font.

    This is the fix for the reel that shipped the wrong emoji.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"missing {what}: {p}\nno silent fallback, fix the asset")
    return p


def probe(path):
    out = run([ffprobe(), "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", str(path)])
    return json.loads(out)


def duration(path):
    return float(probe(path)["format"]["duration"])


def audio_duration(path):
    """Length of the audio stream, falling back to the container length."""
    info = probe(path)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    return float(a.get("duration") or info["format"]["duration"]) if a else duration(path)


def has_audio(path):
    return any(s["codec_type"] == "audio" for s in probe(path)["streams"])


# ------------------------------------------------------------ text rules ----
def lint_text(s, where="text", hook=False):
    """No em dashes, en dashes or double hyphens in anything published.
    No the word 'free' in a hook or title. Raises rather than warns.
    """
    bad = [c for c in C.BANNED_CHARS if c in s]
    if bad:
        raise ValueError(f"{where}: banned character(s) {bad} in: {s!r}")
    if hook:
        # word boundary, so "free." and "FREE!" are caught too, "freedom" is not
        if re.search(r"\bfree\b", s, re.IGNORECASE):
            raise ValueError(f"{where}: the word 'free' is banned in hooks and titles. "
                             f"Say the licence instead (MIT, Apache 2.0). Got: {s!r}")
    return s


def claim_keyword(word):
    """One unique CTA keyword per post, never reused. Ledger is append only."""
    word = word.strip().upper()
    if not word.isalpha():
        raise ValueError(f"CTA keyword must be a single alpha word, got {word!r}")
    C.BURNED_KEYWORDS.parent.mkdir(parents=True, exist_ok=True)
    C.BURNED_KEYWORDS.touch()
    burned = {l.split("#")[0].strip().upper()
              for l in C.BURNED_KEYWORDS.read_text(encoding="utf-8").splitlines() if l.strip()}
    if word in burned:
        raise ValueError(f"CTA keyword {word} is already burned. Pick another. "
                         f"Two posts on one keyword send the wrong thing to somebody.")
    return word


def burn_keyword(word, slug):
    word = claim_keyword(word)
    with C.BURNED_KEYWORDS.open("a", encoding="utf-8") as f:
        f.write(f"{word}  # {slug}\n")
    return word


# --------------------------------------------------------------- randoms ----
def shuffled(seq, seed):
    """Seeded shuffle. Looks random, is identical between rebuilds.
    Never (i * 97 + 13) % N, that draws visible diagonal stripes.
    """
    out = list(seq)
    random.Random(seed).shuffle(out)
    return out


# -------------------------------------------------------------- loudness ----
def measure_loudness(audio):
    """Measurement pass of loudnorm. Returns the real measured numbers."""
    p = subprocess.run(
        [ffmpeg(), "-hide_banner", "-nostats", "-i", str(audio),
         "-af", f"loudnorm=I={C.LUFS_TARGET}:TP={C.TRUE_PEAK_MAX}:LRA=11:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = p.stderr[p.stderr.rfind("{"):p.stderr.rfind("}") + 1]
    return json.loads(tail)


def master(src, dst):
    """Two pass loudnorm to an exact number, then MEASURE AGAIN and report.

    Instagram normalises audio. A reel that is quiet next to the one before it
    in the feed loses people, so we do not trust a single pass.
    """
    m = measure_loudness(src)
    run([ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
         "-af", (f"loudnorm=I={C.LUFS_TARGET}:TP={C.TRUE_PEAK_MAX}:LRA=11:"
                 f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                 f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
                 f"offset={m['target_offset']}:linear=true:print_format=summary"),
         "-ar", str(C.SAMPLE_RATE), "-ac", str(C.CHANNELS),
         "-c:a", "pcm_s16le", str(dst)])
    v = measure_loudness(dst)
    out_i, out_tp = float(v["input_i"]), float(v["input_tp"])
    print(f"[master] verified integrated {out_i:.2f} LUFS, true peak {out_tp:.2f} dBTP")
    if abs(out_i - C.LUFS_TARGET) > 1.0:
        raise RuntimeError(f"loudness off target: {out_i} vs {C.LUFS_TARGET}")
    if out_tp > C.TRUE_PEAK_MAX + 0.3:
        raise RuntimeError(f"true peak too hot: {out_tp} dBTP")
    return out_i, out_tp


# ----------------------------------------------------------------- silence ---
def detect_silence(audio, noise_db=-38, min_dur=0.12):
    """Measured silence from the waveform, not from word boundaries.

    Speech to text word boundaries are loose by up to 0.2s. Cut the UNION of
    both or you ship dead air the transcript said was not there.
    """
    p = subprocess.run(
        [ffmpeg(), "-hide_banner", "-nostats", "-i", str(audio),
         "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    spans, start = [], None
    for line in p.stderr.splitlines():
        if "silence_start:" in line:
            start = float(line.split("silence_start:")[1].split()[0])
        elif "silence_end:" in line and start is not None:
            spans.append((start, float(line.split("silence_end:")[1].split()[0])))
            start = None
    if start is not None:
        spans.append((start, duration(audio)))
    return spans
