# Changelog

## 1.1.0 (2026-10-13)

From a full faceless test build on Linux and a platform review.

### Fixed
- `lint.sh` failed under bash everywhere but Windows: the bundle had CRLF line
  endings. Now LF, pinned by `.gitattributes`; the ledger check also tolerates
  a hand-added CRLF line, so lint and Python can no longer disagree.
- YouTube reference pulls: `pull_reference.py` now passes `--js-runtimes node`
  (yt-dlp enables only Deno by default).
- Shots cut early on AI-voice reels: anchors are searched after the previous
  cut, must be unambiguous, and `voice.py` picks openings said only once.
  Applies to `pace.py` too.
- B-roll shorter than its shot looped on screen; it now holds its last frame
  and `final.py` says what `--seconds` to re-render at.
- `verify.py` now reads `forbid` and `max_seconds` from reel.json.
- `newreel.py` no longer ships an empty plate that drew a dark box.
- `addmusic.py`: no default commercial track, `which` replaced (Windows), and
  the mixed audio is re-mastered to -14 LUFS.

### Added
- `verify.py` fails a reel silent at 0.1s, and `trim.py` starts every reel at
  the measured voice onset.
- Topic gate middle band (40 to 54): test as a Trial Reel first. Its verdicts
  are computed from its own benchmark table.
- Hook patterns 21 to 23, taken from the account's winners.
- Meta's one-DM-per-comment rule in the posting step; 3 minute length note.
- `REEL_HANDLE`, `REEL_ACCOUNT`; Linux font fallback to Liberation and DejaVu.

### Changed
- Beat 3 describes what `final.py` really does (a floating presenter window).
  `matte.py`, torch and torchvision are optional; doctor no longer fails on them.
- `breathe.py`, `pace.py` and `addmusic.py` are documented.

## 1.0.0 (2026-10-13)

Renamed from `Reel_direction` to **Reel Boss** (`reel-boss`).

### Added
- **Local AI voice** (`voice.py`): no phone take, no paid service. Kokoro v1.0
  reads the six line script on the CPU, writes a normal `take.mp4`, makes the
  reel faceless and anchors one shot per block of lines.
- **3D b-roll** (`renderers/scene3d.py`): price bars and `.glb` turntables via
  vendored three.js, rendered frame by frame so rebuilds are frame identical.
- **Eased motion** (`lib/ease.py`): plates fade and rise in, the spoken caption
  word pops, counters and fills ease instead of stepping.
- **Preflight** (`scripts/doctor.py`): every package, binary, font, model and
  asset, with the exact fix, before a keyword is burned.
- `lint.sh --allow-free` for a deliberate "free".
- Windows, macOS and Linux support, with per machine paths as env vars.

### Fixed
- The end of a reel was silently cut when the take's video outlasted its voice;
  `verify.py` now fails any video/audio length mismatch.
- Lip sync drifted a frame per trim cut.
- `verify.py` now fails a reel with no voice (guide tracks, music-only drafts).
- Captions took Whisper's spelling ("DakuSign"); they now take the script's.
- `final.py` crashed on Windows ffmpeg (no glob) and on a fresh `newreel.py`
  project (missing `presenter_track`).
- A duplicate slug burned a CTA keyword; the linter and the pipeline could read
  different keyword ledgers; the "free" check missed `free.` and `FREE!`.
- Console encoding crashes on Windows; bare `/tmp`, Mac font and `whisper-cli`
  paths; yt-dlp and gallery-dl not found when pip's Scripts dir is off PATH.

### Changed
- SKILL.md is about a third shorter; traps, setup and history moved to
  `references/traps-and-setup.md`. No rule was dropped.

## 0.1.0 (2026-08-22)

First bundle, as `Reel_direction`, macOS only.
