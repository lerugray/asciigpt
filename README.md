# asciigpt

**A real CLI image to ASCII-art converter. Runs local, no network.**

```bash
python generate.py photo.jpg --preset high-contrast
```

asciigpt turns an image into genuine ASCII art with real conversion
technique: a Pillow preprocessing stack, named gradient presets, a Sobel
edge-detection mode with directional glyphs, three dithering algorithms,
and plain-text / ANSI-truecolor / HTML output. It also renders FIGlet text
banners. The feature set matches or beats the tools it learned from:
`jp2a`, `libcaca` / `img2txt`, and `asciiart.eu`.

> **What this is not (yet):** asciigpt does **not** generate images from
> prompts and does **not** ask an LLM to "draw" characters. It is a
> deterministic converter. AI-guided glyph selection is a documented future
> layer on top of this base, not part of it.

## What it does

- **Named gradient presets** — ~20 character-ramp styles you pick by name
  (`--preset high-contrast`), mirroring asciiart.eu's set (Alphabetic,
  Code Page 437, Gray Scale, Minimalist, ...) plus themed ramps of our own.
- **Preprocessing stack** — brightness, contrast, sharpness, gamma, invert,
  and bilevel threshold, all via Pillow.
- **Edge-detection mode** — a real Sobel outline that draws edges with
  directional glyphs (`-` `|` `/` `\`), not a luminance ramp. This is the
  jp2a `--edges-only` quality bar.
- **Dithering** — Floyd-Steinberg (default), ordered (Bayer), Atkinson, or
  none. Pure Python.
- **Three output formats** — plain text, 24-bit truecolor ANSI for the
  terminal, and a standalone HTML page with per-character colour.
- **Custom glyph palette** — bring your own ramp with `--chars " .:-=+*#%@"`.
- **FIGlet text** — `--text "ZERO PAGE"` prints a banner; combine it with an
  image to stamp a caption on the art.

## Quick start

```bash
# 1. Enter the repo
cd asciigpt

# 2. Set up a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies (Pillow + pyfiglet)
pip install -r requirements.txt

# 4. Convert an image
python generate.py photo.jpg
```

No API key, no account, no upload. Everything runs on your machine.

`python generate.py` is the convenient entry point. `python -m asciigpt`
is equivalent.

## Usage

### Basic conversion

```bash
# Default ramp, 80 columns
python generate.py photo.jpg

# Wider, with the detailed 70-step photographic ramp
python generate.py photo.jpg --width 120 --preset high-contrast

# Fix the output height too (overrides the aspect-ratio guess)
python generate.py photo.jpg --width 100 --height 50
```

### Gradient presets

```bash
# List every preset with a preview and description
python generate.py --list-presets

# Pick one by name
python generate.py portrait.jpg --preset smooth
python generate.py logo.png --preset minimalist
python generate.py game-screen.png --preset retro-green-screen
```

### Edge-detection mode (outlines)

```bash
# Sobel outline with directional glyphs  - | / \
python generate.py logo.png --edges

# Tune sensitivity: lower threshold = more edges
python generate.py photo.jpg --edges --edge-threshold 25
```

### Dithering

```bash
python generate.py photo.jpg --dither floyd-steinberg   # default, smooth
python generate.py photo.jpg --dither atkinson          # crisp, high-contrast
python generate.py photo.jpg --dither ordered           # screen-printed texture
python generate.py photo.jpg --dither none              # hard banding
```

### Preprocessing

```bash
# Brighten a dark photo and add punch
python generate.py dark.jpg --brightness 1.4 --contrast 1.3

# Sharpen fine detail before conversion
python generate.py detailed.jpg --sharpness 2.0

# Gamma curve (mid-tone lift)
python generate.py photo.jpg --gamma 0.7

# Invert light/dark (dark subject on light ground)
python generate.py sketch.jpg --invert

# Hard two-level threshold (great with --preset max-bw)
python generate.py logo.png --preset max-bw --threshold 128
```

### Output formats

```bash
# Plain text (default) — paste anywhere
python generate.py photo.jpg

# 24-bit truecolor for a modern terminal
python generate.py photo.jpg --format ansi

# Standalone HTML page with per-character colour
python generate.py photo.jpg --format html --background "#0b0b12" -o art.html
```

### Custom glyph palette

```bash
# Bring your own ramp, ordered dark -> light
python generate.py photo.jpg --chars " .:-=+*#%@"
```

### FIGlet text banners

```bash
# Standalone banner, no image needed
python generate.py --text "ZERO PAGE" --font slant

# Stamp a banner onto converted art (text output only)
python generate.py photo.jpg --text "RETRO" --text-row 1 --text-col 2
```

### Save to a file

```bash
python generate.py photo.jpg -o out.txt
python generate.py photo.jpg --format html -o out.html
```

## Gradient presets

ASCII presets are pure printable ASCII (safe in any terminal). Three
presets (`blocks`, `code-page-437`, `arrow`) use Unicode and need a
Unicode-capable font/terminal. Run `python generate.py --list-presets`
for the full table with previews.

| Name | Look | Best for |
|------|------|----------|
| `default` | Balanced 10-step | General purpose |
| `high-contrast` | 70-step Paul Bourke ramp | Photographs, max detail |
| `normal` / `normal2` | Classic medium ramps | Photographs |
| `smooth` | Gentle tonal steps | Portraits, faces |
| `grayscale` | Even perceptual steps | Balanced tone |
| `minimalist` / `minimal` | 4-5 levels | Logos, bold graphic look |
| `max-bw` | Two-level on/off | Line art (+ `--threshold`) |
| `mechanical` | Sharp angular glyphs | Machines, buildings |
| `organic` | Soft rounded glyphs | Nature, animals |
| `retro-green-screen` | Chunky phosphor ramp | Pair with `--format ansi` |
| `alphabetic` / `numerical` / `alphanumeric` / `math` | Character-class ramps | Texture/novelty |
| `blocks` / `code-page-437` / `arrow` | Unicode | Pixel-art / DOS / novelty |

## How it works

```
image ─▶ resize to char grid ─▶ grayscale ─▶ preprocessing ─┐
                                                            │
        ┌───────────────────────────────────────────────────┘
        ▼
   edges?  ── yes ─▶ Sobel pass ─▶ directional glyphs ( - | / \ ) ─┐
        │                                                          │
        └─ no ─▶ dither ─▶ level indices ─▶ map onto ramp ─────────┤
                                                                   ▼
                                              render: text / ANSI / HTML
```

The luminance path maps each cell's brightness to a character in the
chosen ramp (dark pixels get dense glyphs); dithering breaks up the
banding that a small character set would otherwise show. The edge path
ignores the ramp entirely: it runs a Sobel operator, and where the
gradient is strong enough it draws a glyph whose direction matches the
edge.

## Examples

The [`examples/`](examples/) directory holds real, reproducible output from
the CLI (regenerate with `python examples/make_examples.py`):

- `sphere.png` → `sphere.txt` — a shaded sphere via the `high-contrast`
  ramp with Floyd-Steinberg dithering.
- `house.png` → `house_edges.txt` — a house line drawing through edge mode
  (straight walls as `|`/`-`, roof as `/`/`\`).
- `house.html` — the same house as a truecolor HTML page.
- `banner.txt` — a FIGlet banner.

A peek at `house_edges.txt`:

```
                                                -------
                                              \\-------//
                                             \\\-     -//
                                             ||        |||
                            \--/             ///       \\\
                          \------/           ///-------\\
```

## Code tour

asciigpt is a small, readable package under [`asciigpt/`](asciigpt/):

| Module | Responsibility |
|--------|----------------|
| `gradients.py` | Named character ramps (`--preset`) |
| `preprocess.py` | Pillow stack: resize, grayscale, brightness/contrast/sharpness/gamma/invert/threshold |
| `dither.py` | Floyd-Steinberg, ordered, Atkinson, none |
| `edges.py` | Sobel edge detection + directional glyphs |
| `render.py` | text / ANSI / HTML serialisers |
| `figlet.py` | FIGlet banners and overlay compositing |
| `convert.py` | The pipeline that wires it all together (`image_to_ascii`) |
| `cli.py` | argparse front end |

`generate.py` at the repo root is a thin shim that forwards to `cli.py`.

## Dependencies

- `Pillow` — image loading and the preprocessing stack
- `pyfiglet` — FIGlet text banners

Both are in `requirements.txt`. Tests need `pytest` (`requirements-dev.txt`).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The suite covers gradient presets, glyph/level mapping, all four dithering
algorithms, edge-mode glyph direction, the renderers, and CLI parsing plus
end-to-end conversions — using small images generated on the fly, so no
binary fixtures are needed.

## Project docs

- `MISSION.md` — why this exists and what success looks like
- `research.md` — the reference-tool landscape (jp2a, libcaca, asciiart.eu, ...)
- `pipeline.md` — pipeline design notes
- `docs/handoffs/` — build-out briefs

## What's next

The deterministic base is the foundation. The planned next layer is the
"GPT" differentiator: **AI-guided glyph selection** that picks characters to
preserve edges and texture instead of mapping luminance blindly — enhancing
the real conversion rather than replacing it. That work is intentionally out
of scope for this build.
