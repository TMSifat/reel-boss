# reel-system

Windows: use `python` for `python3`; setup and env vars are in
`references/traps-and-setup.md`. Hook patterns live in `references/hook-sheet.md`.

The pipeline from HOW-WE-MAKE-A-REEL.md, built and verified on this machine.

Everything here is free and runs locally. No paid API, no subscription, no stock
library.

## Verified working on this machine

| Piece | Version | Proof |
|---|---|---|
| Python | 3.14.3 | `python3 -V` |
| ffmpeg / ffprobe | 8.1 | `ffmpeg -version` |
| faster-whisper | 1.2.1, `small.en` | transcribed the smoke take, 47 words |
| torch / torchvision | 2.13.0 / 0.28.0 | DeepLabV3 MobileNetV3 forward pass |
| Playwright | 1.62.0, chromium 151.0.7922.34 | recorded `proof.html` |
| yt-dlp | 2026.07.04 | pulled live view/like/comment counts with `--js-runtimes node` |
| yt-dlp-ejs | 0.8.0 | the YouTube 403 fix |
| Pillow | 12.1.1 | every graphic and every caption frame |
| numpy | 2.4.3 | matte and frame buffers |
| imageio-ffmpeg | 0.6.0 | ffmpeg fallback if brew's disappears |

Apple Color Emoji only accepts these strike sizes here: 20, 26, 32, 40, 48, 52,
64, 96, 160. Anything else raises `invalid pixel size`. `theme.py` bakes at 160
and resamples down, which is why the emoji are PNGs in `assets/emoji/` and why a
missing one throws instead of falling back.

## Layout

```
reel-system/
  config.py            frame spec, audio targets, safe zones, palettes, banned text
  keywords_burned.txt  every CTA keyword ever used, append only, never reused
  newreel.py           stage 0, opens a reel and claims the keyword
  voice.py             stage 0b, no phone take: local AI voice -> take.mp4, faceless
  stt.py               stage 1, word level transcript, captions in the script's spelling
  trim.py              stage 2, cut pauses, speed up, retime the words
  matte.py             stage 3, cut the presenter out of the background
  theme.py             stage 4, banner, progress, plates, captions, emoji
  renderers/
    screenrec.py       b-roll A, real screens via Playwright, with the mask
    graphic.py         b-roll B, animated graphics via Pillow
    seatcost.py        b-roll C, the per seat bill that counts up then drops to zero
    plate.py           b-roll D, typographic statement rows
    scene3d.py         b-roll E, 3D via three.js: price bars, or a .glb turntable
  final.py             stage 5, composite, master, deliver
  verify.py            stage 6, check the DELIVERED file, not the log
  lib/util.py          loudness, silence, seeded shuffle, text lint, keyword ledger
  lib/ease.py          easing curves every renderer and the compositor share
  assets/three/        vendored three.js 0.170.0 (MIT) and the 3D scene page
  projects/<slug>/     one folder per reel
```

Delivered files land in `~/Documents/Notes/video-assets/` (override with `REEL_DELIVERY`) as `<slug>.mp4` and
`<slug>_SB.jpg`.

## Run it

```bash
cd reel-system   # inside the skill folder

# 0. open the reel. This burns the CTA keyword before anything else exists.
python3 newreel.py my-slug --palette security --cta VET \
  --banner "one in four had a hole" --handle "@billy.coder" --forbid toolname

# drop the phone take in as projects/my-slug/take.mp4, fill in reel.json

# no phone take? read the six lines with the local voice instead
# python3 voice.py projects/my-slug --voice am_michael

# 1..2  transcript, then cut every pause and speed up slightly
python3 stt.py  projects/my-slug/take.mp4
python3 trim.py projects/my-slug/take.mp4 --speed 1.06

# 3  cut the presenter out
python3 matte.py projects/my-slug/take_trim.mp4

# 4  b-roll. Real screen first, graphic second.
python3 renderers/screenrec.py "https://the-project-site" \
  projects/my-slug/broll_1.mp4 --seconds 6 --blur ".repo-name" "header .url"
python3 renderers/graphic.py projects/my-slug/broll_2.mp4 --seconds 6 --palette security
# 3D: the paid thing towers, the open one sits at zero. Values are published figures.
python3 renderers/scene3d.py projects/my-slug/broll_3.mp4 bars --palette security \
  --bar "DocuSign|50" --bar "This one|0" --prefix '$' --suffix ' a month'
# 3D: turntable of the project's own model export
python3 renderers/scene3d.py projects/my-slug/broll_4.mp4 model --glb rover.glb --palette hardware

# 5  build and deliver
python3 final.py projects/my-slug

# 6  check the file that actually shipped
python3 verify.py ~/Documents/Notes/video-assets/my-slug.mp4   # or $REEL_DELIVERY \
  --project projects/my-slug --forbid toolname reponame
```

