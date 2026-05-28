"""
asciigpt — render a character grid to text, ANSI truecolor, or HTML.

This is the back half of the pipeline. The front half (preprocess + dither
+ edges) decides WHICH character lands in each cell; this module decides
how to SERIALISE that grid of characters into something you can paste into
a terminal, a web page, or a file.

Three output formats, matching the reference tools:

  * ``text`` — plain monospace characters. Universal, copy-paste anywhere.
  * ``ansi`` — 24-bit truecolor escape codes (libcaca / jp2a ``--colors``).
               Each character is wrapped in the colour sampled from the
               source image at that cell.
  * ``html`` — a ``<pre>`` block with per-character ``<span>`` colours and
               a configurable page background (jp2a ``--html``).

Colour comes from the ORIGINAL (un-grayscaled) image, resized to the same
character grid, so a red balloon renders in red glyphs even though the
glyph *choice* was made from luminance.
"""

import html as _html

from PIL import Image


# ANSI escape helpers.
_ESC = "\x1b["
_RESET = "\x1b[0m"


def grid_to_text(char_grid):
    """Join a 2D list of characters into a plain multi-line string."""
    return "\n".join("".join(row) for row in char_grid)


def _sample_colors(source_img, cols, rows):
    """Resize the source image to the grid and return RGB tuples per cell.

    Args:
        source_img: The ORIGINAL Pillow image (any mode); converted to RGB.
        cols, rows: Character-grid dimensions.

    Returns:
        2D list ``color[y][x] = (r, g, b)``.
    """
    rgb = source_img.convert("RGB").resize(
        (cols, rows), Image.Resampling.LANCZOS
    )
    try:
        flat = list(rgb.get_flattened_data())
    except AttributeError:
        flat = list(rgb.getdata())
    return [flat[y * cols:(y + 1) * cols] for y in range(rows)]


def grid_to_ansi(char_grid, source_img):
    """Render a character grid as 24-bit truecolor ANSI text.

    Each character is prefixed with a foreground-colour escape sampled from
    ``source_img`` at that cell, and every line ends with a reset so the
    terminal state never leaks past the art.

    Args:
        char_grid:  2D list of characters.
        source_img: Original Pillow image for colour sampling.

    Returns:
        A string containing ANSI escape codes; print it to a truecolor
        terminal.
    """
    rows = len(char_grid)
    cols = len(char_grid[0]) if rows else 0
    colors = _sample_colors(source_img, cols, rows)

    out_lines = []
    for y in range(rows):
        parts = []
        prev = None
        for x in range(cols):
            ch = char_grid[y][x]
            r, g, b = colors[y][x]
            # Only emit a new colour code when the colour actually changes;
            # keeps the output dramatically smaller on flat regions.
            if (r, g, b) != prev:
                parts.append(f"{_ESC}38;2;{r};{g};{b}m")
                prev = (r, g, b)
            parts.append(ch)
        parts.append(_RESET)
        out_lines.append("".join(parts))
    return "\n".join(out_lines)


def grid_to_html(char_grid, source_img=None, *, background="#000000",
                 default_fg="#cccccc", font_size="10px",
                 title="asciigpt"):
    """Render a character grid as a standalone HTML document.

    If ``source_img`` is given, each character gets its own colour sampled
    from the image (truecolor, like the ANSI path). If it's None, the whole
    block uses ``default_fg`` (monochrome), which keeps the HTML tiny.

    Args:
        char_grid:  2D list of characters.
        source_img: Optional original image for per-character colour.
        background: CSS colour for the page/``<pre>`` background.
        default_fg: CSS colour used when no source image is supplied.
        font_size:  CSS font-size for the monospace block.
        title:      HTML document title.

    Returns:
        A complete HTML document string.
    """
    rows = len(char_grid)
    cols = len(char_grid[0]) if rows else 0

    colors = None
    if source_img is not None:
        colors = _sample_colors(source_img, cols, rows)

    body_lines = []
    for y in range(rows):
        line_parts = []
        prev_hex = None
        run = []
        for x in range(cols):
            ch = char_grid[y][x]
            esc = _html.escape(ch)
            if colors is not None:
                r, g, b = colors[y][x]
                hexc = f"#{r:02x}{g:02x}{b:02x}"
                if hexc != prev_hex:
                    # flush the previous run
                    if run:
                        line_parts.append(
                            f'<span style="color:{prev_hex}">'
                            f'{"".join(run)}</span>'
                        )
                        run = []
                    prev_hex = hexc
                run.append(esc)
            else:
                run.append(esc)
        # flush the tail of the line
        if colors is not None and run:
            line_parts.append(
                f'<span style="color:{prev_hex}">{"".join(run)}</span>'
            )
        elif colors is None:
            line_parts.append("".join(run))
        body_lines.append("".join(line_parts))

    body = "\n".join(body_lines)

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>{_html.escape(title)}</title>\n"
        "<style>\n"
        f"  body {{ background: {background}; margin: 0; }}\n"
        "  pre.asciigpt {\n"
        "    font-family: 'Courier New', Courier, monospace;\n"
        f"    font-size: {font_size};\n"
        "    line-height: 1.0;\n"
        "    letter-spacing: 0;\n"
        f"    color: {default_fg};\n"
        f"    background: {background};\n"
        "    white-space: pre;\n"
        "    margin: 0;\n"
        "    padding: 8px;\n"
        "  }\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        '<pre class="asciigpt">'
        f"{body}"
        "</pre>\n"
        "</body>\n"
        "</html>\n"
    )


# Registry for the CLI.
FORMATS = ("text", "ansi", "html")
DEFAULT_FORMAT = "text"
