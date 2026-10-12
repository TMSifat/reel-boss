#!/usr/bin/env python3
"""Stage 5 of the edit: assemble, composite, burn, mix, master, deliver.

Structural decision that removes the worst trap in the whole pipeline:
the video track is built with NO audio anywhere in it, the audio is mastered on
its own, and the two are muxed at the very end with -c:v copy -c:a aac. Two
independent chains inside one filter_complex once dropped 3.2 seconds of voice
and nothing errored. This layout cannot do that.

Shot boundaries are derived from words_trim.json, from where the speaker
actually stops talking. No timecode is typed anywhere in this file.

    python3 final.py projects/<slug>
"""
import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
import theme
from lib.util import ffmpeg, run, need, master, duration, has_audio
from lib.ease import window, out_cubic

PLATE_IN, PLATE_OUT = 0.28, 0.16   # seconds

PRESENTER_SCALE = 0.52
SWIPE = 0.34          # window slide duration
SWIPE_LEAD = 0.20     # facecam pops, THEN the window comes in
PRESENTER_ANCHOR = "bottom-right"


# ------------------------------------------------------- shots from speech ---
def derive_spans(words, n, total):
    """Split the runtime at the n-1 biggest pauses between words.

    The cut follows the speech. Change the pacing and every shot re-times with
    it instead of sliding off the word it was cut to.
    """
    if n <= 1 or len(words) < n:
        return [(0.0, total)]
    gaps = sorted(((b["start"] - a["end"], a["end"], b["start"])
                   for a, b in zip(words, words[1:])), reverse=True)[:n - 1]
    cuts = sorted((g[1] + g[2]) / 2 for g in gaps)
    edges = [0.0, *cuts, total]
    return [(round(edges[i], 3), round(edges[i + 1], 3)) for i in range(len(edges) - 1)]


def spans_from_anchors(words, anchors, total):
    """Shot boundaries anchored to phrases instead of to the biggest pauses.

    derive_spans() splits at the longest silences, which is right when the take
    breathes between lines. This take does not: lines 1 to 3 are read as one
    breath, so the pause split put 10.05s of a 20.43s reel on a single shot and
    left the licence line holding 0.85s. Anchoring each shot to the words that
    open its line re-balances that without typing a single timecode, so a pacing
    change still re-times the whole edit.
    """
    cuts = [0.0]
    for a in anchors:
        s, _ = find_phrase(words, a)
        cut = round(s - 0.10, 3)
        if cut <= cuts[-1]:
            raise ValueError(f"shot anchor {a!r} lands at {cut}s, "
                             f"at or before the previous cut {cuts[-1]}s")
        cuts.append(cut)
    cuts.append(round(total, 3))
    return [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]


def find_phrase(words, phrase):
    """Locate a phrase in the transcript and return its (start, end).

    Plates are anchored to the words that are actually being said, so a pacing
    change re-times them instead of sliding them off the line they belong to.
    """
    toks = [w["w"].strip(" .,!?").lower() for w in words]
    want = [t.strip(" .,!?").lower() for t in phrase.split()]
    for i in range(len(toks) - len(want) + 1):
        if toks[i:i + len(want)] == want:
            return words[i]["start"], words[i + len(want) - 1]["end"]
    raise ValueError(f"plate phrase not in the delivered take: {phrase!r}\n"
                     f"transcript: {' '.join(toks)}")


def resolve_plate(p, words, total):
    """A plate may anchor to a phrase (preferred) or to explicit seconds."""
    if "on_phrase" in p:
        s, e = find_phrase(words, p["on_phrase"])
        return max(0.0, s - p.get("lead", 0.15)), min(total, e + p.get("hold", 1.2))
    return float(p["from"]), float(p["to"])


