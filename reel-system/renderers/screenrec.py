#!/usr/bin/env python3
"""B-roll renderer A: real screens, driven by Playwright.

Proof on a real screen is beat 2 and it is the beat that turns a like into a
comment. This records an actual page or an actual local HTML surface at
1080 wide, then scales into the content band.

Two guards baked in:
  * BLUR_SELECTORS masks anything that would name the tool. Never show the repo.
  * the recording is checked for a non zero duration before it is returned.

    python3 renderers/screenrec.py https://example.com out.mp4 --seconds 5
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as C
from lib.util import ffmpeg, run, duration

VIEW_W, VIEW_H = 1080, 1200          # fits the content band once scaled


def record(url, out, seconds=5.0, scroll=True, blur_selectors=(), script=None):
    out = Path(out)
    tmp = out.parent / "_pw"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--force-device-scale-factor=1"])
        ctx = b.new_context(viewport={"width": VIEW_W, "height": VIEW_H},
                            record_video_dir=str(tmp),
                            record_video_size={"width": VIEW_W, "height": VIEW_H})

        # The mask goes in as an init script so it is live on the FIRST painted
        # frame. Applying it after goto() leaves the repo name readable on the
        # opening frames of the recording, which is the exact way a repo name
        # shipped on one frame once and flattened the comment count.
        if blur_selectors:
            css = " ".join(f"{s}{{filter:blur(16px)!important;"
                           f"user-select:none!important;}}" for s in blur_selectors)
            ctx.add_init_script("""(css => {
                const add = () => {
                  const s = document.createElement('style');
                  s.textContent = css;
                  (document.head || document.documentElement).appendChild(s);
                };
                if (document.documentElement) add();
                else document.addEventListener('readystatechange', add, {once:true});
            })(%s)""" % json.dumps(css))

        pg = ctx.new_page()
        # networkidle is the right default for a repo page, but a marketing site
        # with live telemetry never goes idle and goto() then times out with
        # nothing recorded. Fall back to load + a settle, rather than failing the
        # shot. The settle is what stops us recording a half painted page.
        try:
            pg.goto(url, wait_until="networkidle", timeout=25000)
        except Exception:
            print(f"[screenrec] {url} never reached networkidle, "
                  f"falling back to load + settle")
            pg.goto(url, wait_until="load", timeout=60000)
            pg.wait_for_timeout(4000)

        # Prove the mask actually landed. A selector typo must not pass silently.
        for sel in blur_selectors:
            n = pg.eval_on_selector_all(sel, "els => els.length")
            if n == 0:
                raise RuntimeError(f"blur selector {sel!r} matched 0 elements. "
                                   f"The gate is the business model, fix the selector.")
            blurred = pg.eval_on_selector_all(
                sel, "els => els.every(e => getComputedStyle(e).filter.includes('blur'))")
            if not blurred:
                raise RuntimeError(f"blur selector {sel!r} matched {n} elements "
                                   f"but the blur did not apply")
            print(f"[screenrec] masked {n} element(s) matching {sel!r}")
        if script:
            pg.evaluate(script)

        steps = max(1, int(seconds * 10))
        for i in range(steps):
            if scroll:
                pg.mouse.wheel(0, 26)
            pg.wait_for_timeout(100)
        ctx.close()
        b.close()

    webm = next(tmp.glob("*.webm"))
    run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(webm),
         "-vf", f"fps={C.FPS},scale={VIEW_W}:-2",
         "-an", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)])
    shutil.rmtree(tmp, ignore_errors=True)

    d = duration(out)
    if d < 0.5:
        raise RuntimeError(f"screen recording is {d:.2f}s, something did not load")
    print(f"[screenrec] {url} -> {out.name} {d:.2f}s")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--no-scroll", action="store_true")
    ap.add_argument("--blur", nargs="*", default=[])
    a = ap.parse_args()
    record(a.url, a.out, a.seconds, not a.no_scroll, a.blur)
