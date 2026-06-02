"""
asciigpt — image preprocessing stack (Pillow).

Everything that happens to an image BEFORE it becomes characters:

    load -> resize to character grid -> grayscale -> adjustments

The adjustments mirror the asciiart.eu slider panel and libcaca's flags:
brightness, contrast, sharpness, gamma, invert, and threshold. Each is a
pure transform on a Pillow ``Image`` in 8-bit grayscale ("L") mode, so
they compose cleanly and the renderer downstream only ever sees a single
grayscale image whose pixel dimensions equal the output character grid.

Terminal characters are roughly twice as tall as they are wide, so when
we auto-compute height from the image's aspect ratio we multiply by
``char_aspect`` (~0.5) to keep the art from looking vertically stretched.
"""

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


# Terminal characters are ~2x taller than wide; 0.5 compensates so a
# square image produces a roughly square block of characters.
DEFAULT_CHAR_ASPECT = 0.5


def load_image(path):
    """Open an image file with Pillow.

    Args:
        path: Path to an image (any format Pillow supports: PNG, JPEG,
              GIF, BMP, WebP, ...).

    Returns:
        A Pillow ``Image`` in whatever mode the file uses.

    Raises:
        FileNotFoundError: If the path does not exist.
        OSError: If the file exists but is not a readable image.
    """
    # Already a Pillow image (e.g. one a generation backend produced in
    # memory)? Use it as-is. This lets image_to_ascii() accept an open image,
    # not just a path, which is exactly what the prompt -> image -> ASCII
    # generation path relies on.
    if isinstance(path, Image.Image):
        return path
    try:
        return Image.open(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found: {path}")
    except OSError as exc:
        raise OSError(f"Could not open image '{path}': {exc}")


def compute_grid_size(orig_w, orig_h, width=None, height=None,
                      char_aspect=DEFAULT_CHAR_ASPECT):
    """Work out the (cols, rows) character grid for an image.

    Rules:
      * If both width and height are given, use them verbatim.
      * If only width is given, derive height from the aspect ratio,
        squashed by ``char_aspect`` for the tall-character correction.
      * If only height is given, derive width the same way.
      * If neither is given the caller should pass a default width first;
        this function still handles it by falling back to 80 columns.

    Args:
        orig_w, orig_h: Original pixel dimensions of the source image.
        width:  Desired columns (characters per line), or None to derive.
        height: Desired rows (lines), or None to derive.
        char_aspect: Width/height ratio of a terminal cell (~0.5).

    Returns:
        A (cols, rows) tuple, each at least 1.
    """
    if orig_w <= 0 or orig_h <= 0:
        raise ValueError("Source image has zero width or height.")

    aspect = orig_h / orig_w  # rows-per-col in pixel space

    if width is not None and height is not None:
        cols, rows = width, height
    elif width is not None:
        cols = width
        rows = int(round(aspect * width * char_aspect))
    elif height is not None:
        rows = height
        # Invert the derivation: cols = rows / (aspect * char_aspect)
        denom = aspect * char_aspect
        cols = int(round(rows / denom)) if denom > 0 else 80
    else:
        cols = 80
        rows = int(round(aspect * cols * char_aspect))

    return max(1, cols), max(1, rows)


def to_grid(img, cols, rows):
    """Resize an image to exactly ``cols`` x ``rows`` and convert to grayscale.

    After this, every pixel in the returned image corresponds to one output
    character, which is what the renderer expects.

    Args:
        img:  A Pillow image.
        cols: Target width in pixels (= characters per line).
        rows: Target height in pixels (= lines).

    Returns:
        A grayscale ("L" mode) Pillow image of size (cols, rows).
    """
    resized = img.resize((cols, rows), Image.Resampling.LANCZOS)
    return resized.convert("L")


def apply_brightness(img, factor):
    """Scale brightness. 1.0 = unchanged, <1 darker, >1 brighter."""
    if factor == 1.0:
        return img
    return ImageEnhance.Brightness(img).enhance(factor)


def apply_contrast(img, factor):
    """Scale contrast. 1.0 = unchanged, <1 flatter, >1 punchier."""
    if factor == 1.0:
        return img
    return ImageEnhance.Contrast(img).enhance(factor)


def apply_sharpness(img, factor):
    """Scale sharpness. 1.0 = unchanged, <1 blurrier, >1 sharper.

    Sharpening before ASCII conversion pulls out fine edges that would
    otherwise blur into a flat mid-tone at low character counts.
    """
    if factor == 1.0:
        return img
    return ImageEnhance.Sharpness(img).enhance(factor)


def apply_gamma(img, gamma):
    """Apply gamma correction via a 256-entry lookup table.

    gamma < 1 brightens mid-tones, gamma > 1 darkens them. Pillow has no
    built-in gamma op, so we build the power-law LUT ourselves and apply
    it with ``Image.point`` (fast, stays in C).

    Args:
        img:   Grayscale image.
        gamma: Exponent. 1.0 = unchanged.
    """
    if gamma == 1.0:
        return img
    if gamma <= 0:
        raise ValueError("gamma must be > 0")
    lut = [int(round(255 * (i / 255.0) ** gamma)) for i in range(256)]
    return img.point(lut)


def apply_invert(img):
    """Invert grayscale values (light <-> dark).

    Use this when the subject is dark on a light background and you want the
    subject rendered in dense glyphs rather than the background.
    """
    return ImageOps.invert(img)


def apply_threshold(img, level):
    """Hard two-level threshold: pixels >= level become white, else black.

    Produces a clean bilevel image, ideal with the ``max-bw`` preset or as a
    pre-step before line-art rendering.

    Args:
        img:   Grayscale image.
        level: Cutoff 0-255. Pixels at or above become 255, below become 0.
    """
    level = max(0, min(255, int(level)))
    lut = [255 if i >= level else 0 for i in range(256)]
    return img.point(lut)


def preprocess(img, cols, rows, *, brightness=1.0, contrast=1.0,
               sharpness=1.0, gamma=1.0, invert=False, threshold=None):
    """Run the full preprocessing stack and return a grayscale grid image.

    Order matters and is deliberate:
        1. resize + grayscale  (down to the character grid)
        2. sharpness           (recover edges lost in the downscale)
        3. brightness          (linear level shift)
        4. contrast            (spread or compress the range)
        5. gamma               (perceptual mid-tone curve)
        6. invert              (flip polarity, if asked)
        7. threshold           (bilevel clamp, if asked — applied last so it
                                acts on the fully-adjusted image)

    Args:
        img:        Source Pillow image (any mode).
        cols, rows: Target character-grid dimensions.
        brightness, contrast, sharpness, gamma: Enhancement factors.
        invert:     If True, flip light/dark.
        threshold:  If set (0-255), apply a hard bilevel threshold last.

    Returns:
        A grayscale ("L") Pillow image of size (cols, rows), ready for the
        renderer.
    """
    grid = to_grid(img, cols, rows)
    grid = apply_sharpness(grid, sharpness)
    grid = apply_brightness(grid, brightness)
    grid = apply_contrast(grid, contrast)
    grid = apply_gamma(grid, gamma)
    if invert:
        grid = apply_invert(grid)
    if threshold is not None:
        grid = apply_threshold(grid, threshold)
    return grid


def to_luminance_grid(img):
    """Convert a grayscale Pillow image to a 2D list of ints (0-255).

    Rows are lists of column values, i.e. ``grid[y][x]``.

    Args:
        img: A grayscale ("L") image whose size is (cols, rows).

    Returns:
        A list of ``rows`` lists, each of length ``cols``.
    """
    if img.mode != "L":
        img = img.convert("L")
    cols, rows = img.size
    # get_flattened_data() is the Pillow 12+ name; getdata() is the classic.
    try:
        flat = list(img.get_flattened_data())
    except AttributeError:
        flat = list(img.getdata())
    return [flat[y * cols:(y + 1) * cols] for y in range(rows)]
