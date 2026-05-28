"""Tests for the Sobel edge-detection mode and its directional glyphs."""

from asciigpt import edges


def test_flat_region_has_no_edges():
    """A perfectly uniform grid has zero gradient -> all blanks."""
    grid = [[120] * 10 for _ in range(10)]
    out = edges.detect_edges(grid, threshold=10)
    assert all(ch == edges.GLYPH_BLANK for row in out for ch in row)


def test_vertical_boundary_gives_vertical_glyph():
    """A left-dark / right-light split is a vertical edge -> '|'."""
    grid = [[0, 0, 0, 0, 255, 255, 255, 255] for _ in range(6)]
    out = edges.detect_edges(grid, threshold=40)
    # The boundary sits around column 3-4; a vertical glyph must appear there.
    boundary_glyphs = {out[y][3] for y in range(6)} | {out[y][4] for y in range(6)}
    assert edges.GLYPH_VERTICAL in boundary_glyphs


def test_horizontal_boundary_gives_horizontal_glyph():
    """A top-dark / bottom-light split is a horizontal edge -> '-'."""
    rows = [[0] * 8 for _ in range(4)] + [[255] * 8 for _ in range(4)]
    out = edges.detect_edges(rows, threshold=40)
    boundary_glyphs = set(out[3]) | set(out[4])
    assert edges.GLYPH_HORIZONTAL in boundary_glyphs


def test_only_directional_glyphs_or_blank():
    """Edge mode emits exactly the 4 directional glyphs or a space."""
    allowed = {
        edges.GLYPH_HORIZONTAL, edges.GLYPH_VERTICAL,
        edges.GLYPH_DIAG_FWD, edges.GLYPH_DIAG_BACK, edges.GLYPH_BLANK,
    }
    # A diagonal split to exercise the diagonal glyphs too.
    grid = [[0 if x < y else 255 for x in range(12)] for y in range(12)]
    out = edges.detect_edges(grid, threshold=30)
    produced = {ch for row in out for ch in row}
    assert produced <= allowed


def test_diagonal_boundary_gives_diagonal_glyph():
    """A diagonal dark/light split should produce a diagonal glyph somewhere."""
    grid = [[0 if x < y else 255 for x in range(16)] for y in range(16)]
    out = edges.detect_edges(grid, threshold=30)
    produced = {ch for row in out for ch in row}
    assert (edges.GLYPH_DIAG_FWD in produced) or (edges.GLYPH_DIAG_BACK in produced)


def test_threshold_controls_edge_count():
    """A higher threshold yields fewer (or equal) edge cells than a lower one."""
    # A gentle ramp so gradient magnitude is modest and threshold-sensitive.
    grid = [[min(255, x * 12) for x in range(20)] for _ in range(8)]
    low = edges.detect_edges(grid, threshold=5)
    high = edges.detect_edges(grid, threshold=120)

    def count_edges(g):
        return sum(ch != edges.GLYPH_BLANK for row in g for ch in row)

    assert count_edges(high) <= count_edges(low)


def test_dimensions_preserved():
    grid = [[i * 7 % 256 for i in range(9)] for _ in range(5)]
    out = edges.detect_edges(grid)
    assert len(out) == 5
    assert all(len(r) == 9 for r in out)


def test_direction_glyph_sectors():
    """Direct unit-check of the angle->glyph binning for the cardinal cases."""
    # gradient pointing +x (horizontal gradient) => vertical edge '|'
    assert edges._direction_glyph(10.0, 0.0) == edges.GLYPH_VERTICAL
    # gradient pointing +y (vertical gradient) => horizontal edge '-'
    assert edges._direction_glyph(0.0, 10.0) == edges.GLYPH_HORIZONTAL
