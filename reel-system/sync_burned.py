#!/usr/bin/env python3
"""
Refresh section A of keywords_burned.txt from what is actually live on Instagram.

WHY THIS EXISTS. On 2026-08-21 the burned list held 7 words and did not contain
REPO, which was live on three posts carrying 3,546 comments between them.
`lint.sh --cta REPO` returned "clean". The list was hand maintained, so it drifted
the moment anyone posted without updating it, and the guard kept saying yes.

Section A (LIVE ON INSTAGRAM) is now derived, not typed. Sections B, C and D stay
hand maintained because they record intent rather than fact, and are preserved
byte for byte by this script.

  python3 sync_burned.py            show what would change, write nothing
  python3 sync_burned.py --write    rewrite section A in place

No auth, no API key, no cookies. The public web_profile_info endpoint is enough.
It returns only the most recent 12 posts and GraphQL pagination is auth gated, so
this CANNOT see the full history. It widens the guard, it does not complete it.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config as C  # noqa: E402

LEDGER = C.BURNED_KEYWORDS          # one ledger, the same one lint.sh reads
USER = os.environ.get("REEL_ACCOUNT", "billy.coder")
APP_ID = "936619743392459"

BEGIN = "# A. LIVE ON INSTAGRAM"
NEXT_SECTION = "# B. CLAIMED"

# words that follow "Comment" but are never the keyword
STOP = {"AND", "THE", "FOR", "BELOW", "IF", "TO", "THIS", "IT", "ME", "YOUR", "A"}


def fetch():
    url = (f"https://www.instagram.com/api/v1/users/web_profile_info/"
           f"?username={USER}")
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "X-IG-App-ID": APP_ID,
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)["data"]["user"]


def live_keywords(user):
    out = {}
    for e in user["edge_owner_to_timeline_media"]["edges"]:
        n = e["node"]
        caps = n["edge_media_to_caption"]["edges"]
        cap = caps[0]["node"]["text"] if caps else ""
        ts = datetime.fromtimestamp(n["taken_at_timestamp"], timezone.utc)
        views = n.get("video_view_count") or n.get("video_play_count") or 0
        cmts = n["edge_media_to_comment"]["count"]
        for m in re.findall(r'\bComment\s+["“]?([A-Za-z][A-Za-z0-9_]{1,20})\b',
                            cap, re.I):
            kw = m.upper()
            if kw in STOP:
                continue
            out.setdefault(kw, []).append((ts, views, cmts))
    return out


def render(found):
    lines = []
    for kw in sorted(found, key=lambda k: min(t for t, _, _ in found[k])):
        hits = sorted(found[kw])
        if len(hits) == 1:
            ts, v, c = hits[0]
            note = f"LIVE {ts:%Y-%m-%d}, {v:,}v/{c:,}c"
        else:
            note = (f"LIVE x{len(hits)}: "
                    + ", ".join(f"{t:%Y-%m-%d} ({v:,}v/{c:,}c)" for t, v, c in hits))
        lines.append(f"{kw:<9} # {note}")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    if not LEDGER.exists():
        sys.exit(f"FATAL: no ledger at {LEDGER}")

    user = fetch()
    found = live_keywords(user)
    if not found:
        # Never silently blank the section. An empty parse means the endpoint
        # changed shape, and rewriting would DELETE real burned words.
        sys.exit("FATAL: parsed 0 keywords from the live feed. Refusing to write.")

    old = LEDGER.read_text(encoding="utf-8").splitlines()
    try:
        i = next(k for k, l in enumerate(old) if l.startswith(BEGIN))
        j = next(k for k, l in enumerate(old) if l.startswith(NEXT_SECTION))
    except StopIteration:
        sys.exit(f"FATAL: could not find section markers in {LEDGER}")

    # keep the section's own comment block, replace only the keyword lines
    head_end = i
    while head_end < j and (old[head_end].startswith("#") or not old[head_end].strip()):
        head_end += 1

    # Split the section into keyword lines and everything else. The "everything
    # else" is prose that explains the section's limits, and an earlier version
    # of this splice silently deleted it along with a separator rule. Comments
    # in a guard file are the part a human actually reads, so they are preserved
    # verbatim and re-emitted after the keywords.
    seg = old[head_end:j]
    is_kw = lambda l: bool(l.strip()) and not l.lstrip().startswith("#")
    tail = [l for l in seg if not is_kw(l)]
    existing = {l.split()[0] for l in seg if is_kw(l)}
    new_lines = render(found)
    added = sorted(set(found) - existing)
    dropped = sorted(existing - set(found))

    print(f"followers {user['edge_followed_by']['count']:,}  "
          f"posts {user['edge_owner_to_timeline_media']['count']}  "
          f"visible {len(user['edge_owner_to_timeline_media']['edges'])}")
    print(f"live keywords parsed: {len(found)}")
    for k in added:
        print(f"  + {k}")
    for k in dropped:
        # only reachable if a post was deleted or fell out of the visible 12
        print(f"  ! {k} no longer visible in the last 12 posts. KEPT, "
              f"because falling out of the window does not un-burn a word.")

    keep = [l for l in seg if is_kw(l) and l.split()[0] in dropped]
    out = old[:head_end] + new_lines + keep + tail + old[j:]

    if not a.write:
        print("\ndry run. pass --write to apply.")
        return
    LEDGER.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"\nwrote {LEDGER}")


if __name__ == "__main__":
    main()
