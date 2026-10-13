---
name: reel-boss
description: The creative direction system behind @billy.coder reels - topic gate, the four beats, the rules that never move, the six line script, the recording pack, the local Python edit pipeline, delivery verification, and the caption/CTA funnel. Use whenever the user is making, planning, scripting, editing, checking, captioning or posting a short vertical reel, picking a reel topic or hook, or asks how a reel should be directed. Triggers on "Reel Boss", "reel-boss", "/reel-boss", "reel-direction", "Reel_direction", "direct this reel", "make a reel", "reel rules", "hook for this reel", "check this reel before posting", "write the caption", "pick a topic for the next reel".
---

# Reel Boss

The operating system behind @billy.coder. Not a style guide, a funnel.
Everything here is free and local. Paths below are relative to this skill's
folder. On Windows use `python` for `python3` and Git Bash for `.sh`.

The account went 79 to 669 followers on one reel built this way. What did it was
**the topic and the shape**, not the polish.

**The product is a comment, not a view.** The comment triggers the DM that
delivers the promised thing, and that DM is where the audience gets built. And
that half already works: measured 2026-08-22 across the last 12 posts, comment
rate is flat at **2.16%** while views range **89 to 89,480**, and two posts hold
92.8% of all views. **Reach is the only variable, and topic is the only lever on
reach.** Evidence: [what-actually-moves-reach.md](references/what-actually-moves-reach.md).

---

## Spec

| | |
|---|---|
| Length | 15 to 20 seconds by habit. **Not a law.** The two hits are 54.17s and 13.44s, and non-followers are still recommended reels up to 3 minutes. Never cut a real-world beat to hit 20. The pipeline caps at 20 by default; raise it per reel with `spec.max_seconds` in reel.json and `verify.py --max-seconds`. |
| Frame | 1080 x 1920, 30fps, vertical, full bleed |
| Audio | 48 kHz stereo, -14 LUFS integrated, true peak under -1 dBTP |
| Voice | one person, phone camera, chest up, straight to camera. No take? The local AI voice (`voice.py`) reads the script over full-frame b-roll. **Never deliver a reel without a voice**: no guide tracks, no music-only animatics |
| On screen | real footage or a live graphic at all times, plus burned captions |
| Ending | one uppercase word, and a promise to send something if they comment it |

## The four beats

1. **A named paid thing loses.** "DocuSign is $50 a month." A price the viewer
   recognises, out loud, in the first five seconds.
2. **Proof on a real screen.** Actual footage of the thing working. Not a
   mockup, not a slide. This is the like-vs-comment line.
3. **The presenter and the evidence share the frame.** `final.py` shows the
   take as a floating window (rounded, rimmed, shadowed) that pops between
   corners over the proof; the full-frame hook comes first. No take: the reel
   goes faceless and the b-roll carries every frame.
4. **One word.** "Comment VET and I will send you the setup."

A reel that is not landing is almost always missing beat 1 or beat 2.

## The rules that never move

Each one is a lesson that cost a post. Do not relax them to make a task easier.

- **Never show the repo NAME.** Not in audio, on screen, in a URL, or in a
  terminal prompt. This is the whole business. Show the proof (stars, forks,
  the page, the diagram) and scroll or blur only the `owner/repo` header.
  Hiding the proof too is what cost the payoff beat.
- **The word "free", and naming GitHub: both hits break this rule.** Both say
  "free on GitHub" out loud, and the 68k reel burns "free" on screen. n = 2, so
  it is a documented contradiction, not a licence. Saying the licence is still
  the stronger, checkable claim. **Decide it deliberately, do not drift into
  it**: the linter blocks it unless you pass `--allow-free`.
- **No em dashes, en dashes or double hyphens in anything published.** Biggest
  AI tell, and this audience spots it.
- **One unique CTA keyword per post, never reused.** The automation routes on
  it. Burned list: `reel-system/keywords_burned.txt`, append only.
- **Free and local, every stage.** Never send the user to a paid or
  credit-based service (Higgsfield, ElevenLabs, CapCut Pro) for voice, video
  or graphics. `voice.py`, the renderers and the pipeline cover all of it.
- **Never invent a number.** Use the repo's own published figures and verify
  them the day you shoot. One fabricated stat and the account pays for it.
- **Change the colour theme between reels.** Pick the palette from the subject.
  A security reel runs red and amber, not the house lime.
