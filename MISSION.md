# asciigpt — Mission

## What

A standalone CLI tool that converts images into high-quality ASCII art
through real conversion technique — luminance ramps, edge detection,
dithering, and glyph mapping — with output that looks intentional, not
"I ran it through jp2a." It also renders FIGlet text banners.

## Why

Existing tools (jp2a, libcaca, asciiart.eu, web converters) each do part
of this well but none do all of it in one CLI-first, runs-local package:
asciiart.eu has the richest preset/preprocessing surface but is browser
only; jp2a has the best edge mode but a weak scaler; libcaca has the most
output formats but no presets. asciigpt unifies the best of each.

The "GPT" in the name points at a planned *future* layer — AI-guided glyph
selection that enhances the deterministic conversion. That layer is not
part of the base tool; the base is honest, deterministic conversion that
stands on its own.

## How

- **Command-line first, runs locally.** No browser, no uploads, no SaaS,
  no network calls.
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
- **Budget:** DeepSeek API (essentially free at current usage) or
  Cursor flat-rate. No paid external services.
- **Time:** Stolen evening/weekend hours. Ship incrementally.
- **Target:** A tool Ray can actually use for retrogaze, game jams,
  and social posts.

## Non-goals

- Not a drawing/painting app (that's Nokse22/ascii-draw)
- Not a live webcam/video tool (that's asciicam)
- Not a prompt-to-image generator, and not an LLM-draws-characters tool
- Not a web converter / SaaS
- Not "just another jp2a wrapper" — it matches the full reference feature
  set, not just luminance mapping

## Success

Ray types `python generate.py photo.jpg --preset high-contrast` and gets
terminal-ready ASCII art he'd actually want to share — good enough to ship
as a free bonus on retrogaze.
