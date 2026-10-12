#!/usr/bin/env python3
"""Stage 0: open a reel. Claims the CTA keyword before anything else exists.

The keyword is said on camera and cannot change afterwards, so it is burned into
the ledger here, at the top of the job, and the ledger refuses a repeat.

    python3 newreel.py vet-scan --palette security --cta VET \
        --banner "one in four had a hole" --handle "@billy.coder"
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from lib.util import burn_keyword, lint_text

TEMPLATE = {
    "slug": None, "palette": None, "cta": None, "banner": None, "handle": None,
    "forbid": [],
    "script": {
        "1_hook": "", "2_scale": "", "3_personal": "",
        "4_proof": "", "5_licence": "", "6_cta": ""
    },
    "shots": ["broll_1.mp4", "broll_2.mp4", "broll_3.mp4"],
    # final.py requires this. Face full on the hook, then a corner window over
    # the proof. Times are take seconds; corners are tl tr bl br.
    "presenter_track": [
        {"from": 0.0, "to": 3.0, "mode": "full"},
        {"from": 3.0, "to": 60.0, "mode": "mini", "corner": "br"}
    ],
    "plates": [
        {"from": 0.0, "to": 3.0, "text": "", "sub": "", "y": 520, "emoji": None}
    ],
    "caption": {"hook": "", "what": "", "licence": "", "cta": "", "hashtags": []}
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--palette", required=True, choices=sorted(C.PALETTES))
    ap.add_argument("--cta", required=True)
    ap.add_argument("--banner", required=True)
    ap.add_argument("--handle", default="@billy.coder")
    ap.add_argument("--forbid", nargs="*", default=[])
    a = ap.parse_args()

    lint_text(a.banner, "banner", hook=True)
    d = C.PROJECTS / a.slug
    if d.exists():
        sys.exit(f"{d} already exists")   # before the burn, or the keyword is wasted
    cta = burn_keyword(a.cta, a.slug)
    d.mkdir(parents=True)

    spec = dict(TEMPLATE, slug=a.slug, palette=a.palette, cta=cta,
                banner=a.banner, handle=a.handle, forbid=a.forbid)
    (d / "reel.json").write_text(json.dumps(spec, indent=2))
    print(f"[new] {d}\n[new] CTA {cta} burned into {C.BURNED_KEYWORDS.name}")
    print("[new] drop take.mp4 in, fill reel.json, then run the stages")


if __name__ == "__main__":
    main()
