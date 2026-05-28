"""
Shared test fixtures: small, deterministic, generated images.

The tests must not depend on any binary asset checked into git, so we
synthesise tiny images with Pillow on the fly. Each helper returns a path
to a freshly-written file inside a pytest ``tmp_path`` directory.

The images are chosen to exercise specific code paths:
  * gradient_image  — a smooth left->right luminance ramp (tests tonal
                      mapping + dithering: every ramp level should appear).
  * shapes_image    — a white disc + a black rectangle on grey (tests edge
                      detection: clear curved + straight boundaries).
  * solid_image     — a single flat colour (degenerate / edge-case input).
"""

from PIL import Image, ImageDraw


def gradient_image(tmp_path, w=64, h=32, name="gradient.png"):
    """Write a horizontal black->white gradient PNG. Returns its path."""
    img = Image.new("L", (w, h))
    px = img.load()
    for x in range(w):
        value = int(round(255 * x / max(1, w - 1)))
        for y in range(h):
            px[x, y] = value
    path = tmp_path / name
    img.save(path)
    return str(path)


def shapes_image(tmp_path, w=80, h=80, name="shapes.png"):
    """Write an RGB image with a disc and a rectangle. Returns its path.

    Mid-grey background, a white filled circle (curved edges) and a black
    filled rectangle (straight edges) — ideal for checking the edge mode
    produces a mix of directional glyphs.
    """
    img = Image.new("RGB", (w, h), (128, 128, 128))
    draw = ImageDraw.Draw(img)
    # White disc, upper-left-ish.
    draw.ellipse([8, 8, 40, 40], fill=(255, 255, 255))
    # Black rectangle, lower-right-ish.
    draw.rectangle([44, 44, 72, 72], fill=(0, 0, 0))
    path = tmp_path / name
    img.save(path)
    return str(path)


def color_image(tmp_path, w=48, h=24, name="color.png"):
    """Write an RGB image with distinct colour quadrants. Returns its path.

    Used to verify ANSI / HTML colour sampling emits the expected channels.
    """
    img = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w // 2, h // 2], fill=(255, 0, 0))       # red
    draw.rectangle([w // 2, 0, w, h // 2], fill=(0, 255, 0))       # green
    draw.rectangle([0, h // 2, w // 2, h], fill=(0, 0, 255))       # blue
    draw.rectangle([w // 2, h // 2, w, h], fill=(255, 255, 255))   # white
    path = tmp_path / name
    img.save(path)
    return str(path)


def solid_image(tmp_path, value=200, w=20, h=10, name="solid.png"):
    """Write a flat single-luminance PNG. Returns its path."""
    img = Image.new("L", (w, h), value)
    path = tmp_path / name
    img.save(path)
    return str(path)
