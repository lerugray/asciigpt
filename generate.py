#!/usr/bin/env python3
"""
asciigpt — image -> ASCII art converter (entry point shim).

This file used to hold the whole tool in one script. The tool has grown a
clean module set under ``asciigpt/`` (gradients, preprocess, dither, edges,
render, figlet, convert, cli); this shim just forwards to that CLI so the
familiar invocation keeps working:

    python generate.py photo.jpg --preset high-contrast --format ansi
    python generate.py --text "ZERO PAGE" --font slant
    python generate.py --list-presets

Equivalent to ``python -m asciigpt ...`` and the ``asciigpt`` console
script. See README.md for the full flag list, or run with --help.
"""

import os
import sys

# Make sure the package next to this file is importable when the script is
# run directly (``python generate.py`` from anywhere).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from asciigpt.cli import main  # noqa: E402  (import after sys.path tweak)

if __name__ == "__main__":
    sys.exit(main())
