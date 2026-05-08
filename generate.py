#!/usr/bin/env python3
"""
asciigpt — AI-assisted ASCII art generator.

Takes text prompts or source images and produces high-quality ASCII art
via an AI-assisted pipeline. The "gpt" in the name is the point.

Usage:
    # Prompt mode — the marquee feature
    python generate.py --prompt "steampunk airship over a burning city"

    # Image mode — fast deterministic conversion
    python generate.py --image photo.jpg --width 80

    # Hybrid mode — use an image as a style reference for a prompt
    python generate.py --prompt "a lone astronaut" --image space.jpg

    # Save to file
    python generate.py --prompt "dragon" --output dragon.txt

Dependencies: pip install requests pillow
"""

import argparse
import os
import sys
import json
import math
from io import BytesIO

# ---------------------------------------------------------------------------
# Dependency checks — these are optional, with helpful error messages
# ---------------------------------------------------------------------------

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: Configuration
# ═══════════════════════════════════════════════════════════════════════════

# --- API settings ---
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# --- Default output settings ---
DEFAULT_WIDTH = int(os.environ.get("ASCIIGPT_DEFAULT_WIDTH", "80"))
DEFAULT_HEIGHT = None  # Auto-computed from aspect ratio
CHAR_ASPECT_RATIO = 0.5  # Terminal characters are roughly 2x taller than wide

# --- API call settings ---
API_TEMPERATURE = 0.7      # Creative but coherent
API_MAX_TOKENS = 4096      # Enough for ~80x50 character art
API_TIMEOUT = 60           # Seconds before giving up on the API


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: Gradient Presets (character density maps)
# ═══════════════════════════════════════════════════════════════════════════
#
# Each preset is an ordered string from "darkest" (fills the most visual
# space) to "lightest". Inspired by asciiart.eu's gradient selector.
#
# Ray can add custom presets here — just add a new key to the dict.

GRADIENT_PRESETS = {
    # General purpose — balanced contrast, works for most images
    "default": "@%#*+=-:. ",

    # High detail — the classic "70-level" gradient for photographs
    "high-contrast": (
        "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft"
        "/|()1{}[]?-_+~<>i!lI;:,\"^'. "
    ),

    # Smooth — reverses the order for a different look, good for portraits
    "smooth": (
        " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvcz"
        "XYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
    ),

    # Mechanical — sharp angles, good for robots, buildings, vehicles
    "mechanical": "#@%*+|-=:. ",

    # Organic — soft curves, good for nature, animals, landscapes
    "organic": "@%#*~-:,. ",

    # Minimal — just a few levels for small output or simple subjects
    "minimal": "@%#* ",

    # Blocky — Unicode block characters for pixel-art style
    # (requires terminal with Unicode support)
    "blocky": "\u2588\u2593\u2592\u2591 ",
}


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: DeepSeek API Client
# ═══════════════════════════════════════════════════════════════════════════

def check_api_ready():
    """Verify the API key is set and dependencies are installed.

    Returns (True, "") if everything is ready, or (False, error_message)
    if something is missing.
    """
    if not HAS_REQUESTS:
        return False, "Missing 'requests' library. Install it: pip install requests"
    if not DEEPSEEK_API_KEY:
        return False, (
            "DEEPSEEK_API_KEY environment variable is not set.\n"
            "Get a key from https://platform.deepseek.com/api_keys\n"
            "Then run: export DEEPSEEK_API_KEY=sk-..."
        )
    return True, ""


def call_deepseek_api(system_prompt, user_prompt, temperature=API_TEMPERATURE):
    """Send a prompt to the DeepSeek API and return the response text.

    Args:
        system_prompt: The system-level instructions for the model.
        user_prompt: The user's actual request.
        temperature: Creativity level (0.0 = deterministic, 1.0 = wild).

    Returns:
        The model's response text.

    Raises:
        RuntimeError: If the API call fails (network error, auth error, etc.)
    """
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": API_MAX_TOKENS,
        "stream": False,
    }

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"API request timed out after {API_TIMEOUT} seconds. "
            "The model might be overloaded — try again in a moment."
        )
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Could not connect to the DeepSeek API. Check your internet connection."
        )
    except requests.exceptions.HTTPError as e:
        # Try to extract a useful error message from the response
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", str(e))
        except Exception:
            error_msg = str(e)
        raise RuntimeError(f"API error: {error_msg}")

    # Parse the response
    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(
            f"Unexpected API response format. Got: {json.dumps(data, indent=2)[:500]}"
        )

    return content


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: Prompt Engineering
# ═══════════════════════════════════════════════════════════════════════════

