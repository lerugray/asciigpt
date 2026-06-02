<div align="center">

# asciigpt

### Generate ASCII art from a text prompt — or convert any image.

A real, local, dependency-light CLI: named gradient presets, a Sobel
edge-detection mode, three dithering algorithms, and plain-text /
ANSI-truecolor / HTML output. Type a prompt and get art, or point it at a photo.

[![tests](https://github.com/lerugray/asciigpt/actions/workflows/tests.yml/badge.svg)](https://github.com/lerugray/asciigpt/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Version](https://img.shields.io/badge/version-0.3.0-blueviolet.svg)

</div>

```console
$ asciigpt --prompt "a little house" --edges

                          \-
                        \----//
                     \\---------/
                   \-----\\//-----//
                \\-----\      //-----/
             \\-----\\          //-----//
           \-----\\                //-----//
         \\\\\--------------------------/////
         ||//|||  ---                  /|\\||
         //-/|/\----------------------/-|\-\\
           /||||\\----//              | ||\
           ||||||\---/||              | ||
           ||||||/---\||-------/      | |||
           |||||/-----\\\-----//      | |||
           |||||-------||\----||      | |||
           |||||       |||    |||     | |||
           |||||  ---  ||\----||/     \ |||
           |||/\-------//-----\\\-----/-|||
            |/--------------------------\|
            //---------------------------\
                          ----
```

> **`prompt → image → ASCII`.** A prompt becomes a base image through a
> pluggable *backend*, and the converter turns it into ASCII. The output is
> ASCII, never a raster image. asciigpt does **not** train its own image model
> and does **not** ask an LLM to "type" characters. See
> [How it works](#how-it-works).

---

## Contents

- [Features](#features)
- [Install](#install)
- [Usage](#usage)
- [Gradient presets](#gradient-presets)
- [How it works](#how-it-works)
- [Examples](#examples)
- [Roadmap](#roadmap)
- [Code tour](#code-tour)
- [Tests](#tests)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Features

- 🎨 **Generate from a prompt** — `--prompt "a neon city"` makes a base image
  through a pluggable backend and converts it. An **offline procedural**
  backend is the default (deterministic, no network); `--backend command`
  shells out to any external generator. Every feature below applies to
  generated art too.
- 🌈 **~20 named gradient presets** — pick a character ramp by name
  (`--preset high-contrast`), mirroring asciiart.eu's set plus themed ramps.
- 🛠️ **Full preprocessing stack** — brightness, contrast, sharpness, gamma,
  invert, and bilevel threshold, all via Pillow.
- ✏️ **Edge-detection mode** — a real Sobel outline drawn with directional
  glyphs (`-` `|` `/` `\`), not a luminance ramp. The jp2a `--edges-only`
  quality bar.
- 🌫️ **Dithering** — Floyd–Steinberg (default), ordered (Bayer), Atkinson, or
  none. Pure Python.
- 🖥️ **Three output formats** — plain text, 24-bit truecolor ANSI, and a
  standalone HTML page with per-character colour.
- 🔤 **Custom glyph palette** and **FIGlet text banners** (`--text`, `--chars`).
- 📦 **Local & dependency-light** — just Pillow + pyfiglet. No account, no
  upload; the converter and procedural backend run fully offline.

## Install

```bash
git clone https://github.com/lerugray/asciigpt.git
cd asciigpt
python3 -m venv .venv && source .venv/bin/activate
pip install .          # installs Pillow + pyfiglet and the `asciigpt` command
```

Then `asciigpt` is on your PATH:

```bash
asciigpt --prompt "a shaded sphere" --preset high-contrast
asciigpt photo.jpg --format ansi
```

No install needed if you'd rather not: `python generate.py …` and
`python -m asciigpt …` work the same way from the repo.

## Usage

### Generate from a prompt

```bash
# Offline procedural backend (default) — deterministic, no network
asciigpt --prompt "a shaded sphere" --preset high-contrast
asciigpt --prompt "a little house" --edges

# Live backend: shell out to any external image generator. The command is a
# template with {prompt} {output} {size}; it must write an image to {output}.
export ASCIIGPT_IMAGE_COMMAND='txt2img --prompt {prompt} --size {size} --out {output}'
asciigpt --prompt "a neon city at dusk" --backend command --format ansi
```

The default **procedural** backend recognises a handful of subjects (sphere,
sun, moon, star, house, tree, mountain, heart, face) and draws a deterministic
abstract composition for anything else — it exists to prove the pipeline
offline, not to be a general artist. For arbitrary prompts, point
`--backend command` at a real generator: a hosted text-to-image API, or the
[`rasterize`](https://github.com/suxrobgm/rasterize) Claude Code plugin
rendering to a file. Design notes live in [`docs/handoffs/`](docs/handoffs/).

### Convert an image

```bash
asciigpt photo.jpg                                   # default ramp, 80 cols
asciigpt photo.jpg --width 120 --preset high-contrast
asciigpt photo.jpg --width 100 --height 50           # fix both dimensions
```

### Gradient presets

```bash
asciigpt --list-presets                              # every preset, with previews
asciigpt portrait.jpg --preset smooth
asciigpt game-screen.png --preset retro-green-screen
```

### Edge-detection mode (outlines)

```bash
asciigpt logo.png --edges                            # Sobel outline:  - | / \
asciigpt photo.jpg --edges --edge-threshold 25       # lower = more edges
```

### Dithering

```bash
asciigpt photo.jpg --dither floyd-steinberg          # default, smooth
asciigpt photo.jpg --dither atkinson                 # crisp, high-contrast
asciigpt photo.jpg --dither ordered                  # screen-printed texture
asciigpt photo.jpg --dither none                     # hard banding
```

### Preprocessing

```bash
asciigpt dark.jpg --brightness 1.4 --contrast 1.3
asciigpt detailed.jpg --sharpness 2.0
asciigpt photo.jpg --gamma 0.7                       # mid-tone lift
asciigpt sketch.jpg --invert                         # dark subject on light ground
asciigpt logo.png --preset max-bw --threshold 128    # hard two-level
```

### Output formats

```bash
asciigpt photo.jpg                                   # plain text (default)
asciigpt photo.jpg --format ansi                     # 24-bit truecolor terminal
asciigpt photo.jpg --format html --background "#0b0b12" -o art.html
```

### Custom glyphs, FIGlet, saving

```bash
asciigpt photo.jpg --chars " .:-=+*#%@"              # your own ramp, dark -> light
asciigpt --text "ZERO PAGE" --font slant             # standalone FIGlet banner
asciigpt photo.jpg --text "RETRO" --text-row 1       # banner stamped on the art
asciigpt photo.jpg -o out.txt                        # write to a file
```

## Gradient presets

ASCII presets are pure printable ASCII (safe in any terminal). Three presets
(`blocks`, `code-page-437`, `arrow`) use Unicode. Run `asciigpt --list-presets`
for the full table with previews.

| Name | Look | Best for |
|------|------|----------|
| `default` | Balanced 10-step | General purpose |
| `high-contrast` | 70-step Paul Bourke ramp | Photographs, max detail |
| `normal` / `normal2` | Classic medium ramps | Photographs |
| `smooth` | Gentle tonal steps | Portraits, faces |
| `grayscale` | Even perceptual steps | Balanced tone |
| `minimalist` / `minimal` | 4–5 levels | Logos, bold graphic look |
| `max-bw` | Two-level on/off | Line art (+ `--threshold`) |
| `mechanical` | Sharp angular glyphs | Machines, buildings |
| `organic` | Soft rounded glyphs | Nature, animals |
| `retro-green-screen` | Chunky phosphor ramp | Pair with `--format ansi` |
| `alphabetic` / `numerical` / `math` | Character-class ramps | Texture/novelty |
| `blocks` / `code-page-437` / `arrow` | Unicode | Pixel-art / DOS / novelty |

## How it works

```
prompt ─▶ image backend ─▶ base image ─┐
                                        │   (or just an image file)
                          image file ───┤
                                        ▼
   resize to char grid ─▶ grayscale ─▶ preprocess ─┐
                                                    │
        ┌───────────────────────────────────────────┘
        ▼
   edges?  ── yes ─▶ Sobel pass ─▶ directional glyphs ( - | / \ ) ─┐
        │                                                          │
        └─ no ─▶ dither ─▶ level indices ─▶ map onto ramp ─────────┤
                                                                   ▼
                                              render: text / ANSI / HTML
```

Generation and conversion share one engine: the **only** difference is where
the image comes from. A prompt is turned into a base image by a pluggable
`ImageBackend`; an image file is loaded directly. From there the deterministic
converter does the rest — luminance maps each cell to a ramp character (dither
breaks up banding), while edge mode ignores the ramp and draws an outline whose
glyphs follow the Sobel gradient direction.

## Examples

The [`examples/`](examples/) directory holds real, reproducible CLI output
(regenerate with `python examples/make_examples.py`):

| File | From | How |
|------|------|-----|
| `prompt_house_edges.txt` | `--prompt "a little house"` | generated, edge mode |
| `prompt_sphere.txt` | `--prompt "a shaded sphere"` | generated, `high-contrast` ramp |
| `sphere.txt` | `sphere.png` | converted, `high-contrast` + Floyd–Steinberg |
| `house_edges.txt` | `house.png` | converted, edge mode |
| `house.html` | `house.png` | converted, truecolor HTML |
| `banner.txt` | `--text asciigpt` | FIGlet banner |

## Roadmap

- **A live backend for real prompts** — wire a hosted text-to-image API (cost
  absorbed server-side) or the `rasterize` plugin into `--backend command`.
- **retrogaze integration** — ship as a free companion to the SaaS.
- **Packaging to PyPI** so `pip install asciigpt` just works.
- **AI-guided glyph selection** — the original "GPT" idea as a quality layer:
  pick glyphs that preserve edges/texture instead of mapping luminance blindly.

See [`tasks.md`](tasks.md) for the full backlog.

## Code tour

asciigpt is a small, readable package under [`asciigpt/`](asciigpt/):

| Module | Responsibility |
|--------|----------------|
| `generate.py` | Prompt → image → ASCII: pluggable backends + `prompt_to_ascii` |
| `gradients.py` | Named character ramps (`--preset`) |
| `preprocess.py` | Pillow stack: resize, grayscale, brightness/contrast/sharpness/gamma/invert/threshold |
| `dither.py` | Floyd–Steinberg, ordered, Atkinson, none |
| `edges.py` | Sobel edge detection + directional glyphs |
| `render.py` | text / ANSI / HTML serialisers |
| `figlet.py` | FIGlet banners and overlay compositing |
| `convert.py` | The pipeline that wires it together (`image_to_ascii`) |
| `cli.py` | argparse front end |

`generate.py` at the repo root is a thin shim that forwards to `cli.py`.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

The suite (94 tests) covers gradient presets, glyph/level mapping, all four
dithering algorithms, edge-mode glyph direction, the renderers, the generation
backends (procedural determinism + the external-command path), and CLI parsing
plus end-to-end conversions — using small images generated on the fly, so no
binary fixtures are needed.

## License

[MIT](LICENSE) © 2026 Ray Weiss.

## Acknowledgements

Built on the shoulders of the tools it learned from — `jp2a`, `libcaca` /
`img2txt`, and [asciiart.eu](https://www.asciiart.eu/image-to-ascii) — and
powered by [Pillow](https://python-pillow.org/) and
[pyfiglet](https://github.com/pwaller/pyfiglet). The live-generation path pairs
naturally with [`rasterize`](https://github.com/suxrobgm/rasterize).
