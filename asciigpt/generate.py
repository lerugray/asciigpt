"""
asciigpt.generate — the prompt -> image -> ASCII generation seam.

Direction (2026-06-02): asciigpt's headline capability is *generating* ASCII
art from a text prompt, with the deterministic converter (the rest of this
package) retained as the engine underneath. The path is always:

    prompt -> [image backend] -> Pillow image -> image_to_ascii() -> ASCII art

The middle "make a picture" step is a PLUGGABLE BACKEND. A backend is any
object with a ``generate(prompt, *, size)`` method that returns a Pillow
``Image``. That single seam lets very different generators share one pipeline
without ever touching the converter or the renderers:

    * ProceduralBackend — the default, and what ships today. Draws a
      recognisable scene from prompt keywords using Pillow primitives.
      Offline, deterministic, zero-cost, no dependency beyond Pillow. It is
      the development / test / offline-fallback backend, *not* a general
      artist: prompts it doesn't recognise get a deterministic abstract
      composition. Think of it as the seam's proof that the wiring works.

    * (next) a Claude-backed dev backend — Claude emits a structured drawing
      (SVG / primitives) that we rasterise, so *arbitrary* prompts work using
      an Anthropic subscription during development. Keeps a real image in the
      middle, so the converter is unchanged.

    * (integration) a hosted text-to-image API backend — best quality, used by
      the retrogaze service where the per-image cost is absorbed server-side.

Swapping backends never changes the converter; only this file grows.
"""

import hashlib
import math
import os
import shlex
import subprocess
import tempfile

from PIL import Image, ImageDraw

from .convert import image_to_ascii


# Pixel resolution of the generated base image. The converter downsamples this
# to the character grid, so it only needs to be big enough to carry the shapes
# cleanly; 256 is plenty and keeps procedural generation fast.
DEFAULT_GEN_SIZE = 256

# Background palettes. The converter maps dark pixels to dense glyphs and bright
# pixels to sparse ones, so polarity is an art-direction choice, not a detail:
#   * luminous subjects (sun, sphere, star) read best as bright shapes on a
#     dark ground — the subject becomes a clean void in a textured field.
#   * "icon" subjects (house, tree, face) read best as darker ink on a light
#     ground — the subject is drawn in glyphs on near-empty space.
_DARK = (14, 16, 26)
_SKY = (12, 16, 44)
_PAPER = (244, 244, 248)


# --------------------------------------------------------------------------
# Backend interface
# --------------------------------------------------------------------------

class ImageBackend:
    """Contract for a 'turn a prompt into a picture' backend.

    A backend is any object exposing:

        name                       -- short identifier (str)
        generate(prompt, *, size)  -- return a Pillow Image of (size, size)

    Subclass and override :meth:`generate`, or just duck-type the same shape.
    Whatever image you return is fed straight into the deterministic converter.
    """

    name = "base"

    def generate(self, prompt, *, size=DEFAULT_GEN_SIZE):
        raise NotImplementedError(
            "ImageBackend subclasses must implement generate()."
        )


# --------------------------------------------------------------------------
# Small drawing helpers
# --------------------------------------------------------------------------

def _box(*vals):
    """Round a flat sequence of coords to an int bounding box list."""
    return [int(round(v)) for v in vals]


def _poly(*xy):
    """Turn a flat x0,y0,x1,y1,... sequence into a list of int (x, y) points."""
    it = iter(xy)
    return [(int(round(x)), int(round(y))) for x, y in zip(it, it)]


def _seed_ints(prompt, n):
    """Return ``n`` deterministic 0-255 ints derived from ``prompt``.

    Uses SHA-256 so the same prompt always yields the same numbers across
    runs — Python's built-in ``hash()`` is salted per process and would not be
    reproducible. Used to place shapes in the abstract fallback.
    """
    digest = hashlib.sha256(prompt.encode("utf-8")).digest()
    return [digest[i % len(digest)] for i in range(n)]


# --------------------------------------------------------------------------
# Procedural scene painters (each takes an RGB image + the prompt)
# --------------------------------------------------------------------------

def _draw_sphere(img, *, tint=(210, 220, 255), bright=False):
    """Shade a sphere lit from the upper-left onto ``img`` (RGB)."""
    w, h = img.size
    px = img.load()
    cx, cy = w * 0.5, h * 0.46
    r = min(w, h) * 0.40
    lx, ly = -0.5, -0.5
    lz = math.sqrt(max(0.0, 1 - lx * lx - ly * ly))
    base = 70 if bright else 25
    for y in range(h):
        for x in range(w):
            dx, dy = x - cx, y - cy
            dist = math.hypot(dx, dy)
            if dist <= r:
                # z-component of a fake unit normal, then Lambert shading.
                nz = math.sqrt(max(0.0, 1 - (dist / r) ** 2))
                nx, ny = dx / r, dy / r
                intensity = max(0.05, nx * lx + ny * ly + nz * lz)
                level = min(1.0, (base + intensity * 220) / 255.0)
                px[x, y] = tuple(int(c * level) for c in tint)


