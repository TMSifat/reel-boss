#!/usr/bin/env python3
"""
addmusic.py — drop the standing background bed onto a finished reel.

The recipe was tuned by ear over bc-012-guard-dart / -data and bc-020-once,
and every number here was measured, not guessed:

  bed sits 4.8 dB under the video's own voice     (the level the user approved)
  +5.5 dB intro lift decaying to 0 dB by t=2.5s   (the track's attack is soft AND
                                                   the hook is the loudest moment,
                                                   so the bed opened ~10 dB down
                                                   without this)
  sidechain duck 0.06 / 4 / 15ms / 350ms          (music dips only while he talks)
  0.6s fade at the tail, none at the head         (music must be audible on frame 0)
  video stream COPIED                             (no re-encode, no quality loss)

The multiplier is NOT transferable between videos: each cut has its own voice
level and its own density, so the same vol lands at a different bed. This solves
for it per video instead of reusing a number.

Usage:
  python3 addmusic.py video-assets/bc-020-once-desktop.mp4
  python3 addmusic.py IN.mp4 -o OUT.mp4 --gap 4.8
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

# No default track. The old default was a commercial song: a rights claim, and
# Instagram's repost filter flags shared audio. Use a track you have rights to.
MUSIC = os.environ.get("REEL_MUSIC")
DUCK = "sidechaincompress=threshold=0.06:ratio=4:attack=15:release=350:makeup=1"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(v, entries, stream=None, count_frames=False):
    cmd = ["ffprobe", "-v", "error"]
    if stream:
        cmd += ["-select_streams", stream]
    if count_frames:
        # nb_read_frames is only populated when frames are actually counted
        cmd += ["-count_frames"]
    cmd += ["-show_entries", entries, "-of", "csv=p=0", v]
    return run(cmd).stdout.strip()


def mean_db(path, ss=None, t=None):
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if ss is not None:
        cmd += ["-ss", str(ss)]
    if t is not None:
        cmd += ["-t", str(t)]
    cmd += ["-i", path, "-af", "volumedetect", "-f", "null", "-"]
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", run(cmd).stderr)
    return float(m.group(1)) if m else None


def music_filter(vol, fade_out_at, atrim_to, split_for_mix):
    """The music chain. split_for_mix=True also emits the mixed [mix] pad."""
    expr = f"{vol:.4f}*(1+0.884*max(0\\,(2.5-t)/2.5))"
    mus = (f"[1:a]atrim=0:{atrim_to},asetpts=N/SR/TB,"
           f"volume=volume='{expr}':eval=frame,"
           f"afade=t=out:st={fade_out_at}:d=0.6[mus]")
    if not split_for_mix:
        return f"{mus};[0:a]asetpts=N/SR/TB[sc];[mus][sc]{DUCK}[duck]"
    return (f"{mus};[0:a]asplit=2[vo][sc];[mus][sc]{DUCK}[duck];"
            f"[vo][duck]amix=inputs=2:duration=first:dropout_transition=0:"
            f"normalize=0[mix]")


def render(video, music, vol, dur, fade_out_at, atrim_to, out, pad):
    fc = music_filter(vol, fade_out_at, atrim_to, split_for_mix=(pad == "mix"))
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostats", "-y",
         "-i", video, "-stream_loop", "-1", "-i", music,
         "-filter_complex", fc, "-map", f"[{pad}]", "-t", str(dur), out],
        check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("-m", "--music", default=MUSIC,
                    help="a track you have the rights to (or set REEL_MUSIC)")
    ap.add_argument("--gap", type=float, default=4.8,
                    help="dB the bed sits under the voice (default 4.8, approved)")
    a = ap.parse_args()

    if not a.music:
        sys.exit("no music: pass -m TRACK (one you have the rights to) or set REEL_MUSIC")
    a.music = os.path.expanduser(a.music)
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):          # `which` does not exist on Windows
            sys.exit(f"missing tool: {tool}")
    for p in (a.video, a.music):
        if not os.path.exists(p):
            sys.exit(f"not found: {p}")

    dur = float(probe(a.video, "format=duration"))
    frames_in = probe(a.video, "stream=nb_read_frames", "v", count_frames=True)
    if not probe(a.video, "stream=index", "a"):
        sys.exit("video has no audio track — nothing to duck against")

    voice = mean_db(a.video)
    target = voice + -abs(a.gap)
    fade_at = round(dur - 0.6, 6)
    atrim = round(dur + 0.05, 6)
    out = a.out or os.path.splitext(a.video)[0] + "_with_music.mp4"

    print(f"video   {os.path.basename(a.video)}  {dur:.6f}s  {frames_in}f")
    print(f"voice   {voice:.1f} dB   ->  target bed {target:.1f} dB "
          f"({a.gap:.1f} under)")

    # Solve for the multiplier. bed_dB is ~linear in 20log10(vol), so one
    # correction lands close; iterate to be sure rather than trusting the model.
    with tempfile.TemporaryDirectory() as td:
        stem = os.path.join(td, "stem.wav")
        vol, bed = 1.0, None
        for i in range(4):
            render(a.video, a.music, vol, dur, fade_at, atrim, stem, "duck")
            bed = mean_db(stem)
            print(f"  probe vol={vol:.4f} -> bed {bed:.1f} dB "
                  f"({bed - voice:+.1f} vs voice)")
            if abs(bed - target) < 0.05:
                break
            vol *= 10 ** ((target - bed) / 20.0)

        # final: same chain plus a safety limiter, video copied untouched
        fc = music_filter(vol, fade_at, atrim, split_for_mix=True)
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostats", "-y",
             "-i", a.video, "-stream_loop", "-1", "-i", a.music,
             "-filter_complex", fc + ";[mix]alimiter=limit=0.97[aout]",
             "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
             "-movflags", "+faststart", out], check=True)

        # The bed adds energy after final.py mastered the voice, so the posted
        # file was never at -14 LUFS. Master the mixed audio again, video copied.
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from lib.util import master
        mixed, mastered = os.path.join(td, "mixed.wav"), os.path.join(td, "mastered.wav")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", out,
                        "-vn", "-c:a", "pcm_s16le", mixed], check=True)
        master(mixed, mastered)
        tmp_out = out + ".tmp.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-i", out, "-i", mastered, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", tmp_out], check=True)
        os.replace(tmp_out, out)

        # VERIFY: phase-invert the original against a lossless mix, so what
        # remains IS the bed. A mean alone would hide a silent opening.
        mix = os.path.join(td, "mix.wav")
        orig = os.path.join(td, "orig.wav")
        iso = os.path.join(td, "iso.wav")
        render(a.video, a.music, vol, dur, fade_at, atrim, mix, "mix")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostats",
                        "-y", "-i", a.video, "-map", "0:a", "-t", str(dur), orig],
                       check=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostats",
                        "-y", "-i", mix, "-i", orig, "-filter_complex",
                        "[1:a]volume=-1.0[inv];[0:a][inv]amix=inputs=2:normalize=0[d]",
                        "-map", "[d]", iso], check=True)

        iso_all = mean_db(iso)
        head = mean_db(iso, 0, 2)
        frames_out = probe(out, "stream=nb_read_frames", "v", count_frames=True)
        peak = re.search(r"max_volume:\s*(-?[\d.]+) dB",
                         run(["ffmpeg", "-hide_banner", "-nostats", "-i", out,
                              "-af", "volumedetect", "-f", "null", "-"]).stderr)

        print(f"\nvol={vol:.4f}")
        print(f"  bed        {iso_all:.1f} dB  ({iso_all - voice:+.1f} vs voice)")
        print(f"  first 2s   {head:.1f} dB   <- must NOT be silent")
        print(f"  peak       {peak.group(1) if peak else '?'} dB")
        print(f"  frames     {frames_in} -> {frames_out}"
              f"{'  OK' if frames_in == frames_out else '  MISMATCH'}")
        print(f"  duration   {dur:.6f} -> {float(probe(out, 'format=duration')):.6f}")
        print(f"\n-> {out}")


if __name__ == "__main__":
    main()
