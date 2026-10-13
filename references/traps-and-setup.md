# Traps, setup, and the corrections history

Moved out of SKILL.md to keep it short. Nothing here is optional reading when
something breaks.

## The traps, ranked by what they cost

1. **Silently losing audio in ffmpeg.** Two independent chains in one
   `filter_complex` dropped 3.2 seconds of voice and nothing errored. Prefer
   `-vf` and `-af`, and always transcribe the delivered file.
2. **Trusting the log over the file.** Ships mistakes to an audience.
3. **Silent asset fallbacks.** Make missing assets throw.
4. **Overlays that hide the evidence.** A banner covering the install command is
   worse than no banner. Give furniture a fixed zone, lay content underneath.
5. **Pulling b-roll from the competitor's reel.** Check the project's own site
   or repo first. Higher quality, and not somebody else's frame. Since April
   2026 Instagram reportedly flags reposts that share most of another
   creator's visuals or audio, which is also why `addmusic.py` has no default
   track: use one you hold the rights to.
6. **Fake randomness.** `(i * 97 + 13) % N` drew visible diagonal stripes. Use a
   seeded shuffle: random-looking, identical between rebuilds.

## Toolchain

Python 3 with `Pillow`, `numpy`, `imageio-ffmpeg`; `faster-whisper` (`small.en`,
CPU) for word level transcription, used by both `stt.py` and
`decode_reference.py`; `kokoro-onnx` and `soundfile` for the local voice
(`python reel-system/voice.py --download` fetches the model once); `torch` and `torchvision` for the person matte;
`Playwright` (plus `python -m playwright install chromium`) for screen
recordings and 3D (three.js 0.170.0 is vendored in `reel-system/assets/three`); `yt-dlp`, `yt-dlp-ejs` and `gallery-dl` for reference pulls; full
`ffmpeg` including `ffprobe`; Airtable free tier for the idea bank; a DM
automation tool for the keyword. All free, all local.

`python scripts/doctor.py` checks every one of these and prints the install
command for anything missing.

`yt-dlp` on YouTube needs a JS runtime. On a 403 across every format, install
`yt-dlp-ejs` and pass `--js-runtimes node`.

## Sandboxed and cloud sessions

- `stt.py` downloads Whisper `small.en` from Hugging Face on first use, and
  `voice.py` downloads Kokoro from GitHub. Where those hosts are blocked, fetch
  the models once on a machine that can and copy the caches across
  (`~/.cache/huggingface`, `~/.cache/reel-boss/kokoro`).
- Linux fonts fall back from Microsoft core fonts to Liberation Sans (same
  metrics as Arial) to DejaVu. `doctor.py` shows which one resolved.
- Verified on ffmpeg 6.1 and 8.x.

## Windows

- Use `python` where the docs say `python3`. Run `scripts/lint.sh` from Git Bash
  (ships with Git for Windows) or WSL.
- ffmpeg: `winget install Gyan.FFmpeg`, or unzip a build from gyan.dev or
  github.com/BtbN/FFmpeg-Builds and add its `bin` to PATH. `imageio-ffmpeg`
  alone is not enough: it ships `ffmpeg` but never `ffprobe`.
- Fonts resolve to Arial Black, Arial and Consolas in `C:\Windows\Fonts`.
- The baked emoji PNGs in `reel-system/assets/emoji/` work as is. Baking a *new*
  one needs the Apple Color Emoji font, so bake on a Mac and copy the PNG in.
- Git Bash rewrites any argument that starts with `/` into a Windows path, so
  `--suffix "/mo"` arrives as `C:/Program Files/Git/mo`. Write `" a month"`,
  or run with `MSYS_NO_PATHCONV=1`, or use PowerShell.
- yt-dlp cannot read Chrome's cookies on Windows (app-bound encryption). Log in
  once in Firefox and set `REEL_COOKIE_BROWSER=firefox`.

Per-machine paths are environment variables, never edits: `REEL_DELIVERY`,
`REEL_COOKIE_BROWSER`, `REEL_FONT_BOLD`, `REEL_FONT_REG`, `REEL_FONT_MONO`,
`REEL_APPLE_EMOJI`, `REEL_MUSIC`, `REEL_BURNED_KEYWORDS`.

## Corrections history

Kept so nobody re-learns these.

- **2026-08-22, the repo rule.** It was written as "never show the repo" and was
  over-broad. The 68k reel shows the GitHub page in full (`23.5k stars`,
  `5.4k forks`, the Star button, the project's own architecture diagram) and
  scrolls only the `owner/repo` header off the top of frame. Verified by
  cropping the full resolution frame. Hiding the proof too cost the payoff beat.
- **2026-08-22, "the metric is comments, not views".** Wrong. Across the last 12
  posts the comment rate is flat at 2.16% mean and does not move with quality:
  the 89,480 view post converted at 2.18%, the 89 view post at 4.49%. Comments
  are a near-linear function of views, so maximising comments and maximising
  reach are the same job, and the job is the topic.
- **2026-08-22, cut count.** An earlier note claimed the hits had zero cuts. That
  came from `ffmpeg -v error` silently suppressing `showinfo` output. Measured
  properly at threshold 0.25: 9 cuts in 54.29s and 4 in 13.56s. BC-020 cut less
  often than either.
- **View counts drift.** The 68k reel reads 68,591, 68,595 and 68,609 in
  different files because it was measured on different days. Not an error.
