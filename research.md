# asciigpt — Tool Landscape Research

> Phase 2 findings. What exists, what they do well, where they fall short,
> and what's worth adapting into our AI-assisted pipeline.
>
> Drafted 2026-05-07 from prior research. Validation pass 2026-05-18: jp2a and
> libcaca installed and run on macOS, asciicam built from source, asciiart.eu
> and Nokse22/ascii-draw checked against current upstream. What changed in
> that pass is recorded in the Validation Log at the end.

---

## 1. asciiart.eu/image-to-ascii

**Type:** Browser-based web converter (JavaScript + Bootstrap)

### Strengths
- **Rich parameter set.** Characters, Brightness, Contrast, Saturation, Hue,
  Grayscale, Sepia, Invert Colors, Thresholding, Sharpness, and Edge Detection
  — all exposed as sliders. The fullest settings panel I've seen in a free tool.
- **Multiple ASCII gradients.** Around a dozen named character-set styles —
  Alphabetic, Alphanumeric, Arrow, Code Page 437, Extended High, Gray Scale,
  Minimalist, Math Symbols, Normal, Normal 2, Numerical — plus a Max Black and
  White mode. This is the single best feature to adapt: named gradient presets
  the user picks by name.
- **Dithering options.** None, Floyd-Steinberg, Jarvis-Judice-Ninke (JJN),
  Stucki, Atkinson. Four well-known error-diffusion algorithms.
- **Output flexibility.** Copy to clipboard, save as .txt, save as PNG.
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

## 2. Nokse22/ascii-draw (488 ★)

**Type:** Manual sketch/drawing application (Python + GTK4 + libadwaita)

### Strengths
- **Feature-rich drawing.** Rectangle tools (multiple line styles), filled
  rectangles (customizable border/fill chars), freehand brush, line drawing
  (Cartesian, freehand, stepped), text with FIGlet fonts, table creator,
  tree view, eraser, character picker, flood fill.
- **Active community.** 488 stars, 379 commits, regular releases (v1.3.0 in
  Nov 2025), distributed through Flathub and the Snap Store. A healthy project.
- **Good UX patterns.** The tool palette, character picker, and selection
  tools are well-designed. The FIGlet integration is clever.

### Gaps
- **Not a generator.** This is a drawing tool. You manually place characters.
  There's no conversion from images or prompts.