def build_background(shots, spans, work, fullbleed=False, swipes=None, total=0.0):
    """One background video, exactly as long as the take.

    Layout, and this is the fix for the banner that covered an install command
    for weeks: the SHARP b-roll is confined to the content band, underneath the
    furniture zone. The rest of the frame is the same footage blurred and pushed
    down, so the frame is still full bleed and no second is a dead plate, but
    nothing the banner sits on is load bearing.

    filter_complex is safe here specifically because there is no audio anywhere
    in this stage. The 3.2 seconds of voice that once vanished went missing in a
    filter_complex that carried audio.
    """
    # With swipes, a shot is on screen from its own slide-in to the next one,
    # which is NOT the same as its span: on a line where he holds full frame
    # first, the previous shot has to persist behind him until he shrinks away.
    if swipes:
        W = [0.0] + [t for _, t, _ in swipes]
        DS = [d for _, _, d in swipes]
        durs = [W[i + 1] + DS[i] - W[i] for i in range(len(W) - 1)]
        durs.append(total - W[-1] + 0.30)
    else:
        durs = [e - s for s, e in spans]

    parts = []
    for i, ((s, e), clip) in enumerate(zip(spans, shots)):
        clip = need(clip, f"b-roll shot {i}")
        dur = durs[i]
        p = work / f"bg{i:02d}.mp4"
        if fullbleed:
            # The shot already IS the whole frame. The band and its blurred
            # surround exist to stop a graphic reading as a floating card; a
            # real desktop does not need that, and cropping one into a band
            # would throw away the thing the line is about.
            fc = (f"[0:v]scale={C.W}:{C.H}:force_original_aspect_ratio=increase,"
                  f"crop={C.W}:{C.H},fps={C.FPS}[v]")
        else:
            fc = (
                f"[0:v]scale={C.W}:{C.H}:force_original_aspect_ratio=increase,"
                f"crop={C.W}:{C.H},gblur=sigma=26,eq=brightness=-0.24:saturation=0.55,"
                f"fps={C.FPS}[bgd];"
                f"[0:v]scale={C.W}:{C.BAND_H}:force_original_aspect_ratio=increase,"
                f"crop={C.W}:{C.BAND_H},fps={C.FPS}[band];"
                f"[bgd][band]overlay=0:{C.CONTENT_TOP}[v]"
            )
        run([ffmpeg(), "-y", "-loglevel", "error",
             "-stream_loop", "-1", "-i", str(clip), "-t", f"{dur:.3f}",
             "-filter_complex", fc, "-map", "[v]",
             "-an", "-c:v", "libx264", "-crf", "16", "-preset", "veryfast",
             "-pix_fmt", "yuv420p", str(p)])
        parts.append(p)
    bg = (work / "bg.mp4").resolve()
    if not swipes:
        lst = work / "bglist.txt"
        lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
        run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", lst.name, "-c", "copy", str(bg)], cwd=work)
        return bg

    # Swipe between shots instead of cutting. The direction is the side the
    # facecam just popped up on, so the window appears to come in from behind
    # him, and the swipe starts LEAD after the pop so the eye is already there.
    ins, chain, last = [], [], "0:v"
    for part in parts:
        ins += ["-i", str(part)]
    for i, (direction, at, dur) in enumerate(swipes, start=1):
        tag = f"x{i}"
        chain.append(f"[{last}][{i}:v]xfade=transition={direction}:"
                     f"duration={dur:.3f}:offset={at:.3f}[{tag}]")
        last = tag
    run([ffmpeg(), "-y", "-loglevel", "error", *ins,
         "-filter_complex", ";".join(chain), "-map", f"[{last}]",
         "-t", f"{total:.3f}", "-an", "-c:v", "libx264", "-crf", "16",
         "-preset", "veryfast", "-pix_fmt", "yuv420p", str(bg)])
    print(f"[final] {len(swipes)} swipe transitions, {SWIPE:.2f}s each")
    return bg


# ------------------------------------------------------------- raw readers ---
def reader(src, w, h, pix="rgb24", flip=False):
    vf = ("hflip," if flip else "") + f"scale={w}:{h},fps={C.FPS}"
    return subprocess.Popen(
        [ffmpeg(), "-loglevel", "error", "-i", str(src),
         "-vf", vf, "-f", "rawvideo", "-pix_fmt", pix, "-"],
        stdout=subprocess.PIPE)


