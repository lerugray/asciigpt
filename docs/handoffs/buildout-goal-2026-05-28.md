# asciigpt build-out — goal + brief (corrected 2026-05-28)

> **Supersedes the earlier α (prompt→gpt-image-1) draft.** Operator decision
> 2026-05-28: asciigpt makes **real ASCII art, not "drawn" art** — no image
> generation. The working base matches the feature set of the real ASCII-art
> source sites surveyed in `research.md`. The "GPT"/AI is a *later* layer
> (AI-guided glyph selection that enhances real conversion), NOT this goal.

## Vision

asciigpt is a **CLI image→ASCII converter** that matches or beats the
established tools — `jp2a`, `libcaca/img2txt`, `asciiart.eu` — surveyed in
`research.md`. Input is an **image** (and text, for FIGlet banners). Output is
genuine ASCII art produced by real conversion technique (luminance + edge +
dither + glyph mapping), not a generated picture filtered into characters.

It is **not** a prompt→art generator and **not** an LLM-draws-characters tool.
Those were the unreliable paths; they're out of the base. AI-guided glyph
selection (the differentiator that keeps it "asciiGPT") is a documented *next
layer* on top of the deterministic base — explicitly deferred, not in this goal.

## Build on what exists

`generate.py` (~960 lines, single file, well-commented) already has a solid
deterministic image path. **Extend it; don't rewrite from scratch.** Keep it a
readable single file. Read `research.md` "What to adapt" / "What we build on"
sections for the exact feature targets, plus `MISSION.md` / `README.md`.

## Base features (from research.md)

- **Named gradient presets** — asciiart.eu's standout; ~a dozen character-set
  styles selectable by name. "The single best feature to adapt."
- **Preprocessing stack** (Pillow): brightness, contrast, invert, threshold,
  sharpness, gamma.
- **Edge detection with directional glyphs** (`-` `/` `|` `\`) — jp2a's
  `--edges-only` quality bar: a real outline, not a luminance ramp. Sobel pass.
- **Dithering**: Floyd-Steinberg default, plus ordered/Atkinson options.
- **Output formats**: plain text, ANSI truecolor, HTML.
- **CLI flags + custom glyph palette**: jp2a conventions — `--width`/`--height`,
  `--invert`, `--background`, custom `--chars`.
- **FIGlet text overlays** via `pyfiglet` for titles/headers.

Out of scope (research.md non-goals): drawing/editing tools, live webcam/video.

## /goal completion condition (paste-ready)

> **asciigpt is a working CLI image→ASCII converter matching the reference
> tools' base features.** Done when: `python <entrypoint> <image>` converts an
> image to ASCII; named gradient presets (≥ asciiart.eu's set) selectable by
> name; the preprocessing stack works; an edge-detection mode emits directional
> glyphs; Floyd-Steinberg dithering; output as plain text + ANSI color + HTML;
> custom glyph palette + `--width`/`--invert`/`--background`; FIGlet text overlay
> via pyfiglet; tests covering presets / glyph-mapping / dithering / edge / CLI
> parsing all passing; `examples/` has ≥2 committed outputs; README usage
> accurate. **No image generation, no LLM-drawing.** (AI glyph-selection =
> documented next layer, not this goal.)

## End vision

A polished, real ASCII-art CLI good enough to ship as a **free bonus on
retrogaze**.