def build_system_prompt(width=DEFAULT_WIDTH, height=None, gradient="default",
                         style_hint=None):
    """Build the system prompt that instructs the LLM how to generate ASCII art.

    This is the "secret sauce" — the prompt that makes the LLM produce
    high-quality, intentional-looking ASCII art instead of random characters.

    Args:
        width: Target width in characters.
        height: Target height in lines (None = let the model decide).
        gradient: Which character set to prefer.
        style_hint: Optional extra guidance like "use sharp mechanical lines".

    Returns:
        A system prompt string.
    """
    dims = f"{width} characters wide"
    if height:
        dims += f" and {height} lines tall"
    dims += "."

    # The character palette we recommend to the model
    palette = (
        " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvcz"
        "XYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
    )

    prompt = f"""You are an ASCII art generator. Given a description, produce
high-quality ASCII art using only printable ASCII characters.

CRITICAL RULES:
- Output ONLY the ASCII art itself. No markdown fences (no ```), no
  explanations before or after, no "Here is your art:" — just the art.
- The art should be approximately {dims}
- Use characters that create clear contrast, depth, and texture.
- This palette creates good shading (lightest→darkest):
  {palette}
- For subjects with curves (animals, people, nature), prefer:
  / \\ ( ) {{ }} [ ] ~ - _ , . ' `
- For sharp edges and mechanical subjects (buildings, machines, robots),
  prefer: + | - = # * @
- Preserve the silhouette/outline of the subject. Interior detail is
  secondary to a recognizable shape.
- Create depth by using darker characters (#@$) for shadows and lighter
  characters (. '`) for highlights.
- The art should look intentional — like vintage computer box art or
  a carefully composed BBS ASCII — not like a mechanical conversion."""

    if style_hint:
        prompt += f"\n\nSTYLE GUIDANCE: {style_hint}"

    return prompt


def build_user_prompt(description, width=DEFAULT_WIDTH, height=None):
    """Build the user-facing prompt from the user's description.

    Args:
        description: What the user wants (e.g. "a dragon breathing fire").
        width: Target width hint.
        height: Target height hint.

    Returns:
        A user prompt string.
    """
    prompt = f"Generate ASCII art of: {description}"

    if width:
        prompt += f"\nWidth: approximately {width} characters."
    if height:
        prompt += f"\nHeight: approximately {height} lines."

    return prompt


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: Prompt → ASCII Generation (the marquee feature)
# ═══════════════════════════════════════════════════════════════════════════

def generate_from_prompt(description, width=DEFAULT_WIDTH, height=None,
                          gradient="default", style_hint=None,
                          temperature=API_TEMPERATURE):
    """Generate ASCII art from a text description using the DeepSeek LLM.

    This is the killer feature — no other ASCII art tool does this.

    Args:
        description: Natural language description of the desired art.
        width: Target width in characters.
        height: Target height (None = auto).
        gradient: Gradient preset name for character preferences.
        style_hint: Extra style guidance for the model.
        temperature: Model creativity level.

    Returns:
        A string containing the generated ASCII art.
    """
    ready, error = check_api_ready()
    if not ready:
        raise RuntimeError(error)

    print(f"🎨 Generating ASCII art for: \"{description}\"", file=sys.stderr)
    print(f"   Width: {width} chars | Model: {DEEPSEEK_MODEL}", file=sys.stderr)

    system_prompt = build_system_prompt(width, height, gradient, style_hint)
    user_prompt = build_user_prompt(description, width, height)

    print("   Calling DeepSeek API...", file=sys.stderr)
    raw_art = call_deepseek_api(system_prompt, user_prompt, temperature)

    # Post-process: strip any markdown fences the model might have added
    art = clean_llm_output(raw_art)

    print(f"   Done! Generated {len(art)} characters.", file=sys.stderr)
    return art


