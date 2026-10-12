"""Easing. Linear motion reads as a slideshow; eased motion reads as edited.

Every curve maps 0..1 to 0..1 (out_back overshoots past 1 on purpose).
Beats stay FRACTIONS of the shot, so `window()` turns a shot fraction into a
0..1 progress for one beat and the curve shapes it.
"""


def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def window(t, a, b):
    """Progress through the beat that runs from a to b, clamped to 0..1."""
    return clamp01((t - a) / max(b - a, 1e-6))


def out_cubic(p):
    """Fast in, soft landing. The default for anything arriving."""
    return 1 - (1 - clamp01(p)) ** 3


def in_out_cubic(p):
    """Soft start and soft stop. For counters, fills and camera moves."""
    p = clamp01(p)
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def out_back(p, s=1.70158):
    """Overshoots about 10% then settles. For pops: a word, a badge, a window."""
    p = clamp01(p) - 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2


if __name__ == "__main__":
    for f in (out_cubic, in_out_cubic, out_back):
        assert abs(f(0)) < 1e-9 and abs(f(1) - 1) < 1e-9, f.__name__
    assert max(out_back(i / 100) for i in range(101)) > 1.05      # it really overshoots
    assert all(in_out_cubic(i / 100) <= in_out_cubic((i + 1) / 100) for i in range(100))
    assert window(0.5, 0.25, 0.75) == 0.5 and window(0, 0.25, 0.75) == 0
    print("ease ok")
