#!/usr/bin/env python3
"""Stage -1: pull a reference reel off any platform, then MEASURE it.

`decode_reference.py` takes a local file. This takes a URL, from YouTube,
Instagram, TikTok, X or Facebook, fetches the media plus whatever public
engagement numbers the platform will give up, and hands the file to the decoder.

    python3 pull_reference.py "https://www.instagram.com/reel/XXXX/"
    python3 pull_reference.py "https://www.youtube.com/shorts/XXXX" --no-decode
    python3 pull_reference.py URL1 URL2 URL3 --out ~/Documents/Notes/refs

Auth: everything runs off the logged-in Chrome profile's cookies. Nothing is
typed, nothing is stored, no password is handled here. YouTube now refuses
anonymous requests outright, so cookies are not optional.

Verified working 2026-08-22 on this machine: yt-dlp 2026.07.04,
gallery-dl 1.31.10, Chrome 151. 608 cookies read from the Chrome profile.

Per-platform reality, measured not assumed:
  youtube    yt-dlp, needs Chrome cookies or it returns "Please sign in"
  instagram  gallery-dl for the media. Post metrics come from the public
             web_profile_info endpoint, which needs no auth at all
  tiktok     yt-dlp
  x          yt-dlp, cookies required, gets flaky when rate limited
  facebook   yt-dlp, cookies required, public videos only
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Windows Chrome 127+ app-bound encryption blocks yt-dlp's cookie read. There, use
# REEL_COOKIE_BROWSER=firefox (or edge) after logging in once in that browser.
BROWSER = os.environ.get("REEL_COOKIE_BROWSER", "chrome")
# Run as modules: pip often puts the .exe shims in a Scripts dir that is not on PATH.
YTDLP = [sys.executable, "-m", "yt_dlp"]
GALLERYDL = [sys.executable, "-m", "gallery_dl"]
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # titles carry emoji; cp1252 dies


def platform_of(url):
    u = url.lower()
    for name, pats in {
        "youtube": ("youtube.com", "youtu.be"),
        "instagram": ("instagram.com",),
        "tiktok": ("tiktok.com",),
        "x": ("twitter.com", "x.com"),
        "facebook": ("facebook.com", "fb.watch"),
    }.items():
        if any(p in u for p in pats):
            return name
    return "generic"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def ytdlp_meta(url):
    r = run([*YTDLP, "--cookies-from-browser", BROWSER, "--no-warnings",
             "--skip-download", "--dump-single-json", url])
    if r.returncode != 0:
        return None, r.stderr.strip().splitlines()[-1] if r.stderr else "failed"
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None, "could not parse yt-dlp json"
    return {
        "title": d.get("title"),
        "uploader": d.get("uploader") or d.get("channel"),
        "duration": d.get("duration"),
        "views": d.get("view_count"),
        "likes": d.get("like_count"),
        "comments": d.get("comment_count"),
        "upload_date": d.get("upload_date"),
        "description": (d.get("description") or "")[:400],
    }, None


def ig_meta(url):
    """Post metrics off the public endpoint. No auth, no cookies."""
    m = re.search(r"instagram\.com/([^/]+)/", url)
    owner = None
    if m and m.group(1) not in ("p", "reel", "reels", "tv"):
        owner = m.group(1)
    code = re.search(r"/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)", url)
    if not owner or not code:
        return None
    r = run(["curl", "-s", "-H", "X-IG-App-ID: 936619743392459",
             f"https://www.instagram.com/api/v1/users/web_profile_info/?username={owner}"])
    try:
        edges = json.loads(r.stdout)["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
    except Exception:
        return None
    for e in edges:
        n = e["node"]
        if n.get("shortcode") == code.group(1):
            cap = n["edge_media_to_caption"]["edges"]
            return {
                "views": n.get("video_view_count"),
                "likes": n["edge_media_preview_like"]["count"],
                "comments": n["edge_media_to_comment"]["count"],
                "caption": (cap[0]["node"]["text"] if cap else "")[:400],
            }
    return None


def fetch(url, outdir, plat):
    outdir.mkdir(parents=True, exist_ok=True)
    before = set(outdir.glob("*"))
    if plat == "instagram":
        cmd = [*GALLERYDL, "--cookies-from-browser", BROWSER,
               "-D", str(outdir), url]
    else:
        cmd = [*YTDLP, "--cookies-from-browser", BROWSER, "--no-warnings",
               "-f", "mp4/bestvideo+bestaudio/best",
               "-o", str(outdir / "%(id)s.%(ext)s"), url]
    r = run(cmd)
    new = [p for p in outdir.glob("*") if p not in before and p.is_file()]
    vids = [p for p in new if p.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov")]
    if not vids:
        tail = (r.stderr or r.stdout or "").strip().splitlines()
        return None, tail[-1] if tail else "no media produced"
    return max(vids, key=lambda p: p.stat().st_size), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--out", default=str(HERE / "refs"))
    ap.add_argument("--no-decode", action="store_true")
    a = ap.parse_args()

    outdir = Path(a.out).expanduser()
    failures = 0

    for url in a.urls:
        plat = platform_of(url)
        print("=" * 70)
        print(f"{plat}  {url}")
        print("=" * 70)

        meta = ig_meta(url) if plat == "instagram" else None
        if meta is None:
            meta, err = ytdlp_meta(url)
            if meta is None:
                print(f"  metadata unavailable: {err}")
        if meta:
            for k, v in meta.items():
                if v not in (None, "", 0):
                    print(f"  {k:<12} {v}")
            if meta.get("views") and meta.get("comments"):
                print(f"  {'cmt/view':<12} {meta['comments'] / meta['views'] * 100:.2f}%")
        print()

        f, err = fetch(url, outdir, plat)
        if not f:
            print(f"  DOWNLOAD FAILED: {err}\n")
            failures += 1
            continue
        print(f"  saved  {f}  ({f.stat().st_size:,} bytes)\n")

        if not a.no_decode:
            subprocess.run([sys.executable, str(HERE / "decode_reference.py"), str(f)])
        print()

    if failures:
        print(f"{failures} of {len(a.urls)} failed. Cookies expire; if a platform "
              f"refuses, open it in Chrome once and retry.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