def clean_llm_output(text):
    """Strip markdown fences, leading/trailing whitespace, and other
    common LLM output artifacts from the generated art.

    The model sometimes wraps output in ``` fences or adds explanatory
    text despite being told not to. This function cleans that up.
    """
    lines = text.split("\n")

    # Remove leading and trailing lines that look like markdown fences
    while lines and (lines[0].strip().startswith("```") or
                     lines[0].strip().lower().startswith("here")):
        lines.pop(0)
    while lines and (lines[-1].strip().startswith("```") or
                     lines[-1].strip() == ""):
        lines.pop()

    # Remove leading/trailing blank lines
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: Image Preprocessing
# ═══════════════════════════════════════════════════════════════════════════

def load_and_preprocess(image_path, width=DEFAULT_WIDTH, height=None,
                         brightness=1.0, contrast=1.0, gamma=1.0,
                         edge_detection=False, invert=False,
                         char_aspect=CHAR_ASPECT_RATIO):
    """Load an image and prepare it for ASCII conversion.

    Steps:
    1. Open the image (any format Pillow supports).
    2. Resize to the target character dimensions, accounting for the
       fact that terminal characters are taller than they are wide.
    3. Convert to grayscale.
    4. Apply optional adjustments (brightness, contrast, gamma).
    5. Optionally detect edges for sharper output.
    6. Optionally invert colors (light ↔ dark).

    Args:
        image_path: Path to the image file.
        width: Target width in characters.
        height: Target height in characters (None = auto from aspect ratio).
        brightness: Brightness multiplier (1.0 = no change).
        contrast: Contrast multiplier (1.0 = no change).
        gamma: Gamma correction value (1.0 = no change).
        edge_detection: If True, apply Sobel edge detection.
        invert: If True, invert the grayscale values.
        char_aspect: Character aspect ratio (width/height).
                     Terminals are roughly 0.5 (chars are 2x taller than wide).

    Returns:
        A tuple of (PIL Image in grayscale 'L' mode, width, height).
    """
    if not HAS_PIL:
        raise RuntimeError(
            "Missing 'Pillow' library. Install it: pip install Pillow"
        )

    # --- Step 1: Load ---
    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        raise RuntimeError(f"Image file not found: {image_path}")
    except Exception as e:
        raise RuntimeError(f"Could not open image: {e}")

    # --- Step 2: Compute target dimensions ---
    orig_w, orig_h = img.size

    if height is None:
        # Calculate height to preserve aspect ratio, accounting for
        # the fact that terminal characters are ~2x taller than wide
        char_rows = int((orig_h / orig_w) * width * char_aspect)
        # Ensure at least 1 row
        char_rows = max(1, char_rows)
    else:
        char_rows = height

    # Resize the image so each pixel roughly corresponds to one character
    # (we'll average blocks of pixels per character later)
    img = img.resize((width, char_rows), Image.Resampling.LANCZOS)

    # --- Step 3: Convert to grayscale ---
    img = img.convert("L")

    # --- Step 4: Apply adjustments ---
    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if gamma != 1.0:
        # Gamma correction: apply a power-law curve to pixel values
        # PIL doesn't have a built-in gamma, so we do it manually
        pixels = list(img.getdata())
        # Create a lookup table for the gamma curve
        lut = [int(255 * (i / 255.0) ** gamma) for i in range(256)]
        img = img.point(lut)

    # --- Step 5: Edge detection (optional) ---
    if edge_detection:
        # Use FIND_EDGES which is a simple convolution-based edge detector
        # We blend the edges with the original to preserve some interior detail
        edges = img.filter(ImageFilter.FIND_EDGES)
        # Blend: 60% original, 40% edges — keeps subject visible while
        # emphasizing boundaries
        img = Image.blend(img, edges, alpha=0.4)

    # --- Step 6: Invert (optional) ---
    if invert:
        img = ImageOps.invert(img)

    return img, width, char_rows


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: Glyph Mapping (deterministic luminance → character)
# ═══════════════════════════════════════════════════════════════════════════

