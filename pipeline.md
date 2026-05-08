# asciigpt — Pipeline Design

> Phase 3. How inputs become ASCII art. The data flow, the decisions,
> and where the AI sits in the loop.

---

## Input Types

asciigpt accepts two primary input modes, which can be combined:

| Mode | Flag | Input | AI Role |
|------|------|-------|---------|
| Prompt | `--prompt "..."` | Natural language description | Generates the entire composition |
| Image | `--image photo.jpg` | Image file (PNG, JPEG, GIF, BMP, WebP) | Guides glyph selection and composition |
| Hybrid | `--prompt "..." --image ref.jpg` | Both | Uses image as style/anatomy reference for prompt generation |

---

## Pipeline Overview

```
┌──────────────┐     ┌──────────────────┐     ┌───────────────┐
│   Input      │────▶│   Generation      │────▶│   Output      │
│  (prompt or  │     │  (LLM or hybrid   │     │  (terminal,   │
│   image)     │     │   converter)      │     │   file, etc.) │
└──────────────┘     └──────────────────┘     └───────────────┘
```

---

## Path A: Prompt → ASCII (the marquee feature)

```
User prompt
    │
    ▼
┌─────────────────────────────────┐
│ 1. Prompt Engineering           │
│    - Wrap in system prompt      │
│    - Add dimension constraints  │
│    - Add style/character set    │
│    - Add quality guidelines     │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 2. DeepSeek API Call            │
│    - Model: deepseek-chat       │
│    - Temperature: 0.7 (creative │
│      but coherent)              │
│    - Max tokens: ~4K (enough    │
│      for ~80x25 art)            │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 3. Post-processing              │
│    - Trim leading/trailing      │
│      whitespace                 │
│    - Validate dimensions        │
│    - Optionally apply dither    │
│    - Optionally add border      │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 4. Output                       │
│    - Print to terminal          │
│    - Write to file (.txt)       │
│    - Copy to clipboard          │
└─────────────────────────────────┘
```

### System prompt design (critical)

The LLM prompt is the secret sauce. Key elements:

```
You are an ASCII art generator. Given a description, produce
high-quality ASCII art using only printable characters.

Rules:
- Output ONLY the ASCII art. No explanations, no markdown fences.
- Width: {width} characters. Height: {height} lines (if specified).
- Use characters that create clear contrast and depth.
- Prefer these characters for shading (light→dark): .'`^",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$
- For subjects with curves, use: / \ ( ) { } [ ] ~ - _ , .
- For sharp edges and mechanical subjects, use: + | - = # * @
- Preserve the silhouette/outline. Interior detail is secondary.
- The art should look intentional, like vintage console box art.
```

### What the AI does that deterministic tools can't

- **Understands composition.** "Airships in the sky, city burning below" →
  the AI places airships at the top, flames and buildings at the bottom.
- **Chooses subject-appropriate glyphs.** Curved lines for organic shapes,
  straight pipes and brackets for machinery.
- **Preserves subject hierarchy.** The main subject gets detail; background
  elements get lower-density treatment.
- **Creates depth.** Darker characters for shadows, lighter for highlights.

---

## Path B: Image → ASCII (hybrid converter)

```
Image file
    │
    ▼
