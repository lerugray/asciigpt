# asciigpt

**AI-assisted ASCII art generator — CLI first, runs local.**

```
python generate.py --prompt "steampunk airship over a burning city"
```

Takes text prompts or source images and produces ASCII art that looks
intentional — like vintage console box art, not "I ran it through jp2a."

## What makes this different

- **Prompt → art generation.** Describe what you want in natural language
  and the DeepSeek LLM composes the art. No other ASCII tool does this.
- **Image → ASCII conversion.** Fast, offline, with gradient presets,
  dithering, edge detection — everything jp2a/libcaca do, plus some.
- **Hybrid mode.** Use an image as a style reference for prompt generation.
- **Glyph quality focus.** Curated character density maps that make output
  look intentional, not mechanical.

## Quick start

```bash
# 1. Clone and enter
cd asciigpt

# 2. Set up a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key (for prompt mode)
export DEEPSEEK_API_KEY=sk-your-key-here
# Get a key: https://platform.deepseek.com/api_keys

# 5. Generate something
python generate.py --prompt "a dragon breathing fire over a castle"
```

## Usage

### Prompt mode (requires API key)

```bash
# Basic generation
python generate.py --prompt "a lone wolf howling at the moon"

# Constrain the width
python generate.py --prompt "pixel art cat" --width 40

# Add style guidance
python generate.py --prompt "robot factory" --style "sharp industrial lines, heavy contrast"

# Adjust creativity (0.0 = precise, 1.0 = wild)
python generate.py --prompt "abstract shapes" --temperature 0.9
```

### Image mode (no API key needed)

```bash
# Basic conversion
python generate.py --image photo.jpg

# Choose a gradient preset
python generate.py --image portrait.jpg --gradient smooth

# Edge detection (good for line art)
python generate.py --image logo.png --edges

# Invert colors (dark ↔ light)
python generate.py --image sketch.jpg --invert

# Dithering control
python generate.py --image photo.jpg --dither none

# Adjust brightness/contrast
python generate.py --image dark-photo.jpg --brightness 1.5 --contrast 1.3

# Custom width
python generate.py --image photo.jpg --width 120
```

### Hybrid mode

```bash
# Use an image as a composition/style reference for a prompt
python generate.py --prompt "a warrior" --image warrior-sketch.jpg
```

### Save to file

```bash
python generate.py --prompt "dragon" --output dragon.txt
```

### See available gradients

```bash
python generate.py --list-gradients
```

## Gradient presets

| Name | Look | Best for |
|------|------|----------|
| `default` | Balanced @%#*+=- | General purpose |
| `high-contrast` | 70-level detailed | Photographs |
| `smooth` | Reversed, soft | Portraits, faces |
| `mechanical` | Sharp pipes/dashes | Machines, buildings |
| `organic` | Soft curves | Nature, animals |
| `minimal` | 4 levels | Small output, logos |
| `blocky` | Unicode █▓▒░ | Pixel-art style |

Add custom presets: open `generate.py` and add a string to `GRADIENT_PRESETS`.

## How it works

```
┌──────────┐     ┌──────────────┐     ┌────────┐
│  Input   │────▶│  Generation  │────▶│ Output │
└──────────┘     └──────────────┘     └────────┘

Prompt path:  prompt → LLM (DeepSeek) → post-process → print
Image path:   image → resize/grayscale → luminance → glyph map → print
```

The prompt path sends your description to DeepSeek's API with a carefully
crafted system prompt that instructs the model to produce high-quality ASCII
art. The model understands composition, depth, and subject hierarchy — it
places elements intentionally, not mechanically.

The image path uses Pillow for preprocessing (resize, grayscale, optional
edge detection) then maps pixel luminance to characters via gradient presets,
optionally applying Floyd-Steinberg dithering for smoother transitions.

## Code tour

`generate.py` is a single, well-commented file (~880 lines) with 12 clearly
labeled sections. You can read it top to bottom:

1. **Configuration** — API keys, defaults, constants
2. **Gradient Presets** — named character density maps (add yours here)
3. **DeepSeek API Client** — sends prompts, parses responses
4. **Prompt Engineering** — the "secret sauce" system prompt
5. **Prompt → ASCII** — the marquee feature
6. **Image Preprocessing** — resize, grayscale, adjustments
7. **Glyph Mapping** — luminance → character
8. **Floyd-Steinberg Dithering** — smooth gradient transitions
9. **Image → ASCII** — the full conversion pipeline
10. **Output** — terminal or file
11. **CLI** — argparse interface
12. **Main** — orchestrator

## Dependencies

- `requests` — HTTP client for the DeepSeek API
- `Pillow` — image loading and processing

Both are in `requirements.txt`. Install with `pip install -r requirements.txt`.

## Configuration

Set environment variables (or copy `.env.example` to `.env`):

- `DEEPSEEK_API_KEY` — required for prompt mode
- `ASCIIGPT_DEFAULT_WIDTH` — default output width (default: 80)

## Project docs

- `MISSION.md` — why this exists and what success looks like
- `tasks.md` — prioritized backlog
- `research.md` — competitive landscape analysis
- `pipeline.md` — detailed pipeline design

## What's next (v0.2+)

- AI-enhanced image mode (LLM-guided glyph selection)
- HTML output for embedding in web pages
- Clipboard support (`--clipboard`)
- Batch mode (process multiple images)
- FIGlet integration for title cards
- ANSI color output