def map_luminance_to_glyph(luminance, gradient):
    """Map a luminance value (0-255) to a character in the gradient string.

    The gradient is ordered from darkest character (index 0) to lightest
    (index -1). A luminance of 0 (black) maps to the darkest character,
    and 255 (white) maps to the lightest.

    Args:
        luminance: Integer 0-255, where 0 = black, 255 = white.
        gradient: String of characters ordered dark→light.

    Returns:
        A single character from the gradient.
    """
    # Clamp luminance to valid range
    luminance = max(0, min(255, luminance))

    # Map 0-255 to an index in the gradient
    # luminance 0 → index 0 (darkest char)
    # luminance 255 → index len(gradient)-1 (lightest char)
    num_chars = len(gradient)
    index = int((luminance / 255.0) * (num_chars - 1))

    # Clamp to valid range (handles edge cases)
    index = max(0, min(num_chars - 1, index))

    return gradient[index]


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: Floyd-Steinberg Dithering
# ═══════════════════════════════════════════════════════════════════════════

def apply_floyd_steinberg(luminance_grid, gradient):
    """Apply Floyd-Steinberg error diffusion dithering to a luminance grid.

    This reduces the "banding" effect that happens when mapping continuous
    luminance values to a small set of discrete characters. The error
    (difference between actual luminance and the luminance of the chosen
    character) is distributed to neighboring pixels, creating a smoother
    visual result.

    Args:
        luminance_grid: 2D list of luminance values (0-255).
        gradient: The character gradient string for mapping.

    Returns:
        2D list of characters (same dimensions as input).
    """
    rows = len(luminance_grid)
    cols = len(luminance_grid[0]) if rows > 0 else 0

    # Make a mutable copy of the luminance values (we'll modify these)
    grid = [list(row) for row in luminance_grid]
    result = [[" "] * cols for _ in range(rows)]

    for y in range(rows):
        for x in range(cols):
            old_val = grid[y][x]
            new_val = _closest_gradient_luminance(old_val, gradient)
            result[y][x] = map_luminance_to_glyph(new_val, gradient)

            # Calculate the quantization error
            error = old_val - new_val

            # Distribute error to neighboring pixels
            # Floyd-Steinberg weights: 7/16 right, 3/16 bottom-left,
            # 5/16 bottom, 1/16 bottom-right
            if x + 1 < cols:
                grid[y][x + 1] += error * 7 / 16
            if y + 1 < rows:
                if x - 1 >= 0:
                    grid[y + 1][x - 1] += error * 3 / 16
                grid[y + 1][x] += error * 5 / 16
                if x + 1 < cols:
                    grid[y + 1][x + 1] += error * 1 / 16

    return result


def _closest_gradient_luminance(luminance, gradient):
    """Find the luminance value that the given luminance maps to in the
    gradient. Used for computing quantization error in dithering.

    Args:
        luminance: The actual luminance value (0-255).
        gradient: The character gradient.

    Returns:
        The "ideal" luminance value for the mapped character.
    """
    num_chars = len(gradient)
    # Which index does this luminance map to?
    index = int((luminance / 255.0) * (num_chars - 1))
    index = max(0, min(num_chars - 1, index))
    # What luminance does that index represent?
    return int((index / (num_chars - 1)) * 255.0)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 9: Image → ASCII Conversion Pipeline
# ═══════════════════════════════════════════════════════════════════════════

