#!/usr/bin/env python3
"""B-roll renderer E: 3D, via three.js in headless Chromium.

Two scenes:
  bars    3D price bars. The paid thing towers, the open one sits at zero.
          Bars grow staggered with a small overshoot and the price counts up
          with them while the camera drifts round. Beat 1 with depth.
  model   a turntable of a real object from a .glb (the project's own CAD or
          scan export). Beat 2 when the proof is a physical thing.

Deterministic, not a screen recording: the page has no animation loop. Each
frame is renderAt(t) then a screenshot, so a rebuild is frame identical and
beats are FRACTIONS of the shot like every other renderer. three.js is vendored
in assets/three (0.170.0, MIT), so nothing is fetched at render time.

    python3 renderers/scene3d.py out.mp4 bars --palette money --seconds 5 \\
        --bar "DocuSign|50" --bar "This one|0" --prefix "$" --suffix "/mo"
    python3 renderers/scene3d.py out.mp4 model --glb rover.glb --palette hardware
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as C
from lib.util import ffmpeg, need, lint_text, duration

GW, GH = 1080, 1240          # same content band as the other renderers
THREE = C.ASSETS / "three"
HOST = "http://reel.local"
# headless Chromium has no GPU; SwiftShader is its software WebGL
GL_ARGS = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
TYPES = {".js": "text/javascript", ".html": "text/html", ".glb": "model/gltf-binary",
         ".ttf": "font/ttf", ".ttc": "font/collection", ".otf": "font/otf"}


def render(out, kind, seconds=5.0, palette="money", bars=(), prefix="", suffix="",
           glb=None, turn=1.2, beats=(0.02, 0.62)):
    out = Path(out)
    files = {"/font/bold": need(C.FONT_BOLD, "font"), "/font/reg": need(C.FONT_REG, "font")}
    if kind == "bars":
        if not bars:
            raise ValueError("bars needs at least one --bar 'Label|value'")
        parsed = []
        for b in bars:
            lab, _, v = b.rpartition("|")
            parsed.append({"label": lint_text(lab.strip(), "3d label"), "value": float(v)})
        lint_text(prefix + suffix, "3d value affix")
    elif kind == "model":
        files["/model.glb"] = need(glb, "glb model")
        parsed = []
    else:
        raise ValueError(f"unknown scene {kind!r}")

    scene = {"kind": kind, "w": GW, "h": GH, "pal": C.PALETTES[palette], "bars": parsed,
             "prefix": prefix, "suffix": suffix, "turn": turn, "beats": list(beats)}

    def serve(route):
        path = route.request.url[len(HOST):].split("?")[0]
        f = files.get(path)
        if f is None:   # anything else must live inside assets/three
            f = (THREE / path.lstrip("/")).resolve()
            if THREE.resolve() not in f.parents or not f.is_file():
                return route.fulfill(status=404)
        route.fulfill(path=str(f), content_type=TYPES.get(f.suffix.lower(), "application/octet-stream"))

    frames = int(round(seconds * C.FPS))
    enc = subprocess.Popen(
        [ffmpeg(), "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png",
         "-r", str(C.FPS), "-i", "-",
         "-an", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE)

    from playwright.sync_api import sync_playwright
    errors = []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=GL_ARGS + ["--force-device-scale-factor=1"])
            ctx = b.new_context(viewport={"width": GW, "height": GH})
            ctx.route(f"{HOST}/**", serve)
            ctx.add_init_script(f"window.SCENE = {json.dumps(scene)};")
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(f"{HOST}/scene.html")
            pg.evaluate("document.fonts.ready")
            # errors are checked too, or a WebGL failure just waits out the timeout
            pg.wait_for_function("window.READY === true || !!window.FAILED", timeout=60000)
            failed = pg.evaluate("window.FAILED || null")
            if failed or errors:
                raise RuntimeError(f"3D scene failed: {failed or errors[0]}")
            for f in range(frames):
                pg.evaluate(f"renderAt({f / max(frames - 1, 1)})")
                enc.stdin.write(pg.screenshot(type="png"))
            if errors:
                raise RuntimeError(f"3D scene error mid render: {errors[0]}")
            b.close()
    finally:
        enc.stdin.close()
        enc.wait()

    d = duration(out)
    if d < seconds - 0.2:
        raise RuntimeError(f"3D shot is {d:.2f}s, wanted {seconds}s")
    print(f"[scene3d] {kind} {frames} frames -> {out.name} {d:.2f}s")
    if kind == "bars":
        print("[scene3d] NO INVENTED NUMBERS. Every bar value must be a published "
              "figure, verified the day you shoot.")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("kind", choices=["bars", "model"])
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--palette", default="money", choices=sorted(C.PALETTES))
    ap.add_argument("--bar", action="append", default=[], help="'Label|value', repeatable")
    ap.add_argument("--prefix", default="", help='e.g. "$"')
    ap.add_argument("--suffix", default="", help='e.g. "/mo"')
    ap.add_argument("--glb", help="model scene: path to a .glb")
    ap.add_argument("--turn", type=float, default=1.2, help="model scene: radians of spin")
    a = ap.parse_args()
    render(a.out, a.kind, a.seconds, a.palette, a.bar, a.prefix, a.suffix, a.glb, a.turn)