def _draw_star(img):
    """A five-point star (bright on a dark ground)."""
    d = ImageDraw.Draw(img)
    w, h = img.size
    cx, cy = w * 0.5, h * 0.5
    outer, inner = min(w, h) * 0.44, min(w, h) * 0.18
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rad = outer if k % 2 == 0 else inner
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(_poly(*[c for p in pts for c in p]), fill=(252, 226, 96))


def _draw_house(img):
    """A small house — straight walls + a diagonal roof (good for edges)."""
    d = ImageDraw.Draw(img)
    w, h = img.size
    sx, sy = w / 160.0, h / 160.0
    d.rectangle(_box(40 * sx, 80 * sy, 120 * sx, 140 * sy),
                fill=(70, 90, 160), outline=(20, 20, 30),
                width=max(1, int(2 * sx)))
    d.polygon(_poly(30 * sx, 80 * sy, 80 * sx, 40 * sy, 130 * sx, 80 * sy),
              fill=(160, 60, 50), outline=(20, 20, 30))
    d.rectangle(_box(72 * sx, 108 * sy, 92 * sx, 140 * sy), fill=(60, 40, 20))
    d.rectangle(_box(50 * sx, 92 * sy, 66 * sx, 108 * sy), fill=(210, 210, 110))


def _draw_mountain(img):
    """Two overlapping peaks with snow caps and a low sun."""
    d = ImageDraw.Draw(img)
    w, h = img.size
    d.polygon(_poly(0, h, 0.45 * w, 0.30 * h, 0.78 * w, h), fill=(86, 96, 108))
    d.polygon(_poly(0.34 * w, h, 0.70 * w, 0.42 * h, w, h), fill=(64, 72, 84))
    d.polygon(_poly(0.45 * w, 0.30 * h, 0.385 * w, 0.46 * h, 0.515 * w, 0.46 * h),
              fill=(236, 239, 246))
    d.ellipse(_box(0.70 * w, 0.12 * h, 0.84 * w, 0.26 * h), fill=(248, 226, 120))


def _draw_tree(img):
    """A round-canopy tree on a trunk."""
    d = ImageDraw.Draw(img)
    w, h = img.size
    d.rectangle(_box(0.46 * w, 0.56 * h, 0.54 * w, 0.86 * h), fill=(110, 75, 45))
    d.ellipse(_box(0.22 * w, 0.30 * h, 0.50 * w, 0.62 * h), fill=(72, 158, 82))
    d.ellipse(_box(0.50 * w, 0.30 * h, 0.78 * w, 0.62 * h), fill=(50, 128, 62))
    d.ellipse(_box(0.30 * w, 0.16 * h, 0.70 * w, 0.58 * h), fill=(64, 146, 76))


def _draw_heart(img):
    """A heart from two lobes and a triangle."""
    d = ImageDraw.Draw(img)
    w, h = img.size
    fill = (208, 52, 72)
    d.ellipse(_box(0.22 * w, 0.22 * h, 0.52 * w, 0.52 * h), fill=fill)
    d.ellipse(_box(0.48 * w, 0.22 * h, 0.78 * w, 0.52 * h), fill=fill)
    d.polygon(_poly(0.24 * w, 0.42 * h, 0.76 * w, 0.42 * h, 0.50 * w, 0.80 * h),
              fill=fill)


def _draw_face(img):
    """A simple smiley face."""
    d = ImageDraw.Draw(img)
    w, h = img.size
    d.ellipse(_box(0.28 * w, 0.20 * h, 0.72 * w, 0.80 * h), fill=(232, 196, 162))
    d.ellipse(_box(0.40 * w, 0.42 * h, 0.46 * w, 0.50 * h), fill=(40, 40, 48))
    d.ellipse(_box(0.54 * w, 0.42 * h, 0.60 * w, 0.50 * h), fill=(40, 40, 48))
    d.arc(_box(0.40 * w, 0.52 * h, 0.60 * w, 0.70 * h), 20, 160,
          fill=(120, 60, 50), width=max(1, int(0.012 * w)))