- **Linux only.** GTK4 + libadwaita + GNOME dependency. Won't run on macOS
  (Ray's platform) without significant work.
- **Desktop GUI.** Not embeddable as a library or callable from CLI.

### What to adapt
- **FIGlet integration.** Useful for title cards, headers, and stylized text
  within ASCII art compositions. We can incorporate pyfiglet.
- **Character picker philosophy.** The idea of a curated character set that
  users choose from is good. Our "gradient presets" should follow this model.
- **Selection/move/rotate tools.** If we ever add an interactive mode, this
  is the reference UX.

---

## 3. jp2a (v1.3.3)

**Type:** CLI image-to-ASCII converter (C)

The original `cslarsen/jp2a` (~1k ★) is unmaintained and now points at the
`Talinx/jp2a` fork, which is the live project — v1.3.3, December 2025. The
`--version` string credits Christian Stigen Larsen (2006–2016) and Christoph
Raitzig (2020–2024), so the tool is roughly twenty years old.

### Strengths
- **The baseline everything else is measured against.** Simple, fast, reliable,
  in every Linux package manager and Homebrew.
- **Reads JPEG, PNG, and WebP natively.** The name says "j(peg)2a" but modern
  jp2a is not JPEG-only — confirmed by `jp2a --help` on v1.3.3.
- **Good CLI flags.** `--width` / `--height` / `--size`, `--term-fit` and
  `--term-center` (fit the terminal), `--invert` and `--background=dark|light`,
  `--flipx` / `--flipy`, `--border`, `--output`, and `--chars` for a fully
  custom glyph palette.
- **An edge-detection mode.** `--edges-only` together with `--edge-threshold`
  shades gradients with directional glyphs (`-`, `/`, `|`, `\`). On a test
  image it produced a real outline drawing, not a luminance ramp. jp2a is more
  than pixel-luminance mapping.
- **Output modes.** Plain text, XHTML/HTML (`--html`, `--htmlls`, `--xhtml`,
  with CSS), and ANSI color via `--colors` with `--color-depth` up to 24-bit
  truecolor.
- **URL input is built in.** Pass a URL as an argument (needs libcurl at build
  time) — no separate flag.

### Gaps
- **"Very basic scaling algorithm."** The man page's own words: *"jp2a uses a
  very basic scaling algorithm for every image format except WebP."* Its
  documented workaround is to pipe through WebP: `cwebp -quiet image.jpg -o -
  | jp2a -`. Quality degrades noticeably at low character counts.
- **No content awareness.** jp2a doesn't know what's in the image. A face and
  a landscape get the same luminance-to-glyph treatment. `--edges-only` is
  geometric, not semantic — it finds gradients, not subjects.
- **No prompt-to-art.** Text input is not supported.

### What to adapt
- **CLI flag conventions.** `--width`, `--invert`, `--background` are the de
  facto standard. Match them where they make sense.
- **HTML output mode.** Useful for embedding art in web pages — support it.
- **Custom-palette flag (`--chars`).** Confirms users want to override the
  glyph set. Our named gradient presets are the friendlier version of the
  same idea.
- **Directional edge glyphs.** `--edge-threshold` proves directional glyphs
  along gradients pay off. Our planned Sobel edge pass should feed the same
  kind of `-/|\` glyph selection.
- **Quality benchmark.** jp2a is still the bar for image→ASCII. Our output
  must be noticeably better, especially at low character counts where AI
  glyph selection should shine.

---

## 4. libcaca / img2txt (v0.99.beta20)

**Type:** C library + CLI tool for colored ASCII art conversion

libcaca has shipped as "0.99 beta" for about twenty years (current build dated
Oct 2021). Treat it as stable but in long-term maintenance, not active
development.

### Strengths
- **Broad format support.** PNG, JPEG, GIF, BMP — full support requires
  libcaca built against Imlib2; without it, BMP only.
- **Rich parameter set.** Width, height, font-width, font-height, brightness,
  contrast, gamma, dither.
- **Many output formats.** `img2txt -f` exports twelve: caca, ansi, utf8,
  utf8cr, html, html3, irc, bbfr (BBCode, French), ps (PostScript), svg, tga,
  and troff. The widest output selection of any tool surveyed.
- **Color support.** Generates colored ANSI escape codes by default — even the
  `utf8` format wraps every character in escape codes, not just monochrome.
- **Well-documented.** Clear man page with examples.

### Gaps
- **No AI.** Same pixel-luminance approach as jp2a. Deterministic and simple.
- **C library.** Not directly usable from Python without bindings — we'd shell
  out or use ctypes.
- **Quality ceiling.** Like jp2a, the output reads as "ran through a converter"
  rather than intentional art.

### What to adapt
- **Output format list.** ANSI (terminal), HTML, SVG are the three formats we
  should support. img2txt's `-f` list is a useful checklist of what's possible.
- **Dithering algorithms.** Floyd-Steinberg (`fstein`) as default, with ordered
  (2×2, 4×4, 8×8) and random as options. All implementable in pure Python.
- **Gamma correction.** Often overlooked but important for balancing dark and
  bright images. Include it in preprocessing.

---

## 5. asciicam (muesli/asciicam, 145 ★)

**Type:** Real-time webcam-to-ASCII terminal viewer (Go, MIT). By Christian
Muehlhaeuser (muesli). Roughly 21 commits, no tagged releases — novelty-scale.

### Strengths
- **Real-time.** Converts a live webcam feed to ASCII/ANSI in the terminal at
  speed. The only tool in this survey that handles live video.
- **ANSI color.** `-ansi` for full color, `-color` for a single-color tint.
- **Greenscreen.** `-gen` samples the background to a data directory, then
  `-greenscreen` subtracts it from the live feed — a virtual greenscreen
  rendered in ASCII. Genuinely clever.
- **Tiny footprint.** A single self-contained Go binary, few dependencies.

### Gaps
- **Linux only — and it enforces it.** Built from source with Go 1.26 and run
  on macOS, the binary prints `asciicam only works on Linux` and exits. It
  reads Video4Linux device nodes (`-dev /dev/video0`), which macOS has no
  equivalent of. Ray is on macOS — he cannot run asciicam at all.
- **Not a converter.** Webcam frames only. There is no image-file input; you
  cannot point it at a photo.
- **Not a generator.** No prompt input, no AI, no composition.
- **Novelty-scale.** ~21 commits, no releases — closer to a demo of muesli's
  video/termenv libraries than a maintained tool.

### What to adapt
- **Little to nothing.** asciicam sits in a category asciigpt does not target.
  Live webcam capture is the same kind of out-of-scope as the drawing tools —
  asciigpt converts images and generates from prompts; it is not a video tool.
- **One transferable note:** asciicam has to convert each frame fast enough for
  video. That's a reminder to keep the deterministic image path cheap — though
  asciigpt deliberately trades speed for quality, so it's a low-priority lesson.
- `-ansi` is one more data point that color output is expected; already planned
  for v2.
- **Net:** asciicam is a boundary marker, not a parts donor. It shows where
  asciigpt's scope ends.

---

## 6. Other web converters

(imagetoasciiart.com, convertico.com, codeshack.io, asciiartgenerator.app)

All follow the same pattern as asciiart.eu: browser upload → convert →
download. Some have fewer settings, some have more. None have an AI layer.
None have CLI access. These are not competitive differentiators — they
validate that the market exists but is served by cookie-cutter tools.

---

## Summary: The Gap

| Capability | jp2a | libcaca | asciiart.eu | Nokse22 | asciicam | **asciigpt** |
|---|---|---|---|---|---|---|
| Image → ASCII | ✅ | ✅ | ✅ | ❌ | ❌ (webcam) | ✅ |
| Prompt → ASCII | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| AI glyph selection | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Content awareness | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| CLI-first | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| Edge detection | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Drawing/editing | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ (non-goal) |
| Gradient presets | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Dithering options | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Color output | ✅ truecolor | ✅ | ❌ | ❌ | ✅ | ✅ |
| Live video | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ (non-goal) |

### The unique value proposition

No existing tool takes a text prompt and produces ASCII art through an AI
pipeline. The entire landscape is pixel-luminance-to-glyph mapping — fast,
deterministic, and mechanically blind to image content. jp2a's `--edges-only`
is the closest anyone comes to structure-aware output, and it is still pure
geometry.

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

---

## Validation Log

The 2026-05-07 draft was written from prior research. This pass (2026-05-18)
checked it against the actual tools.

**Installed and run on macOS (Darwin 25.4):**
- `jp2a 1.3.3` — installed via Homebrew. Ran `jp2a --help`, `man jp2a`, and
  conversions of a generated test image at several widths and with
  `--edges-only`.
- `img2txt` (libcaca `0.99.beta20`) — installed via Homebrew. Ran `--help`
  and conversions with `fstein` and `none` dithering.
- `asciicam` (muesli/asciicam) — built from source with Go 1.26. The binary
  refuses to run on macOS (`asciicam only works on Linux`); flags were
  confirmed from the Go source instead.

**Checked against current upstream (cannot be run on this machine):**
- asciiart.eu/image-to-ascii — browser tool; settings and gradient list
  confirmed live.
- Nokse22/ascii-draw — Linux/GTK4 desktop app; repo metadata confirmed live.

**Corrections made to the 2026-05-07 draft:**
- jp2a is **not JPEG-only** — v1.3.3 reads JPEG, PNG, and WebP natively.
- jp2a has an **edge-detection mode** (`--edges-only` + `--edge-threshold`)
  with directional glyphs. The draft missed it and described jp2a as purely
  luminance-based.
- jp2a supports **24-bit truecolor** (`--color-depth=24`); the draft's
  comparison table marked its color support "Partial."
- Removed a non-existent `jp2a --curl` flag — URL input is a plain argument.
- libcaca's `img2txt` exports **twelve** formats (caca, ansi, utf8, utf8cr,
  html, html3, irc, bbfr, ps, svg, tga, troff); the draft listed eight.
- Nokse22/ascii-draw star count refreshed (429 → 488).
- asciiart.eu gradient-style names corrected to the current set.
- **Added section 5, asciicam** — it was named in the task scope but missing
  from the draft entirely.