## What each guard is protecting

Every one of these is a lesson that cost a post, wired in so it cannot be
skipped by remembering.

**The cut is derived from speech, never typed.** `derive_spans()` splits the
runtime at the biggest pauses between words, computed from `words_trim.json`.
Plates anchor with `on_phrase`, so changing the pacing re-times the whole edit
instead of sliding a graphic off the word it was cut to.

**The trim is the union of two measurements.** Whisper word boundaries are loose
by up to 0.2s, so `trim.py` intersects the transcript gaps with `silencedetect`
on the waveform and only cuts where both agree.

**Audio cannot silently vanish.** The video track is built with no audio stream
in it at all, the voice is mastered on its own, and they are muxed at the end
with `-c:v copy`. `final.py` asserts the video track is silent before muxing.
The one `filter_complex` left in the pipeline is video only, by construction.

**Loudness is a measured number, not a hope.** `master()` measures, applies the
exact gain, measures again off the output, and raises if it is more than 1 LUFS
off `-14.0` or hotter than `-1.0 dBTP`. The smoke reel delivered at -14.01 LUFS,
-1.98 dBTP.

**The gate holds.** `screenrec.py` installs the blur as an init script so it is
live on the first painted frame, then asserts the selector matched something and
that the computed style really contains a blur. A selector typo raises. The
first build of the smoke reel had the repo name readable on frame 4 because the
blur was applied after `goto()`, and the contact sheet is what caught it.

**The furniture cannot cover the evidence.** The banner owns `BANNER_ZONE` and
nothing else. The sharp b-roll is confined to the content band underneath it,
with the same footage blurred and darkened behind, so the frame is still full
bleed and no second is a dead plate. The first build had the banner sitting on
top of the proof screen's headline numbers.

**Missing assets throw.** `need()` raises. `bake_emoji()` raises if the glyph
renders nothing. No silent fallback to a system font.

**Keywords cannot repeat.** `keywords_burned.txt` is append only and
`claim_keyword()` refuses a repeat, because the automation routes on the word
and it was said on camera.

**Video and audio end together.** The container length is the longest stream.
A take whose video ran past the voice used to keep a silent tail through trim,
then lose the reel's last two seconds to `-shortest` at the mux, with the
progress bar stopping at 83%. `trim.py` now measures the audio stream, and
`verify.py` fails any delivery where video and audio differ by over 0.15s.

**No reel ships without a voice.** `verify.py` fails any delivery under one
spoken word a second, which is what a guide track or a music-only animatic
measures. When there is no phone take, `voice.py` reads the script with
Kokoro v1.0 on the CPU; its model files are SHA-256 pinned. A synthetic read
pauses evenly, so it writes `shot_anchors` at line starts instead of leaving
`derive_spans()` to split at pauses that do not exist (one shot once took 12s
of 16s and looped).

**Captions spell what the script spells.** `stt.py` aligns Whisper's words to
reel.json's script and keeps the script's spelling wherever a heard word is a
close match: "DakuSign" becomes DocuSign, "kazook" becomes the keyword.

**The keyword is burned last.** `newreel.py` refuses an existing slug before it
touches the ledger, so a typo'd rerun cannot waste a keyword.

**3D is rendered, not recorded.** `scene3d.py` has no animation loop: each frame
is `renderAt(t)` and a screenshot, so a rebuild is frame identical (checked by
framemd5) and the beats are fractions of the shot like every other renderer.
three.js is vendored, so a render never depends on a CDN. Labels go through
`lint_text`, and a missing `.glb` or a WebGL failure raises instead of
rendering an empty shot.

**Motion is eased, never linear.** `lib/ease.py` holds the only curves:
`out_cubic` for arrivals, `in_out_cubic` for fills, counters and camera moves,
`out_back` for pops. Plates fade and rise in over 0.28s and fade out over
0.16s. The spoken caption word pops to about 114% and settles; turn it off
per reel with `"caption_pop": false` in reel.json.

**Randomness is seeded.** `shuffled(seq, seed)` looks random and is identical
between rebuilds. Never `(i * 97 + 13) % N`, which draws visible diagonal
stripes.

**Dashes and the word free are linted.** `lint_text()` raises on em dash, en
dash, horizontal bar, minus sign and double hyphen anywhere, and on the word
free in a hook or title.

## The smoke reel

`projects/pipeline-smoke/` is a real end to end run kept as a reference. Its
presenter take is looped footage out of `go-viral-routines.mp4`, because there
is no phone take on this machine yet, so the cutout reads as a dark silhouette
and carries burned in text from the original reel. That is the fixture, not the
pipeline. The matte itself measured 31.6% mean person coverage across 414
frames, so the segmentation is doing real work.

Delivered: 13.60s, 1080x1920, 30fps, -14.01 LUFS, -1.98 dBTP, delivered audio
100% match against the script.
