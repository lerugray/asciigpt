"""Tests for the output renderers: text, ANSI truecolor, HTML."""

from PIL import Image

from asciigpt import render


def _solid_rgb(color, w=6, h=3):
    return Image.new("RGB", (w, h), color)


def test_grid_to_text_joins_lines():
    grid = [["a", "b"], ["c", "d"]]
    assert render.grid_to_text(grid) == "ab\ncd"


def test_ansi_contains_truecolor_escape_and_reset():
    grid = [["#", "#"], ["#", "#"]]
    img = _solid_rgb((255, 0, 0), 2, 2)
    out = render.grid_to_ansi(grid, img)
    # 24-bit foreground escape for pure red, and a reset per line.
    assert "\x1b[38;2;255;0;0m" in out
    assert out.count("\x1b[0m") == 2  # one reset per row


def test_ansi_line_count_matches_grid():
    grid = [["x"] * 4 for _ in range(5)]
    img = _solid_rgb((10, 20, 30), 4, 5)
    out = render.grid_to_ansi(grid, img)
    assert len(out.split("\n")) == 5


def test_html_is_wellformed_document():
    grid = [["<", ">"], ["&", "x"]]
    img = _solid_rgb((0, 128, 255), 2, 2)
    html = render.grid_to_html(grid, img, background="#123456")
    assert html.startswith("<!DOCTYPE html>")
    assert "<pre" in html and "</pre>" in html
    assert "</html>" in html
    # Background colour propagated.
    assert "#123456" in html


def test_html_escapes_special_characters():
    """The < > & glyphs must be HTML-escaped so the page renders them."""
    grid = [["<", ">", "&"]]
    img = _solid_rgb((255, 255, 255), 3, 1)
    html = render.grid_to_html(grid, img)
    assert "&lt;" in html
    assert "&gt;" in html
    assert "&amp;" in html


def test_html_per_char_color_spans_when_image_given():
    grid = [["#", "#"]]
    img = _solid_rgb((255, 0, 0), 2, 1)
    html = render.grid_to_html(grid, img)
    assert 'style="color:#ff0000"' in html


def test_html_monochrome_when_no_image():
    grid = [["#", "#"]]
    html = render.grid_to_html(grid, source_img=None, default_fg="#abcdef")
    # No per-char color spans; the block uses default_fg.
    assert "<span" not in html
    assert "#abcdef" in html


def test_formats_registry():
    assert render.FORMATS == ("text", "ansi", "html")
    assert render.DEFAULT_FORMAT == "text"
