"""Tests for luminance/level -> glyph mapping (convert + dither quantize)."""

from asciigpt import dither
from asciigpt.convert import map_levels_to_chars


def test_quantize_endpoints():
    """0 luminance -> darkest level (0); 255 -> lightest (levels-1)."""
    assert dither._quantize_level(0, 10) == 0
    assert dither._quantize_level(255, 10) == 9


def test_quantize_midpoint():
    """A mid-grey lands near the middle level."""
    idx = dither._quantize_level(128, 11)  # 11 levels -> centre is 5
    assert idx in (5, 6)


def test_quantize_clamps_out_of_range():
    assert dither._quantize_level(-50, 5) == 0
    assert dither._quantize_level(999, 5) == 4


def test_quantize_single_level():
    """A degenerate 1-level ramp always returns index 0."""
    assert dither._quantize_level(200, 1) == 0


def test_level_to_value_roundtrip_endpoints():
    assert dither._level_to_value(0, 10) == 0.0
    assert dither._level_to_value(9, 10) == 255.0


def test_map_levels_to_chars_basic():
    ramp = "@%#*+=-:. "  # 10 chars, dark->light
    # indices 0 (darkest) and 9 (lightest) and a couple in the middle.
    grid = [[0, 9], [3, 6]]
    chars = map_levels_to_chars(grid, ramp)
    assert chars[0][0] == "@"      # darkest
    assert chars[0][1] == " "      # lightest
    assert chars[1][0] == ramp[3]
    assert chars[1][1] == ramp[6]


def test_map_levels_clamps_bad_indices():
    """Out-of-range indices are clamped, never IndexError."""
    ramp = "@#. "
    grid = [[-1, 99]]
    chars = map_levels_to_chars(grid, ramp)
    assert chars[0][0] == "@"        # clamped to 0
    assert chars[0][1] == " "        # clamped to last


def test_dark_pixel_picks_dense_glyph():
    """End-to-end mapping intent: darker luminance -> denser (front) glyph."""
    ramp = "@%#*+=-:. "
    levels = len(ramp)
    dark = dither.no_dither([[10]], levels)
    bright = dither.no_dither([[245]], levels)
    dark_char = map_levels_to_chars(dark, ramp)[0][0]
    bright_char = map_levels_to_chars(bright, ramp)[0][0]
    # Dense glyph appears earlier in the ramp than the sparse one.
    assert ramp.index(dark_char) < ramp.index(bright_char)