# -------------------------------------------------------------- compositor ---
# ------------------------------------------------------------ presenter ----
# 264x469 keeps the 9:16 of the take. The size is set by the corners, not by
# taste: with the banner ending at 370 and the caption band measured at frame y 1298..1429,
# the usable column is 948px tall. At the first size tried, 320x569, the top
# and bottom slots sat 181px apart and read as one position rather than four.
MINI_W, MINI_H = 264, 469
MINI_MARGIN = 44
MINI_TOP_Y, MINI_BOT_Y = 400, 800
CORNERS = {
    "tl": (MINI_MARGIN, MINI_TOP_Y),
    "tr": (C.W - MINI_W - MINI_MARGIN, MINI_TOP_Y),
    "bl": (MINI_MARGIN, MINI_BOT_Y),
    "br": (C.W - MINI_W - MINI_MARGIN, MINI_BOT_Y),
}
POP_IN, POP_OUT = 0.18, 0.12   # the pop finishes just before the window slides in


def mini_window(frame_full, k):
    """The take as a floating video window: rounded, rimmed, with a shadow.

    It carries his own background rather than a cutout, because the ask was to
    keep his full view and shrink it, not to matte him onto the desktop.
    """
    w = max(2, int(MINI_W * k))
    h = max(2, int(MINI_H * k))
    vid = frame_full.resize((w, h), Image.LANCZOS).convert("RGBA")
    r = max(6, int(28 * k))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    vid.putalpha(m)
    pad = 46
    lay = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    sil = Image.new("RGBA", (w, h), (0, 0, 0, 150))
    sil.putalpha(Image.eval(m, lambda v: int(v * 0.60)))
    sh.paste(sil, (pad, pad + int(14 * k)), sil)
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    lay.alpha_composite(vid, (pad, pad))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([pad, pad, pad + w - 1, pad + h - 1], radius=r,
                        outline=(255, 255, 255, 130), width=max(1, int(3 * k)))
    return lay, pad


def presenter_at(t, track):
    """Which mode the presenter is in at time t, and the pop scale.

    Every segment pops off at its end and pops on at the next corner, so the
    window never slides across the frame; it disappears and reappears somewhere
    else, which is what was asked for.
    """
    for seg in track:
        a, z = seg["from"], seg["to"]
        if not (a <= t < z):
            continue
        if seg["mode"] == "full":
            return "full", 1.0, None
        # A line that explains the process opens on his full view and only then
        # drops to the corner, so the face carries the explanation and the UI
        # still gets its evidence beat.
        cut = seg.get("full_until")
        if cut is not None:
            if t < cut:
                return "full", 1.0, None
            a = cut
        dt, rem = t - a, z - t
        if dt < POP_IN:                       # overshoot in
            u = dt / POP_IN
            k = 0.55 + 0.53 * (1 - (1 - u) ** 3)
            k = k if u > 0.72 else k * 1.0
            k = min(k, 1.12)
        elif rem < POP_OUT:                   # snap out
            k = max(0.0, rem / POP_OUT) ** 1.6
        else:
            k = 1.0
        return "mini", k, seg["corner"]
    return None, 0.0, None


def edge_feather(pw, ph, side="right", edge=70, bottom=90):
    """A ramp that kills the cutout's own rectangle edge.

    The take is chest up and his shoulders run off both sides of the phone
    frame, so the matte is hard against its own border. Composited straight,
    that border draws a vertical line down the frame and the cutout reads as a
    box, which is the one thing beat 3 says it must never be. The left edge is
    parked at x=0 so it falls outside the frame; the right and bottom edges get
    a ramp instead.
    """
    a = np.ones((ph, pw), np.float32)
    if edge:
        ramp = np.linspace(1.0, 0.0, edge, dtype=np.float32)
        if side == "right":
            a[:, pw - edge:] *= ramp[None, :]
        else:
            a[:, :edge] *= ramp[::-1][None, :]
    if bottom:
        a[ph - bottom:, :] *= np.linspace(1.0, 0.0, bottom, dtype=np.float32)[:, None]
    return a


