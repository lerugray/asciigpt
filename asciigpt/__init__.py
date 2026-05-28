"""
asciigpt — a real CLI image-to-ASCII-art converter.

Deterministic conversion that matches or beats jp2a / libcaca / asciiart.eu:
named gradient presets, a full Pillow preprocessing stack, a Sobel
edge-detection mode with directional glyphs, Floyd-Steinberg / ordered /
Atkinson dithering, plain-text / ANSI-truecolor / HTML output, custom glyph
palettes, and FIGlet text banners.

The "GPT" / AI-guided glyph-selection layer is a documented *future*
enhancement on top of this deterministic base — it is intentionally not
part of this build (no image generation, no LLM calls here).

Public API
----------
    image_to_ascii(path, ...)   -> str   # the main converter
    PRESETS, get_ramp, preset_names      # gradient presets
    ALGORITHMS, dither_names             # dithering
    detect_edges                         # Sobel edge mode
    render_text, overlay_banner          # FIGlet banners
"""

from .convert import image_to_ascii, map_levels_to_chars
from .gradients import (
    PRESETS,
    DEFAULT_PRESET,
    get_ramp,
    preset_names,
    describe_presets,
)
from .dither import (
    ALGORITHMS,
    DEFAULT_DITHER,
    dither_names,
    apply_dither,
    floyd_steinberg,
    atkinson,
    ordered,
    no_dither,
)
from .edges import detect_edges, edge_magnitude_grid
from .render import (
    FORMATS,
    DEFAULT_FORMAT,
    grid_to_text,
    grid_to_ansi,
    grid_to_html,
)
from .figlet import render_text, overlay_banner, available as figlet_available

__version__ = "0.2.0"

__all__ = [
    "__version__",
    # converter
    "image_to_ascii",
    "map_levels_to_chars",
    # gradients
    "PRESETS",
    "DEFAULT_PRESET",
    "get_ramp",
    "preset_names",
    "describe_presets",
    # dithering
    "ALGORITHMS",
    "DEFAULT_DITHER",
    "dither_names",
    "apply_dither",
    "floyd_steinberg",
    "atkinson",
    "ordered",
    "no_dither",
    # edges
    "detect_edges",
    "edge_magnitude_grid",
    # render
    "FORMATS",
    "DEFAULT_FORMAT",
    "grid_to_text",
    "grid_to_ansi",
    "grid_to_html",
    # figlet
    "render_text",
    "overlay_banner",
    "figlet_available",
]
