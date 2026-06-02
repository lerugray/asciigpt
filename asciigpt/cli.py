"""
asciigpt — command-line interface (argparse).

Flag conventions follow jp2a where they exist (``--width``/``--height``,
``--invert``, ``--background``, custom ``--chars``) and add the asciigpt
features on top (``--preset``, ``--dither``, ``--edges``, ``--format``,
``--text``). The CLI is deliberately thin: it parses flags, calls
``asciigpt.convert.image_to_ascii`` (or the FIGlet path), and writes the
result to stdout or a file.

Two input modes:

  * an image positional argument (or ``--image``) -> convert it.
  * ``--text "WORDS"``                              -> FIGlet banner.

If ``--text`` is combined with an image, the banner is composited on top
of the converted art (text-format output only).

Entry points:
  * ``python -m asciigpt <image>``
  * the ``asciigpt`` console script (see pyproject / setup), and
  * the legacy ``python generate.py <image>`` shim at the repo root.
"""

import argparse
import sys

from . import (
    __version__,
    image_to_ascii,
    describe_presets,
    preset_names,
    dither_names,
    DEFAULT_PRESET,
    DEFAULT_DITHER,
    FORMATS,
    DEFAULT_FORMAT,
)
from . import figlet as _figlet
from . import render as _render
from . import generate as _generate


