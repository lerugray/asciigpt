"""
asciigpt — dithering (error diffusion + ordered), pure Python.

Dithering decides WHICH ramp level each cell gets. Without it, a smooth
gradient collapses into visible bands (all the "almost-white" pixels snap
to the same character). Dithering hides that banding by either diffusing
the rounding error into neighbouring cells (Floyd-Steinberg, Atkinson) or
by perturbing each cell with a fixed threshold matrix (ordered / Bayer).

Every function here takes:
    grid    : 2D list of luminance values 0-255 (grid[y][x])
    levels  : the number of distinct output levels (== len(character ramp))

and returns a 2D list of integer level indices in ``range(levels)``, where
0 is the darkest level and ``levels - 1`` is the lightest. The renderer
maps those indices straight onto the ramp string.

Keeping the contract as "indices, not characters" means dithering is
totally independent of which preset is in use — a clean seam, and easy to
unit-test (assert every index is in range).
"""


def _quantize_level(value, levels):
    """Snap a luminance value (0-255) to the nearest of ``levels`` levels.

    Returns an integer index in ``range(levels)``. With levels=4 the
    bucket centres land at 0, 85, 170, 255.
    """
    if levels <= 1:
        return 0
    # Scale 0..255 onto 0..levels-1, rounding to nearest.
    idx = int(round((value / 255.0) * (levels - 1)))
    return max(0, min(levels - 1, idx))


def _level_to_value(idx, levels):
    """Inverse of :func:`_quantize_level`: the luminance a level represents.

    Used to compute the quantization error for error-diffusion dithers.
    """
    if levels <= 1:
        return 0.0
    return (idx / (levels - 1)) * 255.0


def no_dither(grid, levels):
    """Plain nearest-level quantization. No error diffusion.

    This is the "None" option — fastest, but shows banding on smooth
    gradients. It's also the building block the renderer uses when the
    user passes ``--dither none``.
    """
    return [[_quantize_level(v, levels) for v in row] for row in grid]


def floyd_steinberg(grid, levels):
    """Floyd-Steinberg error diffusion (the classic default).

    For each cell, quantize to the nearest level, then push the rounding
    error to the right and below using the standard FS kernel::

            *   7/16
        3/16 5/16 1/16

    Args:
        grid:   2D list of luminance (0-255).
        levels: Number of ramp levels.

    Returns:
        2D list of level indices.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    # Work on floats so accumulated error stays precise.
    work = [[float(v) for v in row] for row in grid]
    out = [[0] * cols for _ in range(rows)]

    for y in range(rows):
        for x in range(cols):
            old = work[y][x]
            idx = _quantize_level(old, levels)
            out[y][x] = idx
            err = old - _level_to_value(idx, levels)

            if x + 1 < cols:
                work[y][x + 1] += err * 7 / 16
            if y + 1 < rows:
                if x - 1 >= 0:
                    work[y + 1][x - 1] += err * 3 / 16
                work[y + 1][x] += err * 5 / 16
                if x + 1 < cols:
                    work[y + 1][x + 1] += err * 1 / 16

    return out


def atkinson(grid, levels):
    """Atkinson dithering (the classic Mac / HyperCard look).

    Atkinson diffuses only 6/8 of the error (the rest is discarded), which
    gives crisper, higher-contrast results than Floyd-Steinberg — it tends
    to preserve detail in highlights and shadows at the cost of some tonal
    accuracy. Kernel (each neighbour gets 1/8)::

            *   1/8 1/8
        1/8 1/8 1/8
            1/8

    Args:
        grid:   2D list of luminance (0-255).
        levels: Number of ramp levels.

    Returns:
        2D list of level indices.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    work = [[float(v) for v in row] for row in grid]
    out = [[0] * cols for _ in range(rows)]

    for y in range(rows):
        for x in range(cols):
            old = work[y][x]
            idx = _quantize_level(old, levels)
            out[y][x] = idx
            err = (old - _level_to_value(idx, levels)) / 8.0

            # Two cells to the right on the current row.
            if x + 1 < cols:
                work[y][x + 1] += err
            if x + 2 < cols:
                work[y][x + 2] += err
            # Three cells on the next row (left, centre, right).
            if y + 1 < rows:
                if x - 1 >= 0:
                    work[y + 1][x - 1] += err
                work[y + 1][x] += err
                if x + 1 < cols:
                    work[y + 1][x + 1] += err
            # One cell two rows down.
            if y + 2 < rows:
                work[y + 2][x] += err

    return out


# A 4x4 Bayer threshold matrix, values 0..15. Normalised to 0..1 below.
# Ordered dithering compares each pixel against the matrix entry tiled
# across the image, producing the characteristic cross-hatch texture.
_BAYER_4X4 = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]


def ordered(grid, levels, matrix=None):
    """Ordered (Bayer) dithering using a tiled threshold matrix.

    Unlike error diffusion, ordered dithering is stateless per pixel: it
    nudges each value up or down by a fixed amount taken from a tiled
    matrix, then quantizes. The result has a regular, screen-printed
    texture — great for a retro/halftone feel.

    Args:
        grid:   2D list of luminance (0-255).
        levels: Number of ramp levels.
        matrix: Optional NxN threshold matrix of ascending integers; the
                default is the standard 4x4 Bayer matrix.

    Returns:
        2D list of level indices.
    """
    if matrix is None:
        matrix = _BAYER_4X4
    n = len(matrix)
    span = n * n  # number of distinct thresholds (16 for 4x4)

    # The perturbation amplitude: roughly the size of one quantization step,
    # so the matrix can tip a pixel into the neighbouring level but no more.
    step = 255.0 / max(1, levels)

    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    out = [[0] * cols for _ in range(rows)]

    for y in range(rows):
        for x in range(cols):
            # Threshold in -0.5..+0.5, centred so the average nudge is zero.
            t = (matrix[y % n][x % n] + 0.5) / span - 0.5
            nudged = grid[y][x] + t * step
            out[y][x] = _quantize_level(nudged, levels)

    return out


# Registry so the CLI/renderer can look up an algorithm by name.
ALGORITHMS = {
    "floyd-steinberg": floyd_steinberg,
    "atkinson": atkinson,
    "ordered": ordered,
    "none": no_dither,
}

DEFAULT_DITHER = "floyd-steinberg"


def dither_names():
    """Return the sorted list of available dither algorithm names."""
    return sorted(ALGORITHMS)


def apply_dither(name, grid, levels):
    """Dispatch to a dithering algorithm by name.

    Args:
        name:   One of ``ALGORITHMS`` (e.g. "floyd-steinberg", "none").
        grid:   2D luminance list (0-255).
        levels: Number of ramp levels.

    Returns:
        2D list of level indices.

    Raises:
        KeyError: If ``name`` is unknown (message lists valid names).
    """
    if name not in ALGORITHMS:
        valid = ", ".join(sorted(ALGORITHMS))
        raise KeyError(f"Unknown dither '{name}'. Available: {valid}")
    return ALGORITHMS[name](grid, levels)
