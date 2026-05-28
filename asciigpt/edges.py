"""
asciigpt — Sobel edge detection with directional glyphs (pure Python).

This is the real "outline" mode, the jp2a ``--edges-only`` quality bar. It
is NOT a luminance ramp: instead of "dark pixel -> dense character", it
finds edges in the image and draws each edge with a glyph that matches the
edge's *direction*:

    horizontal edge   ->  -
    vertical edge     ->  |
    diagonal  /       ->  /
    diagonal  \\       ->  \\
    (no edge)         ->  space

The direction comes from the Sobel operator, which estimates the image
gradient (Gx, Gy) at every pixel via two 3x3 convolutions::

        Gx              Gy
    -1  0  +1       -1 -2 -1
    -2  0  +2        0  0  0
    -1  0  +1       +1 +2 +1

The gradient *magnitude* sqrt(Gx^2 + Gy^2) tells us how strong the edge is
(thresholded so flat areas stay blank); the gradient *angle*
atan2(Gy, Gx) tells us which way it runs, which we bin into one of the
four glyphs above. An edge's glyph is perpendicular to its gradient, so we
rotate the angle by 90 degrees before binning.

Everything is plain Python (a few nested loops + math); no numpy. It's the
slow path by design — asciigpt trades speed for quality.
"""

import math


# Sobel kernels (3x3). Indexed [dy+1][dx+1] for dy,dx in {-1,0,+1}.
_SOBEL_X = [
    [-1, 0, 1],
    [-2, 0, 2],
    [-1, 0, 1],
]
_SOBEL_Y = [
    [-1, -2, -1],
    [0, 0, 0],
    [1, 2, 1],
]

# The four directional glyphs, plus the blank for "no edge".
GLYPH_HORIZONTAL = "-"
GLYPH_VERTICAL = "|"
GLYPH_DIAG_FWD = "/"    # bottom-left to top-right
GLYPH_DIAG_BACK = "\\"  # top-left to bottom-right
GLYPH_BLANK = " "


def _sobel_at(grid, x, y, cols, rows):
    """Compute (Gx, Gy) at a single pixel using replicate-edge padding.

    Pixels off the image border reuse the nearest in-bounds pixel
    (clamping), which avoids spurious edges along the picture frame.
    """
    gx = 0.0
    gy = 0.0
    for dy in (-1, 0, 1):
        sy = min(max(y + dy, 0), rows - 1)
        for dx in (-1, 0, 1):
            sx = min(max(x + dx, 0), cols - 1)
            val = grid[sy][sx]
            gx += _SOBEL_X[dy + 1][dx + 1] * val
            gy += _SOBEL_Y[dy + 1][dx + 1] * val
    return gx, gy


def _direction_glyph(gx, gy):
    """Pick the directional glyph for an edge with gradient (gx, gy).

    The gradient points across the edge; the edge itself runs perpendicular
    to it. We compute the edge angle (gradient angle + 90 degrees), fold it
    into 0-180 degrees (an edge and its 180-degree flip look the same), and
    bin into four 45-degree sectors.
    """
    # Gradient angle in degrees.
    grad_angle = math.degrees(math.atan2(gy, gx))
    # Edge runs perpendicular to the gradient.
    edge_angle = grad_angle + 90.0
    # Fold into [0, 180): direction is unsigned.
    edge_angle %= 180.0

    # Four sectors, each 45 degrees wide, centred on 0/45/90/135.
    #   ~0   (and ~180) -> horizontal  '-'
    #   ~45             -> forward diag '/'
    #   ~90             -> vertical     '|'
    #   ~135            -> back diag    '\'
    if edge_angle < 22.5 or edge_angle >= 157.5:
        return GLYPH_HORIZONTAL
    if edge_angle < 67.5:
        return GLYPH_DIAG_FWD
    if edge_angle < 112.5:
        return GLYPH_VERTICAL
    return GLYPH_DIAG_BACK


def detect_edges(grid, threshold=40.0):
    """Run a Sobel pass and return a 2D grid of directional glyph characters.

    Args:
        grid:      2D list of luminance values (0-255), grid[y][x].
        threshold: Minimum gradient magnitude for a cell to count as an
                   edge. Lower = more (noisier) edges; higher = only strong
                   outlines. 40 is a sensible default for 0-255 input.

    Returns:
        A 2D list of single characters: one of ``- | / \\`` on edges, and a
        space elsewhere. Same dimensions as the input grid.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    out = [[GLYPH_BLANK] * cols for _ in range(rows)]

    for y in range(rows):
        for x in range(cols):
            gx, gy = _sobel_at(grid, x, y, cols, rows)
            magnitude = math.hypot(gx, gy)
            if magnitude >= threshold:
                out[y][x] = _direction_glyph(gx, gy)
            # else: leave the blank already in place.

    return out


def edge_magnitude_grid(grid):
    """Return a 2D grid of raw Sobel gradient magnitudes (floats).

    Useful when you want to feed edge strength back into a luminance-style
    render (a "glow the edges" effect) rather than the hard glyph mode.
    Not used by the default edge mode but handy for experimentation/tests.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    out = [[0.0] * cols for _ in range(rows)]
    for y in range(rows):
        for x in range(cols):
            gx, gy = _sobel_at(grid, x, y, cols, rows)
            out[y][x] = math.hypot(gx, gy)
    return out
