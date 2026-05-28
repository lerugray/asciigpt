"""
asciigpt — the conversion pipeline that ties the pieces together.

This is the one function most callers want: :func:`image_to_ascii`. It
walks an image all the way to a finished string:

    load
      -> compute the character grid size
      -> preprocess (brightness / contrast / sharpness / gamma /
                     invert / threshold)
      -> EITHER  edge mode  (Sobel -> directional glyphs)
         OR      ramp mode  (dither -> level indices -> ramp characters)
      -> render (text / ansi / html)

The two rendering branches are mutually exclusive: edge mode draws an
outline with ``- | / \\`` and ignores the gradient ramp/dither entirely;
ramp mode is the luminance-to-character path with optional dithering. A
custom ``chars`` string overrides the named preset's ramp.

Keeping this orchestration in one place means the CLI is a thin wrapper
and the behaviour is easy to unit-test without going through argparse.
"""

from . import dither as _dither
from . import edges as _edges
from . import gradients as _gradients
from . import preprocess as _pre
from . import render as _render


def map_levels_to_chars(level_grid, ramp):
    """Turn a 2D grid of level indices into a 2D grid of characters.

    The dither/quantize step emits indices in ``range(len(ramp))`` where 0
    is darkest. The ramp string is ordered dark->light, so index -> ramp[i]
    is a direct lookup.

    Args:
        level_grid: 2D list of integer indices.
        ramp:       The character ramp (dark->light).

    Returns:
        2D list of single characters.
    """
    n = len(ramp)
    out = []
    for row in level_grid:
        out.append([ramp[max(0, min(n - 1, idx))] for idx in row])
    return out


def image_to_ascii(
    image_path,
    *,
    width=80,
    height=None,
    preset=_gradients.DEFAULT_PRESET,
    chars=None,
    dither=_dither.DEFAULT_DITHER,
    edges=False,
    edge_threshold=40.0,
    brightness=1.0,
    contrast=1.0,
    sharpness=1.0,
    gamma=1.0,
    invert=False,
    threshold=None,
    output_format=_render.DEFAULT_FORMAT,
    background="#000000",
    char_aspect=_pre.DEFAULT_CHAR_ASPECT,
):
    """Convert an image file to ASCII art and return it as a string.

    Args:
        image_path:    Path to the source image.
        width:         Output width in characters.
        height:        Output height in lines (None = derive from aspect).
        preset:        Named gradient preset (see ``gradients.PRESETS``).
        chars:         Custom ramp string; overrides ``preset`` when given.
        dither:        Dither algorithm name (ramp mode only).
        edges:         If True, use Sobel edge mode instead of the ramp.
        edge_threshold: Sobel magnitude cutoff for edge mode.
        brightness, contrast, sharpness, gamma: Preprocessing factors.
        invert:        Invert light/dark before mapping.
        threshold:     Optional 0-255 bilevel threshold.
        output_format: "text", "ansi", or "html".
        background:    Background colour for the HTML format.
        char_aspect:   Terminal cell width/height ratio (~0.5).

    Returns:
        The finished art as a string (plain text, ANSI, or HTML document).

    Raises:
        KeyError:   Unknown preset or dither name.
        ValueError: Bad output format or image dimensions.
        FileNotFoundError / OSError: Image can't be loaded.
    """
    if output_format not in _render.FORMATS:
        valid = ", ".join(_render.FORMATS)
        raise ValueError(
            f"Unknown output format '{output_format}'. Available: {valid}"
        )

    # Resolve the character ramp: custom string wins, else the named preset.
    ramp = chars if chars else _gradients.get_ramp(preset)
    if len(ramp) < 2:
        raise ValueError("Character ramp must have at least 2 characters.")

    # --- Load + size + preprocess -------------------------------------
    source = _pre.load_image(image_path)
    cols, rows = _pre.compute_grid_size(
        *source.size, width=width, height=height, char_aspect=char_aspect
    )
    gray = _pre.preprocess(
        source, cols, rows,
        brightness=brightness, contrast=contrast, sharpness=sharpness,
        gamma=gamma, invert=invert, threshold=threshold,
    )
    lum = _pre.to_luminance_grid(gray)

    # --- Choose characters --------------------------------------------
    if edges:
        # Edge mode: Sobel outline with directional glyphs.
        char_grid = _edges.detect_edges(lum, threshold=edge_threshold)
    else:
        # Ramp mode: dither to level indices, then map onto the ramp.
        levels = len(ramp)
        level_grid = _dither.apply_dither(dither, lum, levels)
        char_grid = map_levels_to_chars(level_grid, ramp)

    # --- Render --------------------------------------------------------
    if output_format == "text":
        return _render.grid_to_text(char_grid)
    if output_format == "ansi":
        return _render.grid_to_ansi(char_grid, source)
    # html
    return _render.grid_to_html(char_grid, source, background=background)


def text_to_ascii(grid_or_lines):
    """Tiny convenience: normalise a char grid OR list of lines to a string.

    Lets callers that already have a banner (list of strings) reuse the
    same output path as the image converter without special-casing.
    """
    if grid_or_lines and isinstance(grid_or_lines[0], list):
        return _render.grid_to_text(grid_or_lines)
    return "\n".join(grid_or_lines)