def _draw_abstract(img, prompt):
    """A deterministic composition of shapes seeded by the prompt text.

    The fallback for prompts the procedural backend doesn't recognise. It is
    different for different prompts but identical for the same prompt, so it is
    safe to assert on in tests and stable for the user.
    """
    d = ImageDraw.Draw(img)
    w, h = img.size
    vals = _seed_ints(prompt, 24)
    palette = [(230, 90, 70), (90, 160, 230), (240, 196, 88),
               (120, 200, 140), (196, 120, 210)]
    for i in range(5):
        b = i * 4
        x0 = vals[b] / 255 * w * 0.65
        y0 = vals[b + 1] / 255 * h * 0.65
        size = 40 + vals[b + 2] / 255 * (min(w, h) * 0.45)
        color = palette[vals[b + 3] % len(palette)]
        bbox = _box(x0, y0, x0 + size, y0 + size)
        if vals[b] % 2 == 0:
            d.ellipse(bbox, fill=color)
        else:
            d.rectangle(bbox, fill=color)


# --------------------------------------------------------------------------
# Scene registry: keyword -> painter, background, human caption
# --------------------------------------------------------------------------

def _scene_sphere(img, prompt):   _draw_sphere(img)
def _scene_sun(img, prompt):      _draw_sphere(img, tint=(255, 224, 120), bright=True)
def _scene_moon(img, prompt):     _draw_sphere(img, tint=(220, 224, 232))
def _scene_star(img, prompt):     _draw_star(img)
def _scene_house(img, prompt):    _draw_house(img)
def _scene_mountain(img, prompt): _draw_mountain(img)
def _scene_tree(img, prompt):     _draw_tree(img)
def _scene_heart(img, prompt):    _draw_heart(img)
def _scene_face(img, prompt):     _draw_face(img)
def _scene_abstract(img, prompt): _draw_abstract(img, prompt)


# Order matters: the first scene whose keyword appears in the prompt wins, so
# specific subjects ("sun", "moon") precede the generic "sphere".
_SCENES = [
    (("sun", "sunshine", "sunrise", "sunset"), _scene_sun,   _SKY,  "a bright sun"),
    (("moon", "lunar"),                        _scene_moon,  _DARK, "the moon"),
    (("star",),                                _scene_star,  _DARK, "a star"),
    (("sphere", "ball", "planet", "orb", "circle", "bubble", "marble"),
                                               _scene_sphere, _DARK, "a shaded sphere"),
    (("house", "home", "cabin", "cottage", "building", "hut"),
                                               _scene_house, _PAPER, "a little house"),
    (("mountain", "mountains", "hill", "peak", "alps", "volcano"),
                                               _scene_mountain, _PAPER, "mountains"),
    (("tree", "forest", "oak", "pine", "palm", "plant", "bush"),
                                               _scene_tree,  _PAPER, "a tree"),
    (("heart", "love", "valentine"),           _scene_heart, _PAPER, "a heart"),
    (("face", "portrait", "head", "person", "smiley", "emoji", "selfie"),
                                               _scene_face,  _PAPER, "a face"),
]

_DEFAULT_SCENE = (("abstract",), _scene_abstract, _PAPER, "an abstract composition")


def _match_scene(prompt):
    """Pick the scene whose keyword first appears in ``prompt`` (lowercased).

    Falls back to the deterministic abstract composition when nothing matches.
    """
    low = prompt.lower()
    for keywords, painter, bg, caption in _SCENES:
        if any(k in low for k in keywords):
            return keywords, painter, bg, caption
    return _DEFAULT_SCENE


def procedural_caption(prompt):
    """Human-readable description of what the procedural backend will draw.

    Handy for telling the user ("Generating: a little house") so it's obvious
    the offline placeholder — not a real text-to-image model — is in play.
    """
    return _match_scene(prompt)[3]


# --------------------------------------------------------------------------
# The default backend
# --------------------------------------------------------------------------

class ProceduralBackend(ImageBackend):
    """Offline, deterministic, dependency-free image backend.

    Maps prompt keywords to a small library of Pillow-drawn scenes; unknown
    prompts get a deterministic abstract composition. Not a general artist —
    it exists so the prompt -> image -> ASCII path works with zero cost and no
    network, as the seam a real text-to-image backend later drops into.
    """

    name = "procedural"

    def generate(self, prompt, *, size=DEFAULT_GEN_SIZE):
        if not prompt or not prompt.strip():
            raise ValueError("prompt must be a non-empty string.")
        size = max(16, int(size))
        _keywords, painter, bg, _caption = _match_scene(prompt)
        img = Image.new("RGB", (size, size), bg)
        painter(img, prompt)
        return img


# --------------------------------------------------------------------------
# A live backend: shell out to any external image generator
# --------------------------------------------------------------------------