def generate_from_image(image_path, width=DEFAULT_WIDTH, height=None,
                         gradient="default", dither="floyd-steinberg",
                         brightness=1.0, contrast=1.0, gamma=1.0,
                         edge_detection=False, invert=False):
    """Convert an image to ASCII art using deterministic glyph mapping.

    This is the fast, offline path. No API calls — pure Python pixel math.
    Use this when you have an image file and don't need AI enhancement.

    Args:
        image_path: Path to the image file.
        width: Output width in characters.
        height: Output height (None = auto from aspect ratio).
        gradient: Name of the gradient preset to use.
        dither: Dithering algorithm ("floyd-steinberg", "none").
        brightness: Brightness multiplier.
        contrast: Contrast multiplier.
        gamma: Gamma correction.
        edge_detection: Apply Sobel edge detection.
        invert: Invert the grayscale.

    Returns:
        A string containing the ASCII art.
    """
    # --- Validate gradient preset ---
    if gradient not in GRADIENT_PRESETS:
        available = ", ".join(GRADIENT_PRESETS.keys())
        raise ValueError(
            f"Unknown gradient '{gradient}'. Available: {available}"
        )
    char_gradient = GRADIENT_PRESETS[gradient]

    # --- Load and preprocess ---
    print(f"📷 Converting image: {image_path}", file=sys.stderr)
    print(f"   Width: {width} chars | Gradient: {gradient} | "
          f"Dither: {dither}", file=sys.stderr)

    img, img_width, img_height = load_and_preprocess(
        image_path, width, height, brightness, contrast, gamma,
        edge_detection, invert
    )

    # --- Build luminance grid ---
    # Get pixel data as a flat list of values (0-255)
    # Pillow 12+ deprecates getdata() in favor of get_flattened_data()
    try:
        pixels = list(img.get_flattened_data())
    except AttributeError:
        pixels = list(img.getdata())

    # Reshape into a 2D grid: each element is the luminance of one "pixel"
    # (which maps 1:1 to a character since we resized to character dimensions)
    luminance_grid = []
    for y in range(img_height):
        row_start = y * img_width
        row = pixels[row_start:row_start + img_width]
        luminance_grid.append(list(row))

    # --- Apply glyph mapping (with or without dithering) ---
    if dither == "floyd-steinberg":
        char_grid = apply_floyd_steinberg(luminance_grid, char_gradient)
    elif dither == "none":
        char_grid = []
        for row in luminance_grid:
            char_grid.append([
                map_luminance_to_glyph(val, char_gradient)
                for val in row
            ])
    else:
        raise ValueError(
            f"Unknown dithering method '{dither}'. Use 'floyd-steinberg' or 'none'."
        )

    # --- Build output string ---
    lines = ["".join(row) for row in char_grid]
    art = "\n".join(lines)

    print(f"   Done! {img_width}×{img_height} characters.", file=sys.stderr)
    return art


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 10: Output
# ═══════════════════════════════════════════════════════════════════════════

def output_art(art, output_path=None):
    """Output the ASCII art to terminal and/or file.

    Args:
        art: The ASCII art string.
        output_path: If provided, write to this file. Otherwise print to stdout.
    """
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(art)
        print(f"📄 Saved to: {output_path}", file=sys.stderr)
    else:
        print(art)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 11: CLI (command-line interface)
# ═══════════════════════════════════════════════════════════════════════════