┌─────────────────────────────────┐
│ 1. Image Loading (Pillow)       │
│    - Open PNG/JPEG/GIF/BMP/WebP │
│    - Detect format, color mode  │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 2. Preprocessing                │
│    - Resize to target dims      │
│      (width × height in chars)  │
│    - Convert to grayscale       │
│    - Apply optional adjustments │
│      • Brightness               │
│      • Contrast                 │
│      • Gamma correction         │
│      • Edge detection (Sobel)   │
│      • Sharpness                │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 3. Glyph Mapping               │
│    ┌──────────────────────┐     │
│    │ FAST PATH (default)  │     │
│    │  - Divide image into │     │
│    │    character cells    │     │
│    │  - Compute average    │     │
│    │    luminance per cell │     │
│    │  - Map luminance to   │     │
│    │    glyph via gradient  │     │
│    │    preset             │     │
│    └──────────────────────┘     │
│    ┌──────────────────────┐     │
│    │ AI PATH (--ai)       │     │
│    │  - Send image         │     │
│    │    metadata + sample  │     │
│    │    regions to LLM     │     │
│    │  - LLM recommends     │     │
│    │    glyph strategy:    │     │
│    │    • Which gradient   │     │
│    │      preset to use    │     │
│    │    • Edge glyphs      │     │
│    │    • Fill glyphs      │     │
│    │    • Special regions  │     │
│    │      (faces, text,    │     │
│    │       detailed areas) │     │
│    │  - Apply LLM guidance │     │
│    │    to mapping         │     │
│    └──────────────────────┘     │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 4. Dithering (optional)        │
│    - Floyd-Steinberg (default)  │
│    - Atkinson                   │
│    - Ordered (2x2, 4x4, 8x8)    │
│    - None                       │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 5. Output                       │
│    - Print to terminal          │
│    - Write to file              │
│    - HTML with CSS              │
│    - Copy to clipboard          │
└─────────────────────────────────┘
```

---

## Gradient Presets (character density maps)

Inspired by asciiart.eu's gradient selector. Each preset is an ordered string
of characters from "darkest" (fills the most space) to "lightest".

| Preset | Characters | Best For |
|--------|-----------|----------|
| `default` | `@%#*+=-:. ` | General purpose |
| `high-contrast` | `$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,"^'. ` | Photographs, complex scenes |
| `smooth` | ` .'`^\",:;Il!i><~+_-?][}{1)(\|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$` | Portraits, faces |
| `blocky` | `█▓▒░ ` | Pixel-art style, retro games |
| `mechanical` | `#@%*+|-=:. ` | Machines, robots, industrial |
| `organic` | `@%#*~-:,. ` | Nature, landscapes, animals |
| `minimal` | `@%#* ` | Small output, logos, icons |
| `retro-green` | `@%#*+=-:. ` + green ANSI codes | Terminal nostalgia |

---

## AI-Enhanced Image Pipeline (the hybrid approach)

When `--ai` flag is used with `--image`, the pipeline splits:

### Stage 1: Image Analysis (LLM)
The LLM receives:
- Image dimensions and aspect ratio
- A text description of the image content (the LLM describes what it sees)
- Edge detection map summary
- Luminance histogram

The LLM returns:
- Recommended gradient preset
- Edge handling strategy (which glyphs for which edges)
- Region-specific instructions (e.g., "the face in the top-left needs
  smoother glyphs than the background trees on the right")

### Stage 2: Enhanced Mapping
The deterministic mapper applies the LLM's recommendations:
- Uses the recommended gradient preset
- Applies edge-specific glyph rules
- Uses region masks for area-specific treatment

### Why this works better than pure deterministic
- A photo of a cat vs. a photo of a skyscraper: deterministic treats
  them identically. The AI says "this is fur, use softer curves" vs.
  "these are straight building edges, use pipes and dashes."
- Low-contrast regions: deterministic loses detail. The AI can say
  "boost contrast on the face even if it's technically low-contrast
  — that's the subject."

---

## Output Formats

| Format | Flag | Description |
|--------|------|-------------|
| Terminal | (default) | Print to stdout, optionally with ANSI color codes |
| Text file | `--output art.txt` | Save as plain .txt |
| HTML | `--format html` | HTML document with CSS, matched-width font |
| ANSI | `--format ansi` | ANSI escape codes for color terminals |
| Clipboard | `--clipboard` | Copy directly to system clipboard |

---

## Configuration

API keys and defaults live in environment variables and/or a `.env` file:

```
DEEPSEEK_API_KEY=sk-...        # Required for prompt mode and AI-enhanced image mode
ASCIIGPT_DEFAULT_WIDTH=80       # Default output width in characters
ASCIIGPT_DEFAULT_GRADIENT=default
ASCIIGPT_DEFAULT_DITHER=floyd-steinberg
```

No config file needed for the prototype — env vars are sufficient.

---

## Prototype Scope

For the first working version:

- **Prompt mode:** Works end-to-end. `python generate.py --prompt "..."` →
  ASCII art on stdout. This is the killer feature.
- **Image mode (fast path only):** Deterministic conversion with gradient
  presets and dithering. `python generate.py --image photo.jpg`.
- **AI-enhanced image mode:** Deferred to v2. The fast path + prompt mode
  already differentiate us from every existing tool.
- **Output:** Terminal (default) and file (`--output`). Clipboard and HTML
  deferred to v2.
