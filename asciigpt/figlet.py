"""
asciigpt — FIGlet text banners (pyfiglet).

FIGlet turns a short string into big ASCII-letterform art ("banner" text).
asciigpt uses it two ways:

  * standalone — ``asciigpt --text "HELLO"`` prints a banner, no image
    needed (handy for titles and headers).
  * overlay — stamp a banner on top of image-converted art so a piece can
    carry a caption in the same ASCII register (the idea borrowed from
    Nokse22/ascii-draw's FIGlet text tool).

This module wraps pyfiglet behind a tiny API so the rest of the code (and
the tests) don't import pyfiglet directly, and so a missing pyfiglet fails
with one clear message instead of an ImportError deep in the CLI.
"""

try:
    import pyfiglet
    _HAS_PYFIGLET = True
except ImportError:  # pragma: no cover - exercised only when dep missing
    _HAS_PYFIGLET = False


DEFAULT_FONT = "standard"


def available():
    """True if pyfiglet is importable."""
    return _HAS_PYFIGLET


def render_text(text, font=DEFAULT_FONT, width=80):
    """Render ``text`` as a FIGlet banner string.

    Args:
        text:  The string to bannerise (keep it short — a word or two).
        font:  A pyfiglet font name (e.g. "standard", "slant", "big").
        width: Wrapping width passed to pyfiglet.

    Returns:
        A multi-line string of the banner (trailing blank lines trimmed).

    Raises:
        RuntimeError: If pyfiglet isn't installed, or the font is unknown.
    """
    if not _HAS_PYFIGLET:
        raise RuntimeError(
            "FIGlet text needs pyfiglet. Install it: pip install pyfiglet"
        )
    try:
        fig = pyfiglet.Figlet(font=font, width=width)
    except pyfiglet.FontNotFound:
        raise RuntimeError(
            f"Unknown FIGlet font '{font}'. "
            "Run `pyfiglet -l` to list installed fonts."
        )
    rendered = fig.renderText(text)
    # Trim trailing whitespace-only lines pyfiglet often appends.
    lines = rendered.rstrip("\n").split("\n")
    while lines and lines[-1].strip() == "":
        lines.pop()
    return "\n".join(lines)


def overlay_banner(art_lines, banner_lines, *, row=0, col=0,
                   transparent=True):
    """Stamp a FIGlet banner onto an existing block of ASCII art.

    The banner is drawn over ``art_lines`` starting at (row, col). Where a
    banner cell is a space and ``transparent`` is True, the underlying art
    shows through; otherwise the banner cell overwrites it.

    The canvas is grown with spaces if the banner would overflow the art's
    current bounds, so a banner is never clipped.

    Args:
        art_lines:    List of strings (the base art), one per line.
        banner_lines: List of strings (the FIGlet banner).
        row:          Top row to place the banner at (0-based).
        col:          Left column to place the banner at (0-based).
        transparent:  If True, banner spaces don't erase the art beneath.

    Returns:
        A new list of strings with the banner composited in.
    """
    # Work on a mutable list-of-lists canvas.
    canvas = [list(line) for line in art_lines]

    banner_h = len(banner_lines)
    banner_w = max((len(b) for b in banner_lines), default=0)

    needed_rows = row + banner_h
    needed_cols = col + banner_w

    # Grow vertically.
    while len(canvas) < needed_rows:
        canvas.append([])
    # Grow each affected row horizontally with spaces.
    for y in range(len(canvas)):
        target_w = needed_cols if (row <= y < row + banner_h) else len(canvas[y])
        while len(canvas[y]) < target_w:
            canvas[y].append(" ")

    # Composite.
    for by, bline in enumerate(banner_lines):
        y = row + by
        for bx, ch in enumerate(bline):
            x = col + bx
            if transparent and ch == " ":
                continue
            canvas[y][x] = ch

    return ["".join(r) for r in canvas]
