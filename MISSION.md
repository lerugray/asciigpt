# asciigpt — Mission

## What

A standalone CLI tool that produces high-quality ASCII art two ways:
**generate** it from a text prompt (make a base image via a pluggable backend,
then convert), or **convert** an existing image. The conversion engine is real
technique — luminance ramps, edge detection, dithering, glyph mapping — with
output that looks intentional, not "I ran it through jp2a." It also renders
FIGlet text banners.

## Why

Existing tools (jp2a, libcaca, asciiart.eu, web converters) each do part
of this well but none do all of it in one CLI-first, runs-local package:
asciiart.eu has the richest preset/preprocessing surface but is browser
only; jp2a has the best edge mode but a weak scaler; libcaca has the most
output formats but no presets. asciigpt unifies the best of each.

The "GPT" in the name is the generative layer: type a prompt, get ASCII art.
The deterministic converter is the engine underneath, and it stands on its
own. Generation is deliberately *not* an LLM typing characters or a bespoke
image model — a prompt becomes a base image through a pluggable backend, and
the converter does the rest (`prompt → image → ASCII`). The output is ASCII.

## How

- **Command-line first, library-first.** Runs locally by default (converter +
  offline procedural backend, no network). A live generation backend may call
  an external service; the retrogaze service absorbs that cost.
- **Deterministic conversion pipeline.** Pillow preprocessing
  (brightness/contrast/sharpness/gamma/invert/threshold) → named gradient
  presets or a Sobel edge mode with directional glyphs → dithering
  (Floyd-Steinberg / ordered / Atkinson) → text / ANSI / HTML output.
- **Output quality over speed.** Glyph choice, edge preservation, and
  density mapping matter more than FPS or file size.

## Reference landscape

| Tool | Category | What we learn |
|------|----------|---------------|
| asciiart.eu/image-to-ascii | Web converter | Dimensions, char sets, UI patterns |
| Nokse22/ascii-draw (429 ★) | Manual sketch tool | Interactive ASCII editing UX |
| jp2a, asciicam, img2txt, libcaca | CLI converters | Baseline quality benchmarks |
| imagetoasciiart.com, convertico.com, codeshack.io | Web converters | Same category as asciiart.eu |

## Constraints

- **Audience:** Ray, a non-programmer game designer. Code must be
  readable and well-commented. Prefer Python.
- **Budget:** Free and offline by default. A live text-to-image backend may be
  a paid API — its cost is absorbed by the retrogaze service, not the end user.
- **Time:** Stolen evening/weekend hours. Ship incrementally.
- **Target:** A tool Ray can actually use for retrogaze, game jams,
  and social posts.

## Non-goals

- Not a drawing/painting app (that's Nokse22/ascii-draw)
- Not a live webcam/video tool (that's asciicam)
- Not an LLM-types-characters tool, and we don't train our own image model;
  generation makes a base image via a pluggable backend, then converts it —
  the output is ASCII art, never a raster image
- Not a web converter / SaaS
- Not "just another jp2a wrapper" — it matches the full reference feature
  set, not just luminance mapping

## Success

Ray types `python generate.py --prompt "a neon city" --format ansi` (or points
it at a photo) and gets terminal-ready ASCII art he'd actually want to share —
good enough to ship as a free companion to the retrogaze SaaS.
