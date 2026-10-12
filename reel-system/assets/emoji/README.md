# Emoji

The pipeline uses **Apple emoji only**, as baked PNGs, and a missing one throws
instead of falling back to a system font. The PNGs are not in this repository:
Apple's font licence does not allow redistributing them.

Bake them once on a Mac (Apple Color Emoji ships with macOS):

```bash
cd reel-system
python3 theme.py                 # bakes the default set: lock money warn check brain fire eyes tools
python3 -c "import theme; theme.bake_emoji('🚀', 'rocket')"   # any other glyph
```

Then copy `assets/emoji/*.png` to the same folder on any other machine. Plates
that do not use an emoji, the 3D renderer and the voice need none of this.
