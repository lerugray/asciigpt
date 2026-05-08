# asciigpt — Mission

## What

A standalone CLI tool that generates high-quality ASCII art using AI in
the loop. Takes text prompts or source images and produces output that
looks intentional — vintage console box art, not "I ran it through jp2a."

## Why

Existing tools (jp2a, asciicam, libcaca, web converters) do pixel-to-glyph
mapping. They're deterministic, fast, and dull. asciigpt adds an AI layer
that understands composition, depth, and aesthetic intent — the "gpt" in
the name is the point.

## How

- **Command-line first, runs locally.** No browser, no uploads, no SaaS.
- **AI-assisted pipeline.** Prompts go to an LLM (DeepSeek API); images
  get preprocessed then rendered with density-aware glyph selection.
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

- Not a drawing/painting app
- Not a web converter / SaaS
- Not integrated into retrogaze (standalone first)
- Not "just another jp2a wrapper"

## Success

Ray types `python generate.py "steampunk airship over a burning city"`
and gets terminal-ready ASCII art he'd actually want to share.