class CommandBackend(ImageBackend):
    """Generate the base image by running an external command.

    This is the seam a *real* generator drops into without asciigpt changing:
    a hosted text-to-image API CLI (the retrogaze service, cost absorbed
    server-side), a local Stable-Diffusion script, or a rasterize render
    written to a file. asciigpt stays out of the image-making business — it
    just runs the command and converts whatever PNG comes back.

    The command is a shell template with three placeholders:

        {prompt}   the text prompt (asciigpt shell-quotes it for you)
        {output}   the path asciigpt expects the image at (shell-quoted)
        {size}     the requested square pixel size (an int)

    Example::

        ASCIIGPT_IMAGE_COMMAND='txt2img --prompt {prompt} --size {size} --out {output}'
        asciigpt --prompt "a neon city" --backend command

    The command must write an image to ``{output}``; asciigpt loads and
    converts it like any other image.
    """

    name = "command"

    def __init__(self, command=None, *, timeout=180):
        # Explicit command wins; otherwise read the environment. Either may be
        # empty here — we only complain at generate() time, so constructing the
        # backend (e.g. via get_backend) never fails just for lack of config.
        self.command = command or os.environ.get("ASCIIGPT_IMAGE_COMMAND") or ""
        self.timeout = timeout

    def generate(self, prompt, *, size=DEFAULT_GEN_SIZE):
        if not prompt or not prompt.strip():
            raise ValueError("prompt must be a non-empty string.")
        if not self.command.strip():
            raise RuntimeError(
                "CommandBackend has no command. Set ASCIIGPT_IMAGE_COMMAND (or "
                "pass command=...) to a shell template using {prompt} {output} "
                "{size} that writes an image to {output}."
            )
        size = max(16, int(size))
        with tempfile.TemporaryDirectory(prefix="asciigpt-gen-") as tmp:
            out_path = os.path.join(tmp, "image.png")
            command = self.command.format(
                prompt=shlex.quote(prompt),
                output=shlex.quote(out_path),
                size=size,
            )
            try:
                subprocess.run(
                    command, shell=True, check=True, timeout=self.timeout,
                    capture_output=True, text=True,
                )
            except subprocess.TimeoutExpired:
                raise RuntimeError(
                    f"Image command timed out after {self.timeout}s."
                )
            except subprocess.CalledProcessError as exc:
                detail = (exc.stderr or exc.stdout or "").strip()
                raise RuntimeError(
                    f"Image command failed (exit {exc.returncode}). {detail}"
                )
            if not os.path.exists(out_path):
                raise RuntimeError(
                    "Image command succeeded but wrote no image to {output}; "
                    "check the command template's output path."
                )
            # Load fully into memory before the temp directory is removed.
            with Image.open(out_path) as img:
                return img.convert("RGB").copy()


# --------------------------------------------------------------------------
# Backend registry + the public generate function
# --------------------------------------------------------------------------

BACKENDS = {
    "procedural": ProceduralBackend,
    "command": CommandBackend,
}


def get_backend(name="procedural", **kwargs):
    """Instantiate a registered backend by name.

    Raises KeyError (with the valid names) for an unknown backend, mirroring
    how the gradient/dither lookups behave elsewhere in the package.
    """
    try:
        backend_cls = BACKENDS[name]
    except KeyError:
        valid = ", ".join(sorted(BACKENDS))
        raise KeyError(f"Unknown backend '{name}'. Available: {valid}")
    return backend_cls(**kwargs)


def default_backend():
    """The backend used when a caller doesn't specify one (procedural)."""
    return get_backend("procedural")


def prompt_to_ascii(prompt, *, backend=None, size=DEFAULT_GEN_SIZE, **convert_opts):
    """Generate ASCII art from a text prompt.

    Runs ``prompt -> backend.generate -> image_to_ascii`` so every converter
    feature (presets, edges, dithering, preprocessing, text/ANSI/HTML output)
    is available on generated art exactly as it is on a converted file.

    Args:
        prompt:       The text description to generate from.
        backend:      An ImageBackend instance; defaults to ProceduralBackend.
        size:         Pixel size of the generated base image (square) before
                      conversion.
        **convert_opts: Forwarded verbatim to ``image_to_ascii`` — e.g.
                      ``width``, ``height``, ``preset``, ``chars``, ``dither``,
                      ``edges``, ``output_format``, the preprocessing factors.

    Returns:
        The finished ASCII art as a string (text, ANSI, or HTML).

    Raises:
        ValueError: Empty prompt, or a bad converter option.
    """
    if not prompt or not prompt.strip():
        raise ValueError("prompt must be a non-empty string.")
    backend = backend or default_backend()
    image = backend.generate(prompt, size=size)
    return image_to_ascii(image, **convert_opts)