def build_parser():
    """Construct the argparse parser for the asciigpt CLI."""
    parser = argparse.ArgumentParser(
        prog="asciigpt",
        description=(
            "asciigpt — generate ASCII art from a text prompt, or convert an "
            "image. Named gradient presets, edge detection, dithering, and "
            "text/ANSI/HTML output."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  asciigpt --prompt "a shaded sphere" --preset high-contrast
  asciigpt --prompt "a little house" --edges
  asciigpt photo.jpg
  asciigpt photo.jpg --width 100 --preset high-contrast
  asciigpt logo.png --edges --edge-threshold 60
  asciigpt photo.jpg --dither atkinson --invert
  asciigpt photo.jpg --format ansi            # 24-bit colour in terminal
  asciigpt photo.jpg --format html -o art.html
  asciigpt photo.jpg --chars " .:-=+*#%@"     # custom ramp
  asciigpt --text "ZERO PAGE" --font slant    # FIGlet banner, no image
  asciigpt photo.jpg --text "RETRO"           # banner stamped on the art
  asciigpt --list-presets
""",
    )

    parser.add_argument(
        "image",
        nargs="?",
        default=None,
        help="Path to the image to convert (or use --image).",
    )
    parser.add_argument(
        "--image", "-i",
        dest="image_flag",
        default=None,
        help="Path to the image to convert (flag form of the positional).",
    )

    # --- generation (prompt -> image -> ASCII) ------------------------
    parser.add_argument(
        "--prompt", "-P", default=None, metavar="TEXT",
        help="Generate ASCII art from a text description instead of "
             "converting a file (prompt -> image -> ASCII).",
    )
    parser.add_argument(
        "--gen-size", type=int, default=_generate.DEFAULT_GEN_SIZE,
        metavar="PX",
        help="Pixel size of the generated base image before conversion "
             f"(prompt mode only; default {_generate.DEFAULT_GEN_SIZE}).",
    )

    # --- size (jp2a conventions) --------------------------------------
    parser.add_argument(
        "--width", "-w", type=int, default=80,
        help="Output width in characters (default: 80).",
    )
    parser.add_argument(
        "--height", "-H", type=int, default=None,
        help="Output height in lines (default: from aspect ratio).",
    )

    # --- character selection ------------------------------------------
    parser.add_argument(
        "--preset", "-p", default=DEFAULT_PRESET, metavar="NAME",
        help=f"Named gradient preset (default: {DEFAULT_PRESET}). "
             "See --list-presets.",
    )
    parser.add_argument(
        "--chars", "-c", default=None, metavar="RAMP",
        help="Custom character ramp, dark->light (overrides --preset). "
             'e.g. --chars " .:-=+*#%%@"',
    )

    # --- dithering / edges --------------------------------------------
    parser.add_argument(
        "--dither", "-d", default=DEFAULT_DITHER, choices=dither_names(),
        help=f"Dither algorithm for ramp mode (default: {DEFAULT_DITHER}).",
    )
    parser.add_argument(
        "--edges", "-e", action="store_true",
        help="Edge-detection mode: Sobel outline with directional glyphs "
             "( - | / \\ ) instead of a luminance ramp.",
    )
    parser.add_argument(
        "--edge-threshold", type=float, default=40.0, metavar="N",
        help="Sobel magnitude cutoff for --edges (default: 40; "
             "lower = more edges).",
    )

    # --- preprocessing (asciiart.eu / libcaca sliders) ----------------
    parser.add_argument("--brightness", type=float, default=1.0,
                        help="Brightness factor (1.0 = unchanged).")
    parser.add_argument("--contrast", type=float, default=1.0,
                        help="Contrast factor (1.0 = unchanged).")
    parser.add_argument("--sharpness", type=float, default=1.0,
                        help="Sharpness factor (1.0 = unchanged).")
    parser.add_argument("--gamma", type=float, default=1.0,
                        help="Gamma correction (1.0 = unchanged).")
    parser.add_argument("--invert", action="store_true",
                        help="Invert light/dark before mapping.")
    parser.add_argument("--threshold", type=int, default=None, metavar="N",
                        help="Hard bilevel threshold 0-255 (off by default).")

    # --- output -------------------------------------------------------
    parser.add_argument(
        "--format", "-f", dest="output_format",
        default=DEFAULT_FORMAT, choices=list(FORMATS),
        help=f"Output format (default: {DEFAULT_FORMAT}).",
    )
    parser.add_argument(
        "--background", "-b", default="#000000", metavar="CSS",
        help="Background colour for --format html (default: #000000).",
    )
    parser.add_argument(
        "--output", "-o", default=None, metavar="FILE",
        help="Write to FILE instead of stdout.",
    )

    # --- FIGlet text --------------------------------------------------
    parser.add_argument(
        "--text", "-t", default=None, metavar="STRING",
        help="Render STRING as a FIGlet banner (standalone, or stamped on "
             "the image when an image is also given).",
    )
    parser.add_argument(
        "--font", default=_figlet.DEFAULT_FONT, metavar="NAME",
        help=f"FIGlet font for --text (default: {_figlet.DEFAULT_FONT}).",
    )
    parser.add_argument(
        "--text-row", type=int, default=0, metavar="ROW",
        help="Row to stamp the --text banner at when overlaying (default: 0).",
    )
    parser.add_argument(
        "--text-col", type=int, default=0, metavar="COL",
        help="Column to stamp the --text banner at when overlaying "
             "(default: 0).",
    )

    # --- info ---------------------------------------------------------
    parser.add_argument(
        "--list-presets", action="store_true",
        help="List gradient presets and exit.",
    )
    parser.add_argument(
        "--version", "-V", action="version",
        version=f"asciigpt {__version__}",
    )

    return parser


def _print_presets():
    """Print the preset table for --list-presets."""
    print("Available gradient presets (dark -> light):\n")
    rows = describe_presets()
    name_w = max(len(name) for name, _, _ in rows)
    for name, preview, desc in rows:
        print(f"  {name:<{name_w}}  {preview}")
        print(f"  {'':<{name_w}}  {desc}\n")


def _write(text, output_path):
    """Write the result to a file or stdout."""
    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(text)
            if not text.endswith("\n"):
                handle.write("\n")
        print(f"Saved to: {output_path}", file=sys.stderr)
    else:
        print(text)


def main(argv=None):
    """CLI entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_presets:
        _print_presets()
        return 0

    # Resolve inputs: a generation prompt, an image (the positional wins over
    # the --image flag), and/or a FIGlet banner.
    image_path = args.image or args.image_flag
    prompt = args.prompt

    # Need at least one input.
    if not image_path and not prompt and not args.text:
        parser.print_help()
        print(
            "\nError: provide a --prompt to generate from, an image to "
            "convert, or --text for a FIGlet banner.",
            file=sys.stderr,
        )
        return 1

    # Conversion knobs shared by the image path and the prompt path.
    convert_opts = dict(
        width=args.width,
        height=args.height,
        preset=args.preset,
        chars=args.chars,
        dither=args.dither,
        edges=args.edges,
        edge_threshold=args.edge_threshold,
        brightness=args.brightness,
        contrast=args.contrast,
        sharpness=args.sharpness,
        gamma=args.gamma,
        invert=args.invert,
        threshold=args.threshold,
        output_format=args.output_format,
        background=args.background,
    )

    try:
        # ---- Standalone FIGlet banner (text only) --------------------
        if args.text and not image_path and not prompt:
            banner = _figlet.render_text(
                args.text, font=args.font, width=args.width
            )
            _write(banner, args.output)
            return 0

        # ---- Produce the art: generate from a prompt, or convert -----
        if prompt:
            if image_path:
                print(
                    "Note: --prompt given; generating from text and ignoring "
                    "the image argument.",
                    file=sys.stderr,
                )
            print(
                "Generating (procedural placeholder): "
                f"{_generate.procedural_caption(prompt)}...",
                file=sys.stderr,
            )
            art = _generate.prompt_to_ascii(
                prompt, size=args.gen_size, **convert_opts
            )
        else:
            art = image_to_ascii(image_path, **convert_opts)

        # ---- Optional FIGlet overlay (text format only) -------------
        if args.text:
            if args.output_format != "text":
                print(
                    "Warning: --text overlay only applies to --format text; "
                    "ignoring the banner for this format.",
                    file=sys.stderr,
                )
            else:
                banner = _figlet.render_text(
                    args.text, font=args.font, width=args.width
                )
                art_lines = art.split("\n")
                banner_lines = banner.split("\n")
                art_lines = _figlet.overlay_banner(
                    art_lines, banner_lines,
                    row=args.text_row, col=args.text_col,
                )
                art = "\n".join(art_lines)

        _write(art, args.output)
        return 0

    except (KeyError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (FileNotFoundError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:  # pragma: no cover
        print("\nCancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
