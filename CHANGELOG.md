# Changelog

## 2.0.0 (2026-10-13)

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

## 1.0.0 (2026-08-22)

First bundle, macOS only.
