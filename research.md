# asciigpt — Tool Landscape Research

> Phase 2 findings. What exists, what they do well, where they fall short,
> and what's worth adapting into our AI-assisted pipeline.

---

## 1. asciiart.eu/image-to-ascii

**Type:** Browser-based web converter (JavaScript + Bootstrap)

### Strengths
- **Rich parameter set.** Characters count, brightness, contrast, saturation,
  hue, grayscale, sepia, invert, thresholding, sharpness, and edge detection
  — all exposed as sliders. This is the most comprehensive settings panel
  I've seen in a free tool.
- **Multiple ASCII gradients.** 12 gradient styles including Alphabetic,
  Alphanumeric, Code Page 437, High Gray Scale, Math Symbols, Numerical,
  Max Black and White, and Space Density. This is the single best feature
  to steal — named gradient presets that users can switch between.
- **Dithering options.** None, Floyd-Steinberg, Jarvis-Judice-Ninke (JJN),
  Stucki, Atkinson. Four well-known error-diffusion algorithms.
- **Output flexibility.** Copy to clipboard, save as .txt, save as PNG.
  Transparent frame option for presentation.
- **Free for any use.** No attribution required. Commercial friendly.

### Gaps
- **Browser only.** No CLI, no API, no automation. Every conversion is manual
  upload → fiddle sliders → download.
- **No AI layer.** Pure pixel-to-glyph mapping. The gradient presets are
  static — they don't adapt to image content.
- **Closed source.** We can observe behavior but can't see the algorithm.
  The gradient strings and dithering are standard techniques we can
  replicate, but the exact implementation is a black box.

### What to adapt
- **Gradient preset concept.** Define named character sets (e.g. "high-contrast",
  "smooth", "retro-green-screen") that users select by name. The AI can also
  recommend or auto-select based on image content.
- **Parameter surface.** The brightness/contrast/sharpness/edge-detection
  pipeline is the right preprocessing stack. We'll implement it server-side
  with PIL/Pillow.
- **Dithering library.** We should include at least Floyd-Steinberg as a
  post-processing option.

---

## 2. Nokse22/ascii-draw (429 ★)

**Type:** Manual sketch/drawing application (Python + GTK4 + libadwaita)

### Strengths
- **Feature-rich drawing.** Rectangle tools (multiple line styles), filled
  rectangles (customizable border/fill chars), freehand brush, line drawing
  (Cartesian, freehand, stepped), text with FIGlet fonts, table creator,
  tree view, eraser, character picker, flood fill.
- **Active community.** 429 stars, 377 commits, Matrix chat room. Healthy
  project with regular releases (v1.3.0 in Nov 2025).
- **Good UX patterns.** The tool palette, character picker, and selection
  tools are well-designed. The FIGlet integration is clever.

### Gaps
- **Not a generator.** This is a drawing tool. You manually place characters.
  There's no conversion from images or prompts.
- **Linux only.** GTK4 + GNOME dependency. Won't run on macOS (Ray's platform)
  without significant work.
- **Desktop GUI.** Not embeddable as a library or callable from CLI.

### What to adapt
- **FIGlet integration.** Useful for title cards, headers, and stylized text
  within ASCII art compositions. We can incorporate pyfiglet.
- **Character picker philosophy.** The idea of a curated character set that
  users choose from is good. Our "gradient presets" should follow this model.
- **Selection/move/rotate tools.** If we ever add an interactive mode, this
  is the reference UX.

---

## 3. jp2a (1k ★)

**Type:** CLI JPEG-to-ASCII converter (C)

### Strengths
- **The gold standard for baseline quality.** 1k stars, 499 commits, 19 years
  of development. Simple, fast, reliable.
- **Good CLI flags.** `--width`, `--height`, `--colors`, `--html`, `--term-fit`,
  `--background`, `--invert`, `--flip`, `--curl` for URL fetching.
- **Output modes.** Plain text, HTML (with CSS), colored ANSI terminal output.
- **Widely available.** In every Linux package manager. The reference that
  other tools are measured against.

### Gaps
- **JPEG only** (by name and primary function). The man page says you can
  pipe through ImageMagick `convert`, but native format support is limited.
- **"Very basic scaling algorithm."** The man page itself admits this for
  non-WebP formats. Quality degrades noticeably at low character counts.
- **No content awareness.** jp2a doesn't know what's in the image. A face
  and a landscape get the same pixel-luminance-to-glyph treatment.
