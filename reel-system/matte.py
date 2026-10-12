#!/usr/bin/env python3
"""Stage 3 of the edit: cut the presenter out of the background.

torchvision DeepLabV3 MobileNetV3 (COCO/VOC, person = class 15) run per frame on
CPU, written out as a greyscale matte video. No box, no border. The compositor
in final.py multiplies the take by this matte so the face and the evidence share
one frame.

    python3 matte.py projects/<slug>/take_trim.mp4
    -> take_trim_matte.mp4  (greyscale, same fps/length)
"""
import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.util import ffmpeg, need, probe

PERSON = 15
INFER_H = 384          # infer small, upscale the matte. 4x faster, no visible loss.
FEATHER = 3            # px of edge softening


def build(src, out=None, infer_h=INFER_H):
    import torch
    from torchvision.models.segmentation import (
        deeplabv3_mobilenet_v3_large, DeepLabV3_MobileNet_V3_Large_Weights)

    src = need(src, "trimmed take")
    out = Path(out) if out else src.with_name(src.stem + "_matte.mp4")
    v = next(s for s in probe(src)["streams"] if s["codec_type"] == "video")
    W, H = int(v["width"]), int(v["height"])
    fps = eval(v["r_frame_rate"])  # e.g. "30/1"
    iw = int(round(W * infer_h / H / 2) * 2)

    net = deeplabv3_mobilenet_v3_large(
        weights=DeepLabV3_MobileNet_V3_Large_Weights.DEFAULT).eval()
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)

    dec = subprocess.Popen(
        [ffmpeg(), "-loglevel", "error", "-i", str(src),
         "-vf", f"scale={iw}:{infer_h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE)
    enc = subprocess.Popen(
        [ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray",
         "-s", f"{iw}x{infer_h}", "-r", str(fps), "-i", "-",
         "-vf", f"scale={W}:{H},gblur=sigma={FEATHER}",
         "-c:v", "libx264", "-crf", "12", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE)

    n = 0
    with torch.no_grad():
        while True:
            buf = dec.stdout.read(iw * infer_h * 3)
            if len(buf) < iw * infer_h * 3:
                break
            arr = np.frombuffer(buf, np.uint8).reshape(infer_h, iw, 3)
            t = torch.from_numpy(arr.copy()).permute(2, 0, 1).float() / 255.0
            t = ((t - mean) / std).unsqueeze(0)
            logits = net(t)["out"][0]
            m = (logits.argmax(0) == PERSON).numpy().astype(np.uint8) * 255
            enc.stdin.write(m.tobytes())
            n += 1
            if n % 30 == 0:
                print(f"[matte] {n} frames", end="\r")

    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"[matte] {n} frames -> {out.name}")
    if n == 0:
        raise RuntimeError("matte produced 0 frames, check the source video")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o", "--out")
    ap.add_argument("--infer-h", type=int, default=INFER_H)
    a = ap.parse_args()
    build(a.src, a.out, a.infer_h)