- **Avoid orange, and purple on dark.** Both read as default AI tool palette.
- **Apple emoji only**, as real PNGs, and a missing one must throw, never fall
  back to a system font. The wrong emoji shipped once on a silent fallback.
- **No dead frames.** Under 20 seconds, a static plate is a wasted second.
- **Cut count is not a signal.** The hits run 9 cuts in 54s and 4 in 13s. Do not
  design to it.
- **Sound and motion on frame 0.** Both hits are at -17 dBFS at 0.1s and open on
  something physical moving. The 89 view reel was at **-64.6 dBFS** on a blurred
  laptop. Silence at 0.1s is the loudest predictor of a dead post.
- **One declarative banner, from frame 0, never changing.** Both hits do this for
  their entire runtime. One has a typo in it and still did 89,480.

## Workflow

Run these in order. Skipping a stage is how the known failures happen.

**1. Topic. Gate it before anything else exists.**

```bash
python scripts/topic_gate.py
```

55 or more: **shoot it**. 40 to 54: **test it first** as a Trial Reel, which
shows it to non-followers only (accounts with 1,000+ followers have them); the
NASA reel, the account's third best at 6,683 views, scores 42. Under 40: **do
not shoot it**. The gate is really asking: **is
there a named party who would be angry this exists, and is there a physical
object a camera can point at?** Those two carry 55 of the 100 points because
they are what separated 89,480 from 89.

Qualifies: an open source thing that replaces something people pay for, and is
provable on a screen. If there is nothing to film, there is no reel. Does not:
explainers, listicles, news with no CTA, anything with no named price and no
licence. Dedupe against the Airtable idea bank first. Take the idea from what
already works in the lane, never the wording. Watch comment rate only as an
alarm: a post far under 2% means the ask or the keyword broke.

**2. Decode the reference. Pull it and measure it, do not watch it.**

```bash
python reel-system/pull_reference.py "<any url>"
```

YouTube, Instagram, TikTok, X and Facebook, off a logged-in browser's cookies
(`REEL_COOKIE_BROWSER`, default chrome; firefox on Windows). Fetches the media
and public engagement numbers, then runs `decode_reference.py`: runtime, frame 0
dBFS, LUFS, true peak, cut timestamps, sampled palette, content bands, and a
transcript with words per second.

Then write down: first two seconds, where the hook sits, what is on screen at
every beat, palette, shot lengths, where the CTA lands, what the caption does.
Then write out **what you are taking and what you are not**. Take structure and
pacing. Never take palette, wording, badges, or anything that identifies the
source.

**3. Script. Six lines, read briskly, no pauses.**
- Line 1 comes off [hook-sheet.md](references/hook-sheet.md), never invented
  fresh. Offer three options, each a different pattern, and name the pattern.
  Start from 21 to 23: they are the account's own winners, the 20 generic
  patterns above them never produced a hit here.
- Lines 2 and 3 carry the numbers, and the numbers must become the viewer's
  problem: state the scale, then make it personal. "Somebody checked forty two
  thousand of them. One in four had a hole in it. **You install these with one
  click.**"
- Line 6 is the CTA. One word, uppercase, never used before:
  `bash scripts/lint.sh --cta WORD`.
- Write pronunciations in ("NVIDIA" as *en VID ee uh*). Saves a reshoot.
- Mark which lines slow down and which speed through.

**4. Record.** Ten minutes of phone footage, vertical, chest up, good light.
Come back with **choices, not one version**: three full straight-through takes
of the six lines; the hook said three ways from three patterns; the CTA line on
its own in case the keyword has to change. Watch the top of frame, a cropped
head is unfixable.

**No phone take? Do not stop and do not deliver a silent draft.** Fill the
six lines into reel.json, then:

```bash
python reel-system/voice.py reel-system/projects/<slug>        # am_michael by default
python reel-system/voice.py --list                             # 28 English voices
```

It reads the script with Kokoro (local, Apache 2.0, ~350 MB one-time
download), writes `take.mp4`, makes the reel faceless and anchors one shot per
block of lines. Then carry on at `stt.py` exactly as with a phone take.
Captions take the script's spelling, so "DocuSign" never shows up as
"DakuSign". Tell the user it is a synthetic voice, offer to swap in their
own take, and switch on Instagram's AI label when posting (it marks the
content; it does not change the account's standing).

