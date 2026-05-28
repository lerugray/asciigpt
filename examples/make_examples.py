#!/usr/bin/env python3
"""
Generate the committed example images and their ASCII conversions.

Run from the repo root:

    .venv/bin/python examples/make_examples.py

This synthesises a couple of small, deterministic source images with
Pillow (so nothing binary needs to be hand-committed or downloaded) and
writes both the source PNG and several ASCII renderings into ``examples/``.
The README points at these files so its sample output is real, reproducible
output from the actual CLI — not hand-edited.

Re-run it any time the renderer changes to refresh the examples.
"""

import os
import sys

from PIL import Image, ImageDraw

# Make the package importable when run as a script from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asciigpt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def _write(name, text):
    path = os.path.join(HERE, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")
    print(f"wrote {name} ({len(text)} chars)")


def make_circle_image():
    """A shaded sphere on a dark ground — good for the luminance ramp."""
    w = h = 200
    img = Image.new("L", (w, h), 12)
    px = img.load()
    cx, cy, r = 95, 90, 80
    # Lambert-ish shading: brightest toward the upper-left light source.
    import math
    for y in range(h):
        for x in range(w):
            dx, dy = x - cx, y - cy
            dist = math.hypot(dx, dy)
            if dist <= r:
                # Surface normal z-component (fake sphere).
                nz = math.sqrt(max(0.0, 1 - (dist / r) ** 2))
                # Light from upper-left.
                lx, ly = -0.5, -0.5
                lz = math.sqrt(max(0.0, 1 - lx * lx - ly * ly))
                nx, ny = dx / r, dy / r
                intensity = max(0.05, nx * lx + ny * ly + nz * lz)
                px[x, y] = int(min(255, 30 + intensity * 225))
    path = os.path.join(HERE, "sphere.png")
    img.save(path)
    print("wrote sphere.png (generated)")
    return path


def make_house_image():
    """A simple house line drawing — good for edge mode (straight + diagonal)."""
    w = h = 160
    img = Image.new("RGB", (w, h), (240, 240, 240))
    d = ImageDraw.Draw(img)
    # Body
    d.rectangle([40, 80, 120, 140], fill=(70, 90, 160), outline=(0, 0, 0), width=2)
    # Roof (triangle)
    d.polygon([(30, 80), (80, 40), (130, 80)], fill=(160, 60, 50),
              outline=(0, 0, 0))
    # Door
    d.rectangle([72, 108, 92, 140], fill=(60, 40, 20))
    # Window
    d.rectangle([50, 92, 66, 108], fill=(220, 220, 120))
    # Sun
    d.ellipse([122, 16, 150, 44], fill=(245, 210, 60))
    path = os.path.join(HERE, "house.png")
    img.save(path)
    print("wrote house.png (generated)")
    return path


def main():
    # --- Example 1: shaded sphere via the luminance ramp ---------------
    sphere = make_circle_image()
    _write(
        "sphere.txt",
        asciigpt.image_to_ascii(
            sphere, width=60, preset="high-contrast",
            dither="floyd-steinberg",
        ),
    )
    _write(
        "sphere_blocks.txt",
        asciigpt.image_to_ascii(
            sphere, width=50, preset="blocks", dither="atkinson",
        ),
    )

    # --- Example 2: house line drawing via edge mode -------------------
    house = make_house_image()
    _write(
        "house_edges.txt",
        asciigpt.image_to_ascii(
            house, width=60, edges=True, edge_threshold=50,
        ),
    )
    _write(
        "house_ramp.txt",
        asciigpt.image_to_ascii(
            house, width=60, preset="default", dither="ordered",
        ),
    )

    # --- Example 3: a FIGlet banner ------------------------------------
    _write("banner.txt", asciigpt.render_text("asciigpt", font="standard"))

    # --- Example 4: HTML output (truecolor) ----------------------------
    _write(
        "house.html",
        asciigpt.image_to_ascii(
            house, width=60, preset="default", output_format="html",
            background="#0b0b12",
        ),
    )

    print("\nAll examples regenerated.")


if __name__ == "__main__":
    main()