def build_parser():
    """Build the argument parser for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="asciigpt — AI-assisted ASCII art generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate.py --prompt "steampunk airship over a burning city"
  python generate.py --prompt "a lone wolf howling at the moon" --width 60
  python generate.py --image photo.jpg
  python generate.py --image logo.png --gradient minimal --width 40
  python generate.py --prompt "dragon" --output dragon.txt
  python generate.py --prompt "robot" --image robot-ref.jpg --output robot.txt

Environment:
  DEEPSEEK_API_KEY    API key for DeepSeek (required for --prompt mode)
  ASCIIGPT_DEFAULT_WIDTH  Default output width (default: 80)
        """,
    )

    # --- Input mode (mutually exclusive group would be ideal, but we
    #     want to allow --prompt + --image for hybrid mode) ---
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        help="Text description of the ASCII art to generate."
    )
    parser.add_argument(
        "--image", "-i",
        type=str,
        help="Path to an image file to convert to ASCII art."
    )

    # --- Output settings ---
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Save the art to a file instead of printing to terminal."
    )
    parser.add_argument(
        "--width", "-w",
        type=int,
        default=DEFAULT_WIDTH,
        help=f"Output width in characters (default: {DEFAULT_WIDTH})."
    )
    parser.add_argument(
        "--height", "-H",
        type=int,
        default=None,
        help="Output height in lines (default: auto from aspect ratio)."
    )

    # --- Style settings ---
    parser.add_argument(
        "--gradient", "-g",
        type=str,
        default="default",
        choices=list(GRADIENT_PRESETS.keys()),
        help="Character density gradient preset."
    )
    parser.add_argument(
        "--dither", "-d",
        type=str,
        default="floyd-steinberg",
        choices=["floyd-steinberg", "none"],
        help="Dithering algorithm for image mode (default: floyd-steinberg)."
    )
    parser.add_argument(
        "--style",
        type=str,
        default=None,
        help="Extra style guidance for the LLM (prompt mode only)."
    )

    # --- Image preprocessing flags ---
    parser.add_argument(
        "--brightness",
        type=float,
        default=1.0,
        help="Brightness multiplier (default: 1.0)."
    )
    parser.add_argument(
        "--contrast",
        type=float,
        default=1.0,
        help="Contrast multiplier (default: 1.0)."
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=1.0,
        help="Gamma correction (default: 1.0)."
    )
    parser.add_argument(
        "--edges",
        action="store_true",
        help="Apply edge detection for sharper output (image mode)."
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert colors (dark ↔ light) (image mode)."
    )

    # --- API settings ---
    parser.add_argument(
        "--temperature",
        type=float,
        default=API_TEMPERATURE,
        help=f"Model creativity level 0.0-1.0 (default: {API_TEMPERATURE})."
    )

    # --- Info ---
    parser.add_argument(
        "--list-gradients",
        action="store_true",
        help="List available gradient presets and exit."
    )

    return parser


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 12: Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = build_parser()
    args = parser.parse_args()

    # --- Info commands ---
    if args.list_gradients:
        print("Available gradient presets:")
        for name, chars in GRADIENT_PRESETS.items():
            # Show the first 20 chars as a preview
            preview = chars[:20] + ("..." if len(chars) > 20 else "")
            print(f"  {name:20s}  {preview}")
        return 0

    # --- Validate: need at least one input ---
    if not args.prompt and not args.image:
        parser.print_help()
        print("\n❌ Error: Provide --prompt or --image (or both).", file=sys.stderr)
        return 1

    # --- Validate dependencies for the chosen mode ---
    if args.image and not HAS_PIL:
        print("❌ Error: Image mode requires Pillow. Install: pip install Pillow",
              file=sys.stderr)
        return 1

    if args.prompt:
        ready, error = check_api_ready()
        if not ready:
            print(f"❌ Error: {error}", file=sys.stderr)
            return 1

    # --- Generate ---
    try:
        if args.prompt and args.image:
            # Hybrid mode: use the image as a style reference for the prompt
            # First, convert the image to get its basic composition
            print("🔀 Hybrid mode: using image as reference for prompt generation.",
                  file=sys.stderr)

            # Generate a text description of the image to feed the LLM
            # (In the prototype, we just pass both and let the LLM decide.
            #  A future version could do image → caption → enhanced prompt.)
            style_hint = args.style or ""
            if args.image:
                style_hint += (
                    f" Reference image: {args.image}. "
                    "Use the composition, lighting, and proportions from "
                    "this image as a guide."
                )

            art = generate_from_prompt(
                description=args.prompt,
                width=args.width,
                height=args.height,
                gradient=args.gradient,
                style_hint=style_hint,
                temperature=args.temperature,
            )

        elif args.prompt:
            # Pure prompt mode — the marquee feature
            art = generate_from_prompt(
                description=args.prompt,
                width=args.width,
                height=args.height,
                gradient=args.gradient,
                style_hint=args.style,
                temperature=args.temperature,
            )

        elif args.image:
            # Pure image mode — fast deterministic conversion
            art = generate_from_image(
                image_path=args.image,
                width=args.width,
                height=args.height,
                gradient=args.gradient,
                dither=args.dither,
                brightness=args.brightness,
                contrast=args.contrast,
                gamma=args.gamma,
                edge_detection=args.edges,
                invert=args.invert,
            )

        # --- Output ---
        output_art(art, args.output)
        return 0

    except RuntimeError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Cancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
