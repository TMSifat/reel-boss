"""Global constants for the reel pipeline.

Frame spec and audio targets come straight from HOW-WE-MAKE-A-REEL.md and do not
change per reel. The palette does change per reel, on purpose.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECTS = ROOT / "projects"
ASSETS = ROOT / "assets"
EMOJI = ASSETS / "emoji"
DELIVERY = Path(os.environ.get("REEL_DELIVERY",
                               Path.home() / "Documents" / "Notes" / "video-assets"))
# same override lint.sh reads, so the linter and newreel.py never disagree
BURNED_KEYWORDS = Path(os.environ.get("REEL_BURNED_KEYWORDS", ROOT / "keywords_burned.txt"))

# ---- frame spec (never changes) ----
W, H, FPS = 1080, 1920, 30
MAX_SECONDS = 20.0

# ---- audio targets (never changes) ----
LUFS_TARGET = -14.0
TRUE_PEAK_MAX = -1.0
SAMPLE_RATE = 48000
CHANNELS = 2

# ---- safe zones ----
# The furniture owns a fixed band. Content is laid out UNDERNEATH it, never behind
# it. This is the fix for "a banner that hides the thing it is describing".
TOP_DANGER = 220        # IG top chrome
BOTTOM_DANGER = 420     # IG caption + buttons
BANNER_ZONE = (0, TOP_DANGER, W, TOP_DANGER + 150)   # furniture lives only here
CONTENT_TOP = BANNER_ZONE[3] + 24                     # everything else starts here
CONTENT_BOTTOM = H - BOTTOM_DANGER                    # and stops here
BAND_H = CONTENT_BOTTOM - CONTENT_TOP                 # the b-roll lives in this band
CAPTION_BASELINE = H - BOTTOM_DANGER - 40             # captions sit above the chrome

# ---- palettes ----
# Rule: rotate per reel, pick from the subject. No orange. No purple on dark.
PALETTES = {
    "security":  {"bg": "#140b0d", "fg": "#ffe9ec", "accent": "#ff3b52", "accent2": "#ffbf3b", "dim": "#7c5a60"},
    "money":     {"bg": "#07130f", "fg": "#e8fff5", "accent": "#00e08a", "accent2": "#7ff0c4", "dim": "#3f6b5c"},
    "docs":      {"bg": "#0a1220", "fg": "#e9f2ff", "accent": "#3b9dff", "accent2": "#8fd0ff", "dim": "#455b78"},
    "hardware":  {"bg": "#101010", "fg": "#f2f2f2", "accent": "#d4d4d4", "accent2": "#8ab4f8", "dim": "#5a5a5a"},
    "video":     {"bg": "#0d0f18", "fg": "#eef0ff", "accent": "#f43f7a", "accent2": "#ffd166", "dim": "#5b5f7a"},
    "data":      {"bg": "#0b1412", "fg": "#e6fffb", "accent": "#14e0d0", "accent2": "#a6fff5", "dim": "#3d6a66"},
    "privacy":   {"bg": "#0e1116", "fg": "#eaeef5", "accent": "#5eead4", "accent2": "#fca5a5", "dim": "#4b5563"},
    # BC-008. Headstone grey with one warm accent, per that reel's b-roll plan.
    # The warm accent is GOLD, not orange: the plan asked for warmth, the rule
    # above bans orange, and gold satisfies both. Not the security red, not the
    # house lime, not the BC-007 aqua.
    "headstone": {"bg": "#101114", "fg": "#ecead4", "accent": "#d8b450", "accent2": "#a8adb4", "dim": "#5a5f66"},
    # BC-011. A pixel-art kingdom, so the palette is a retro game at night:
    # coin yellow on deep night blue with a grass mint second.
    # NOT the reference's daylight green #72a440, which is the one thing
    # Reel Boss says never to take from a reference. Coin yellow is also a
    # full stop brighter and cooler than BC-008's muted gold #d8b450, so the two
    # reels do not read as the same theme.
    "realm": {"bg": "#0b1220", "fg": "#eaf0ff", "accent": "#ffd400", "accent2": "#5ad1a0", "dim": "#4a5570"},
    # BC-012. Its own b-roll plan asks for "slate and a single cold accent, not
    # red, not aqua, not lime", which rules out security, data/privacy and the
    # house lime. Steel blue is cold without being the BC-003 docs blue #3b9dff,
    # which is a full stop brighter and reads as a link rather than as metal.
    "guard": {"bg": "#0d1117", "fg": "#e6edf3", "accent": "#8ab4d8", "accent2": "#5f7d95", "dim": "#3a4a5a"},
    # BC-018. The b-roll is the project's own render, and its background is the
    # app's violet #6466FA. Blue furniture on violet b-roll is the same hue
    # family and the captions stop separating, so the accent goes to the other
    # side of the wheel: amber. Not orange (banned) and not the BC-008 gold
    # #d8b450, which is a full stop duller and reads as brass rather than as a
    # highlighter. The ground is the BC-012 slate, which is the one neutral here
    # that does not tint toward the footage.
    "frame": {"bg": "#0d1117", "fg": "#eef1f6", "accent": "#f0b429", "accent2": "#9fb3c8", "dim": "#435060"},
}
BANNED_PALETTES = ["orange", "purple-on-dark"]  # documented, never registered above

# ---- text hygiene ----
# Em dash, en dash, double hyphen, horizontal bar, minus sign. Any of these in
# published text is the AI tell. lint_text() in lib/util.py enforces it.
BANNED_CHARS = ["—", "–", "―", "−", "--"]
BANNED_WORDS = ["free", "FREE", "Free"]  # banned in hooks and titles only

# ---- fonts ----
# Missing fonts still throw at use (lib.util.need), these are just where to look.
if sys.platform == "win32":
    _F = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    FONT_BOLD, FONT_REG, FONT_MONO = _F / "ariblk.ttf", _F / "arial.ttf", _F / "consola.ttf"
elif sys.platform == "darwin":
    FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
    FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
    FONT_MONO = "/System/Library/Fonts/Menlo.ttc"
else:  # Linux: Microsoft core fonts if installed, else Liberation (same metrics as Arial)
    def _first(*paths):
        return next((p for p in map(Path, paths) if p.exists()), Path(paths[0]))
    _M, _L = Path("/usr/share/fonts/truetype/msttcorefonts"), Path("/usr/share/fonts/truetype/liberation")
    FONT_BOLD = _first(_M / "Arial_Black.ttf", _L / "LiberationSans-Bold.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    FONT_REG = _first(_M / "Arial.ttf", _L / "LiberationSans-Regular.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    FONT_MONO = _first(_M / "Courier_New.ttf", _L / "LiberationMono-Regular.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
FONT_BOLD = os.environ.get("REEL_FONT_BOLD", FONT_BOLD)
FONT_REG = os.environ.get("REEL_FONT_REG", FONT_REG)
FONT_MONO = os.environ.get("REEL_FONT_MONO", FONT_MONO)
# Only needed to BAKE a new emoji. The baked PNGs in assets/emoji/ work anywhere.
# Off macOS there is no Apple font, so baking throws: bake on a Mac and copy the PNG.
APPLE_EMOJI_TTC = os.environ.get("REEL_APPLE_EMOJI", "/System/Library/Fonts/Apple Color Emoji.ttc")