def eased_plate(layer, t, a, z):
    """A plate rises 36px while fading in, and fades out. No hard pop on or off."""
    k = out_cubic(window(t, a, a + PLATE_IN)) * (1 - window(t, z - PLATE_OUT, z))
    if k >= 0.999:
        return layer, (0, 0)
    faded = layer.copy()
    faded.putalpha(layer.getchannel("A").point(lambda v: int(v * k)))
    return faded, (0, int((1 - out_cubic(window(t, a, a + PLATE_IN))) * 36))


def compose(spec, work, bg, take, matte, words, total, out_video):
    pal = C.PALETTES[spec["palette"]]
    flip = bool(spec.get("presenter_flip", False))
    track = spec["presenter_track"]
    lead = float(spec.get("opener_seconds", 0.0))
    r_bg = reader(bg, C.W, C.H)
    r_pv = reader(take, C.W, C.H, flip=flip)

    enc = subprocess.Popen(
        [ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{C.W}x{C.H}", "-r", str(C.FPS), "-i", "-",
         "-an", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_video)],
        stdin=subprocess.PIPE)

    banner = theme.banner(pal, spec["banner"], spec["handle"])
    plates = []
    for p in spec.get("plates", []):
        a, z = resolve_plate(p, words, total)
        plates.append((a, z, theme.plate(pal, p["text"], p.get("y", 520),
                                         p.get("sub"), p.get("emoji"))))
        print(f"[final] plate {p['text']!r} -> {a:.2f}s..{z:.2f}s")

    frames = int(round(total * C.FPS))
    for f in range(frames):
        t = f / C.FPS
        b = r_bg.stdout.read(C.W * C.H * 3)
        # the take is only consumed once the cold open is over, otherwise the
        # presenter runs `lead` seconds ahead of the track that places him
        v = r_pv.stdout.read(C.W * C.H * 3) if t >= lead else b""
        if len(b) < C.W * C.H * 3:
            break
        frame = Image.frombytes("RGB", (C.W, C.H), b).convert("RGBA")

        mode, k, corner = presenter_at(t, track)
        if len(v) == C.W * C.H * 3 and mode:
            take_fr = Image.frombytes("RGB", (C.W, C.H), v)
            if mode == "full":
                frame.alpha_composite(take_fr.convert("RGBA"))
            elif k > 0.02:
                lay, pad = mini_window(take_fr, k)
                cx, cy = CORNERS[corner]
                # a slow float so the window never sits dead still
                fy = int(round(9 * math.sin(2 * math.pi * t / 2.4)))
                ox = cx + (MINI_W - int(MINI_W * k)) // 2
                oy = cy + (MINI_H - int(MINI_H * k)) // 2 + fy
                frame.alpha_composite(lay, (ox - pad, oy - pad))

        frame.alpha_composite(banner)
        frame.alpha_composite(theme.progress(pal, t, total))
        for a, z, layer in plates:
            if a <= t <= z:
                frame.alpha_composite(*eased_plate(layer, t, a, z))
        if spec.get("captions", True):
            frame.alpha_composite(theme.captions(pal, words, t,
                                                 pop=spec.get("caption_pop", True)))

        enc.stdin.write(frame.convert("RGB").tobytes())
        if f % 30 == 0:
            print(f"[final] frame {f}/{frames}", end="\r")

    enc.stdin.close()
    enc.wait()
    for r in (r_bg, r_pv):
        # kill first, then close: closing a pipe a reader is still filling makes
        # ffmpeg shout "broken pipe" into the build log for no reason.
        if r.poll() is None:
            r.kill()
        r.stdout.close()
        r.wait()
    print(f"[final] composited {frames} frames -> {out_video.name}")
    return out_video


# ------------------------------------------------------------------ deliver --
def contact_sheet(mp4, out_jpg, n=16):
    """Sixteen frames across the runtime. One question: does anything overlap?"""
    d = duration(mp4)
    work = out_jpg.parent / "_sb"
    work.mkdir(exist_ok=True)
    for f in work.glob("*.png"):
        f.unlink()
    for i in range(n):
        t = d * (i + 0.5) / n
        run([ffmpeg(), "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(mp4),
             "-frames:v", "1", "-vf", "scale=270:480", str(work / f"f{i:02d}.png")])
    # numbered sequence, not -pattern_type glob: Windows ffmpeg builds have no glob
    run([ffmpeg(), "-y", "-loglevel", "error", "-start_number", "0",
         "-i", str(work / "f%02d.png"), "-filter_complex", "tile=4x4:margin=8:padding=6",
         "-frames:v", "1", "-q:v", "3", str(out_jpg)])
    shutil.rmtree(work)  # scratch frames; the delivery folder keeps only the deliverables
    print(f"[deliver] contact sheet -> {out_jpg.name}")
    return out_jpg


