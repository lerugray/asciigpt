"""
asciigpt — a real CLI image-to-ASCII-art converter.

Deterministic conversion that matches or beats jp2a / libcaca / asciiart.eu:
named gradient presets, a full Pillow preprocessing stack, a Sobel
edge-detection mode with directional glyphs, Floyd-Steinberg / ordered /
Atkinson dithering, plain-text / ANSI-truecolor / HTML output, custom glyph
palettes, and FIGlet text banners.

The deterministic converter is the engine. On top of it sits the headline
capability: generating ASCII art from a text prompt via a pluggable image
backend (prompt -> image -> convert). See ``asciigpt.generate``.

Public API
----------
    image_to_ascii(path, ...)   -> str   # the converter (path OR PIL image)
    prompt_to_ascii(prompt, ...) -> str  # generate art from a text prompt
    ImageBackend, ProceduralBackend      # pluggable generation backends
    get_backend, default_backend         # backend registry
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
from .generate import (
    prompt_to_ascii,
    ImageBackend,
    ProceduralBackend,
    CommandBackend,
    BACKENDS,
    get_backend,
    default_backend,
    procedural_caption,
    DEFAULT_GEN_SIZE,
)

__version__ = "0.3.0"

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
    # generation (prompt -> image -> ASCII)
    "prompt_to_ascii",
    "ImageBackend",
    "ProceduralBackend",
    "CommandBackend",
    "BACKENDS",
    "get_backend",
    "default_backend",
    "procedural_caption",
    "DEFAULT_GEN_SIZE",
]
