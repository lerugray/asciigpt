"""Tests for the dithering algorithms (Floyd-Steinberg, ordered, Atkinson, none)."""

import pytest

from asciigpt import dither


# A small smooth gradient grid (0..255 across 16 columns), 4 rows tall.
def _gradient_grid(cols=16, rows=4):
    return [
        [int(round(255 * x / (cols - 1))) for x in range(cols)]
        for _ in range(rows)
    ]


@pytest.mark.parametrize("name", ["floyd-steinberg", "ordered", "atkinson", "none"])
def test_all_algorithms_registered(name):
    assert name in dither.ALGORITHMS


@pytest.mark.parametrize("name", ["floyd-steinberg", "ordered", "atkinson", "none"])
def test_output_dimensions_preserved(name):
    grid = _gradient_grid()
    out = dither.apply_dither(name, grid, levels=10)
    assert len(out) == len(grid)
    assert all(len(orow) == len(grid[0]) for orow in out)


@pytest.mark.parametrize("name", ["floyd-steinberg", "ordered", "atkinson", "none"])
def test_indices_within_range(name):
    """Every emitted index must be a valid ramp index for the level count."""
    grid = _gradient_grid()
    levels = 8
    out = dither.apply_dither(name, grid, levels)
    for row in out:
        for idx in row:
            assert 0 <= idx < levels
            assert isinstance(idx, int)


def test_no_dither_is_deterministic_quantize():
    """'none' is plain nearest-level quantization: black->0, white->max."""
    grid = [[0, 255]]
    out = dither.no_dither(grid, 10)
    assert out == [[0, 9]]


def test_error_diffusion_changes_uniform_region_pattern():
    """On a flat mid-grey, FS should not collapse to a single index everywhere
    the way plain quantization does — error accumulates and tips some cells."""
    flat = [[100] * 12 for _ in range(6)]
    plain = dither.no_dither(flat, 4)
    fs = dither.floyd_steinberg(flat, 4)
    # Plain quantize: every cell identical.
    assert all(v == plain[0][0] for row in plain for v in row)
    # FS: at least two distinct indices appear (dithered texture).
    distinct = {v for row in fs for v in row}
    assert len(distinct) >= 2


def test_ordered_is_stateless_and_repeatable():
    """Ordered dithering must be deterministic (no RNG)."""
    grid = _gradient_grid()
    a = dither.ordered(grid, 6)
    b = dither.ordered(grid, 6)
    assert a == b


def test_atkinson_differs_from_floyd_steinberg():
    """The two error-diffusion kernels should not produce identical output
    on a gradient (different weights / discarded error)."""
    grid = _gradient_grid(cols=24, rows=6)
    fs = dither.floyd_steinberg(grid, 8)
    atk = dither.atkinson(grid, 8)
    assert fs != atk


def test_apply_dither_unknown_raises():
    with pytest.raises(KeyError) as exc:
        dither.apply_dither("bogus", _gradient_grid(), 10)
    assert "floyd-steinberg" in str(exc.value)


def test_full_range_present_after_dither_on_gradient():
    """A black->white gradient through FS should span from the darkest to the
    lightest level (it shouldn't crush the range)."""
    grid = _gradient_grid(cols=32, rows=8)
    out = dither.floyd_steinberg(grid, 10)
    flat = [v for row in out for v in row]
    assert min(flat) == 0
    assert max(flat) == 9