- **No prompt-to-art.** Text input not supported.

### What to adapt
- **CLI flag conventions.** The `--width`, `--invert`, `--background` flags
  are the de facto standard. We should match them where they make sense.
- **HTML output mode.** Useful for embedding art in web pages. We should
  support this as an output format.
- **Quality benchmark.** We'll compare our image-to-ascii output against
  jp2a's output and the bar is: must be noticeably better, especially at
  low character counts where AI glyph selection shines.

---

## 4. libcaca / img2txt

**Type:** C library + CLI tool for colored ASCII art conversion

### Strengths
- **Broad format support.** PNG, JPEG, GIF, BMP (via Imlib2).
- **Rich parameter set.** Width, height, font-width, font-height, brightness,
  contrast, gamma, dither (none, ordered2/4/8, random, Floyd-Steinberg).
- **Many output formats.** ANSI, UTF8, HTML, SVG, PostScript, IRC, BBCode, TGA.
  This is the widest output format selection of any tool surveyed.
- **Color support.** Generates colored ANSI escape codes, not just monochrome.
- **Well-documented.** Clear man page with examples.

### Gaps
- **No AI.** Same pixel-luminance approach as jp2a. Deterministic and simple.
- **C library.** Not directly usable from Python without bindings. We'd have
  to shell out or use ctypes.
- **Quality ceiling.** Like jp2a, the output looks like "I ran it through a
  converter" rather than intentional art.

### What to adapt
- **Output format list.** ANSI (terminal), HTML, SVG are the three formats
  we should support. The img2txt format list is an excellent checklist.
- **Dithering algorithms.** Floyd-Steinberg as default, with ordered and
  random as options. We can implement these in pure Python.
- **Gamma correction.** Often overlooked but important for dark/bright image
  balancing. We should include it in our preprocessing.

---

## 5. Other web converters

(imagetoasciiart.com, convertico.com, codeshack.io, asciiartgenerator.app)

All follow the same pattern as asciiart.eu: browser upload → convert →
download. Some have fewer settings, some have more. None have an AI layer.
None have CLI access. These are not competitive differentiators — they
validate that the market exists but is served by cookie-cutter tools.

---

## Summary: The Gap

| Capability | jp2a | libcaca | asciiart.eu | Nokse22 | **asciigpt** |
|---|---|---|---|---|---|
| Image → ASCII | ✅ | ✅ | ✅ | ❌ | ✅ |
| Prompt → ASCII | ❌ | ❌ | ❌ | ❌ | ✅ |
| AI glyph selection | ❌ | ❌ | ❌ | ❌ | ✅ |
| Content awareness | ❌ | ❌ | ❌ | ❌ | ✅ |
| CLI-first | ✅ | ✅ | ❌ | ❌ | ✅ |
| Drawing/editing | ❌ | ❌ | ❌ | ✅ | ❌ (non-goal) |
| Gradient presets | ❌ | ❌ | ✅ | ❌ | ✅ |
| Dithering options | ❌ | ✅ | ✅ | ❌ | ✅ |
| Color output | Partial | ✅ | ❌ | ❌ | ✅ |

### The unique value proposition

No existing tool takes a text prompt and produces ASCII art through an AI
pipeline. The entire landscape is pixel-luminance-to-glyph mapping — fast,
deterministic, and mechanically blind to image content.

asciigpt's differentiation is:
1. **Prompt → art.** "Steampunk airship over a burning city" — the LLM
   understands composition, depth, subject hierarchy, and aesthetic intent.
2. **AI-guided glyph selection.** Instead of `char = gradient[luminance]`,
   the AI chooses glyphs that preserve edges, create texture, and respect
   the subject's visual character.
3. **Hybrid pipeline.** Images get conventional preprocessing (resize,
   grayscale, edge detection) then AI-enhanced rendering. The best of both
   worlds: speed where deterministic methods work, intelligence where they
   don't.

### What we build on

- **Pillow (PIL)** for image preprocessing — the standard Python imaging
  library, handles resize/grayscale/edge detection/contrast.
- **DeepSeek API** for LLM calls — essentially free at current usage.
- **pyfiglet** for stylized text overlays (from Nokse22's approach).
- **Floyd-Steinberg dithering** in pure Python (trivial to implement).
- **Named gradient presets** as a configuration layer (from asciiart.eu).
