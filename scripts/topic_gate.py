#!/usr/bin/env python3
"""Score a candidate reel topic BEFORE anything is shot or built.

Calibrated on the 12 most recent @billy.coder posts, measured live 2026-08-22.
Across those posts the comment/view rate is flat at 2.16% mean, while views
range 89 to 89,480. Conversion is solved. Reach is not. Every question below
is a variable that separated the posts that were served from the posts that
were not.

n = 12. These weights are judgment calibrated on a small sample, not a fit.
Re-derive them when the account has more data.

Usage
  python3 topic_gate.py                       interactive
  python3 topic_gate.py --angry --object --institution --stake --caption "..."
  python3 topic_gate.py --json '{"angry":1,"object":1}'
"""
import argparse, json, sys

# (key, weight, question, what a yes looks like)
CRITERIA = [
    ("angry", 30,
     "Is there a named party who would be angry this exists?",
     "Flock, a vendor, an agency, a company with a price list. Not 'developers'."),
    ("object", 25,
     "Is there a physical object a camera can point at?",
     "A camera on a pole, a radar dish, a scanner, a rover. Not a terminal."),
    ("institution", 12,
     "Is the named party one a stranger already recognises?",
     "NASA, Meta, DocuSign. If they have to be told who it is, no."),
    ("stake", 12,
     "Does it happen to the viewer personally, not to their codebase?",
     "Their job application, their plate scanned, their DMs. Highest converting axis on the account."),
    ("destruction", 8,
     "Is there a thing that visibly breaks, bursts, burns or gets caught?",
     "Both winners open on something being destroyed or exposed."),
    ("price", 8,
     "Is there a named recurring price the viewer already pays?",
     "$50 a month, $20 a month. Said out loud in the first five seconds."),
    ("sendable", 5,
     "Would a viewer send this to one specific person they know?",
     "DM sends are the strongest ranking signal. Name that person in the hook."),
]

PASS_MARK = 55

BENCHMARKS = [
    (89480, "Flock, angry party + camera on a pole that bursts",
     ["angry", "object", "institution", "destruction", "sendable"]),
    (68591, "leaked military grade radar, hardware + forbidden framing",
     ["angry", "object", "destruction", "sendable"]),
    (6683, "NASA gave away the Mars rover plans",
     ["object", "institution", "sendable"]),
    (1045, "Meta charges per message, named company, nothing to film",
     ["angry", "institution", "price"]),
    (136, "69 job applications written by a bot, 16.91% comment rate",
     ["stake", "sendable"]),
    (89, "your DMs are a password manager, no name and no object",
     ["stake"]),
]


def score(ans):
    got = sum(w for k, w, _, _ in CRITERIA if ans.get(k))
    return got


def bench_score(keys):
    return sum(w for k, w, _, _ in CRITERIA if k in keys)


def main():
    # Windows pipes default to cp1252, which dies on an emoji in --caption
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(add_help=True)
    for k, _, q, _ in CRITERIA:
        p.add_argument("--" + k, action="store_true", help=q)
    p.add_argument("--json", dest="js", help="answers as a JSON object")
    p.add_argument("--caption", default="", help="the working hook or caption")
    a = p.parse_args()

    ans = {k: getattr(a, k) for k, _, _, _ in CRITERIA}
    if a.js:
        try:
            ans.update({k: bool(v) for k, v in json.loads(a.js).items()})
        except (ValueError, AttributeError):
            p.error("--json needs an object, e.g. '{\"angry\":1,\"object\":1}'")
    interactive = not a.js and not any(ans.values())

    if interactive:
        print("Topic gate. Answer y or n. Be strict, a maybe is a no.\n")
        for k, w, q, hint in CRITERIA:
            print(f"  {q}")
            print(f"    ({hint})")
            ans[k] = input("  y/n > ").strip().lower().startswith("y")
            print()

    s = score(ans)
    print("=" * 62)
    for k, w, q, _ in CRITERIA:
        mark = "yes" if ans.get(k) else " no"
        print(f"  [{mark}] {w:>2}  {q}")
    print("=" * 62)
    print(f"  SCORE {s} / 100        pass mark {PASS_MARK}")
    print()
    print("  where the account's own posts land on this same scale:")
    for v, label, keys in BENCHMARKS:
        b = bench_score(keys)
        here = "   <-- yours is near here" if abs(b - s) <= 6 else ""
        print(f"    {b:>3}  {v:>6} views   {label}{here}")
    print()

    if s >= PASS_MARK:
        print("  VERDICT: shoot it.")
        print("  Open on the object. Sound at frame 0. Name the angry party in line 1.")
    else:
        missing = [q for k, w, q, _ in CRITERIA if not ans.get(k) and w >= 12]
        print("  VERDICT: do not build this yet.")
        print("  4 of the 5 posts scoring under the mark got under 2,300 views, and the craft was not why.")
        if missing:
            print("  Closest thing to a fix, find an angle that makes one of these a yes:")
            for m in missing:
                print(f"    - {m}")
    if a.caption:
        print(f'\n  hook under test: "{a.caption}"')
        print("  now run: bash scripts/lint.sh \"<hook>\"")
    return 0 if s >= PASS_MARK else 1


if __name__ == "__main__":
    sys.exit(main())