**5. Edit.** Two options.
*No code:* CapCut, cut every gap, bold high contrast overlays out of the danger
zones, auto captions, export 1080p. Genuinely fine.
*The real one:* the local Python pipeline in `reel-system/`. Optional stages:
`breathe.py` + `pace.py` give the read a rhythm (capped pauses, per line
speeds) instead of trim's cut-every-pause; `addmusic.py` lays a ducked bed
under the voice, from a track you hold the rights to, and re-masters. Run
`python scripts/doctor.py` first: it fails before a keyword is burned, not
after. Stages and commands: [pipeline.md](references/pipeline.md).
B-roll kit, real screen first: `screenrec.py` (a real page), `graphic.py`,
`seatcost.py`, `plate.py`, and `scene3d.py` for 3D (`bars`: the paid price
towers over the open one at zero; `model`: a turntable of the project's own
`.glb`). All motion is eased, plates fade in, the spoken caption word pops.
3D is graphic b-roll, so beat 2 still needs a real screen or real footage.
Three things worth stealing even in a different build:
1. **Derive the cut from the transcript, never type timecodes.** A pacing
   change then re-times the whole edit.
2. **Trim against measured silence too.** Whisper word boundaries are loose by
   up to 0.2s. Cut where the transcript and `silencedetect` both agree.
3. **Master to a number.** Measure, apply exact gain, measure again.

**6. Deliver and check.** Two files per reel: `NAME.mp4` and a 16 frame contact
sheet `NAME_SB.jpg`. **Check the delivered file, not the build log** (`verify.py`
does: it fails a reel under one spoken word a second, one silent at 0.1s, a
video/audio length mismatch, and a spoken gate word from reel.json's `forbid`). Pull frames out of the shipped mp4, look at them, transcribe the
delivered audio. The contact sheet answers one question: **does anything
overlap anything else?** Banner over caption, caption over presenter, presenter
over the one graphic that matters.

**7. Post.** Caption shape, every time:
1. Hook line: the named paid product, or the claim
2. What it does, in specifics: stars, licence, price, hardware cost
3. The licence line. MIT, Apache, OSHWA, public domain
4. `Comment X and I'll send it.`
5. A few niche hashtags

Lint every caption, title, plate and CTA before it goes out:

```bash
bash scripts/lint.sh "your caption or hook text"
bash scripts/lint.sh --allow-free "caption you decided may say free"
```

It fails on em dash, en dash, horizontal bar, minus sign, double hyphen, the
word "free" (WARN with `--allow-free`), and a burned CTA keyword.

Wire the keyword into the DM automation **before** the post goes up; the word
was said on camera and cannot change. Meta allows one automated DM per
comment, within 7 days, and it does not open the 24 hour messaging window, so
**that one DM must carry the deliverable itself**, never a "follow me first"
step. Posting through an API to more than one
account: always target by account ID, never the default.

## If you only take three things

1. **The topic beats the craft, and it is not close.** The nine best-made posts
   average **610 views**. The two roughest average **79,035**. Gate the topic.
2. **Show the thing working on a real screen.** Proof is the like-vs-comment
   line, and comments are the only thing that compounds.
3. **Protect the gate.** Never name the tool. The system runs on people having
   to ask.

## Files

- [references/traps-and-setup.md](references/traps-and-setup.md) - the six
  traps that cost posts, toolchain, Windows setup, env vars, corrections history
- [references/what-actually-moves-reach.md](references/what-actually-moves-reach.md)
  - measured evidence for every claim above. Re-measure before trusting it
- [references/hook-sheet.md](references/hook-sheet.md) - 23 hook patterns, 3 of
  them the account's own winners
- [references/pipeline.md](references/pipeline.md) - build stages, commands,
  and what each guard protects
- [references/how-we-make-a-reel.md](references/how-we-make-a-reel.md) - the
  original source document
- [scripts/topic_gate.py](scripts/topic_gate.py) - score a topic before it is shot
- [scripts/lint.sh](scripts/lint.sh) - publish text and CTA keyword linter
- [scripts/doctor.py](scripts/doctor.py) - preflight for the pipeline
- `reel-system/` - the pipeline itself; `pull_reference.py` measures any reel by
  URL; `voice.py` reads the script with a local AI voice

Other skills (`Viral-Video-Maker`, `hook-engine`, `post-content`) can run under
this direction if installed. None are required.