def build(project):
    project = Path(project)
    spec = json.loads(need(project / "reel.json", "reel.json").read_text())
    work = project / "_work"
    work.mkdir(exist_ok=True)

    take = need(project / "take_trim.mp4", "trimmed take")
    matte = None      # the presenter is a video window now, not a cutout
    wj = json.loads(need(project / "words_trim.json", "words_trim.json").read_text())
    words, total = wj["words"], duration(take)

    ceiling = float(spec.get("max_seconds", C.MAX_SECONDS))
    if total > ceiling + 0.6:
        raise RuntimeError(f"{total:.2f}s is over the {ceiling}s ceiling")

    shots = [project / s for s in spec["shots"]]
    if spec.get("shot_anchors"):
        anchors = spec["shot_anchors"]
        if len(anchors) != len(shots) - 1:
            raise ValueError(f"{len(shots)} shots need {len(shots) - 1} anchors, "
                             f"got {len(anchors)}")
        spans = spans_from_anchors(words, anchors, total)
    else:
        spans = derive_spans(words, len(shots), total)
    print(f"[final] spans from speech: {spans}")

    # A cold open sits in front of everything and pushes the whole reel back.
    # Shifting here rather than in the spec keeps reel.json authored in take
    # time, so the anchors and the track stay readable.
    lead = float(spec.get("opener_seconds", 0.0))
    track = spec["presenter_track"]
    if lead > 0:
        shots = [project / spec["opener"]] + shots
        spans = [(0.0, lead)] + [(a + lead, b + lead) for a, b in spans]
        track = [{**g, "from": g["from"] + lead, "to": g["to"] + lead,
                  **({"full_until": g["full_until"] + lead} if "full_until" in g else {})}
                 for g in track]
        total += lead

    swipes = None
    if spec.get("swipe_windows"):
        swipes = []
        if lead > 0:
            # the montage hard cuts into the hook; a slide would soften it
            swipes.append(("fade", lead, 0.04))
        for seg in track[1:]:
            corner = seg.get("corner", "bl")
            # a right hand corner means the window arrives from the right,
            # which is what slideleft does
            direction = "slideleft" if corner.endswith("r") else "slideright"
            popped = seg.get("full_until", seg["from"])
            swipes.append((direction, popped + SWIPE_LEAD, SWIPE))
    spec = {**spec, "presenter_track": track}
    bg = build_background(shots, spans, work, spec.get("fullbleed", False),
                          swipes, total)
    silent = work / "video_only.mp4"
    compose(spec, work, bg, take, matte, words, total, silent)
    if has_audio(silent):
        raise RuntimeError("video track should be silent at this stage")

    raw_wav = work / "raw.wav"
    af = f"adelay={int(lead*1000)}|{int(lead*1000)}" if lead > 0 else "anull"
    run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(take), "-vn",
         "-af", af,
         "-ar", str(C.SAMPLE_RATE), "-ac", str(C.CHANNELS), "-c:a", "pcm_s16le",
         str(raw_wav)])
    mastered = work / "mastered.wav"
    master(raw_wav, mastered)

    C.DELIVERY.mkdir(parents=True, exist_ok=True)
    name = spec["slug"]
    out = C.DELIVERY / f"{name}.mp4"
    run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(silent), "-i", str(mastered),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-ar", str(C.SAMPLE_RATE),
         "-shortest", "-movflags", "+faststart", str(out)])
    contact_sheet(out, C.DELIVERY / f"{name}_SB.jpg")
    print(f"[deliver] {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    a = ap.parse_args()
    build(a.project)
