"""
asciigpt — named gradient presets.

A "gradient" is an ordered character ramp from darkest (fills the most
visual space) to lightest (mostly empty). When converting an image, a
dark pixel picks a character from the start of the ramp and a bright
pixel picks one from the end.

This is the single best feature adapted from asciiart.eu's converter:
named character-set styles the user selects by name (``--preset``)
instead of hand-typing a ``--chars`` string. The asciiart.eu set
(Alphabetic, Alphanumeric, Arrow, Code Page 437, Extended High,
Gray Scale, Minimalist, Math Symbols, Normal, Normal 2, Numerical,
plus a Max Black-and-White mode) is mirrored here under friendly names,
alongside a few task-oriented ramps of our own.

Every ramp is ordered DARK -> LIGHT. The renderer maps low luminance to
the front of the string and high luminance to the back, so a ramp that
ends in a space leaves bright areas blank (the usual look). Add your own
by dropping a new entry in ``PRESETS`` — the CLI and ``--list-presets``
pick it up automatically.

NOTE on ASCII vs. Unicode: most presets are pure printable ASCII (safe
in any monospace terminal). A few (``blocks``, ``code-page-437``,
``arrow``) use Unicode glyphs and are marked ``ascii_only=False`` so the
renderer / tests can tell them apart.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    """A named character ramp.

    Attributes:
        name:       The key users pass to ``--preset``.
        ramp:       Characters ordered darkest -> lightest.
        ascii_only: True if every character is printable ASCII (0x20-0x7E).
                    False means the ramp contains Unicode (block elements,
                    box drawing, arrows) and needs a Unicode-capable
                    terminal/font.
        description: One-line human summary for ``--list-presets``.
    """

    name: str
    ramp: str
    ascii_only: bool
    description: str


def _is_pure_ascii(text):
    """True if every character is printable ASCII (space..tilde)."""
    return all(0x20 <= ord(ch) <= 0x7E for ch in text)


# ---------------------------------------------------------------------------
# The preset table.
#
# Ordered dark -> light in every case. The ``ascii_only`` flag is computed
# below so we never have to keep it in sync by hand.
# ---------------------------------------------------------------------------

_RAW_PRESETS = {
    # --- General purpose -------------------------------------------------
    # Balanced contrast, the everyday default. Short ramp = crisp output.
    "default": (
        "@%#*+=-:. ",
        "Balanced 10-step ramp. Good first choice for most images.",
    ),

    # asciiart.eu "Normal" — the classic medium-length photographic ramp.
    "normal": (
        "@#W$9876543210?!abc;:+=-,._ ",
        "Classic medium photographic ramp (asciiart.eu 'Normal').",
    ),

    # asciiart.eu "Normal 2" — an alternate medium ramp with a different feel.
    "normal2": (
        "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
        "Long alternate ramp (asciiart.eu 'Normal 2'). Smooth tonal steps.",
    ),

    # --- Detail / photographic ------------------------------------------
    # The famous 70-character Paul Bourke ramp. Maximum tonal resolution.
    "high-contrast": (
        "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
        "70-step Paul Bourke ramp. Highest tonal detail; best for photos.",
    ),

    # asciiart.eu "Extended High" — a dense ramp packed with mid-tone glyphs.
    "extended-high": (
        "MWNXK0Okxdolc:;,'.   ",
        "Dense high-detail ramp with heavy mid-tones (asciiart.eu 'Extended High').",
    ),

    # Reversed soft ramp, light -> ... no: still dark->light but gentle steps.
    # Good for portraits where you want soft tonal transitions.
    "smooth": (
        "BR%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft|/()1{}[]?-_+~i!lI;:,\"^`'. ",
        "Gentle tonal steps. Flattering on portraits and faces.",
    ),

    # --- Sparse / stylized ----------------------------------------------
    # asciiart.eu "Minimalist" — just a handful of levels. Bold, posterized.
    "minimalist": (
        "@:. ",
        "Four-level posterized look (asciiart.eu 'Minimalist'). Bold and graphic.",
    ),

    # Our own 5-level minimal ramp (kept for backward compatibility).
    "minimal": (
        "@%#* ",
        "Five-level sparse ramp. Good for logos and small output.",
    ),

    # asciiart.eu "Gray Scale" — even perceptual steps across the range.
    "grayscale": (
        "@$#*!=;:~-,. ",
        "Even perceptual gray steps (asciiart.eu 'Gray Scale').",
    ),

    # --- Character-class ramps (asciiart.eu) ----------------------------
    # "Alphabetic" — letters only, dense -> sparse by visual weight.
    "alphabetic": (
        "MWNHQ@KRBOD8GPAEFZS5JYXTLCIVU?abdpqwmkhgones c rzvuxy ",
        "Letters ordered by visual weight (asciiart.eu 'Alphabetic').",
    ),

    # "Numerical" — digits only.
    "numerical": (
        "80695234 71. ",
        "Digits ordered by visual weight (asciiart.eu 'Numerical').",
    ),

    # "Alphanumeric" — letters and digits combined.
    "alphanumeric": (
        "MW8B@N0HQ#R6593D2GPAE4FZS7JYXTLCIVU1abdpqwmkhgones0o c rzvuxy. ",
        "Letters + digits by visual weight (asciiart.eu 'Alphanumeric').",
    ),

    # "Math Symbols" — punctuation/operator glyphs.
    "math": (
        "%#=+*~^<>:-. ",
        "Operator/punctuation glyphs (asciiart.eu 'Math Symbols').",
    ),

    # --- Retro / themed --------------------------------------------------
    # A short, chunky ramp evoking phosphor terminals. Pair with --ansi
    # --color 0,255,0 for the full green-screen look.
    "retro-green-screen": (
        "@8&o*:. ",
        "Chunky phosphor-terminal ramp. Pair with --ansi --color 0,255,0.",
    ),

    # Sharp angular glyphs — robots, buildings, vehicles.
    "mechanical": (
        "#@%*+|-=:. ",
        "Sharp angular glyphs. Suits machines, buildings, vehicles.",
    ),

    # Soft rounded glyphs — nature, animals, organic subjects.
    "organic": (
        "@%#*~-:,. ",
        "Soft rounded glyphs. Suits nature, animals, organic shapes.",
    ),

    # --- Maximum contrast (bilevel) -------------------------------------
    # asciiart.eu "Max Black and White" — two levels only. Pure on/off.
    # Designed to be paired with --threshold or a dither for line art.
    "max-bw": (
        "@ ",
        "Two-level on/off ramp (asciiart.eu 'Max Black and White'). "
        "Pair with --threshold or a dither.",
    ),

    # --- Unicode presets (need a Unicode-capable terminal) --------------
    # Block elements — true pixel-art density steps. The best-looking ramp
    # for blocky/retro images IF the terminal renders block elements.
    "blocks": (
        "█▓▒░ ",   # FULL / DARK / MEDIUM / LIGHT shade / space
        "Unicode block elements (full/dark/medium/light shade). Pixel-art look.",
    ),

    # asciiart.eu "Code Page 437" — the IBM PC OEM glyph feel, approximated
    # with Unicode block/shade characters that exist in CP437.
    "code-page-437": (
        "█▓▒░■▪· ",
        "DOS/CP437 block-and-dot feel (asciiart.eu 'Code Page 437'). Unicode.",
    ),

    # asciiart.eu "Arrow" — directional arrow glyphs, novelty texture.
    "arrow": (
        "█⬛◆▲▶◀▼→↑· ",
        "Arrow/triangle glyphs for novelty texture (asciiart.eu 'Arrow'). Unicode.",
    ),
}


# Build the final immutable table, computing ascii_only automatically.
PRESETS = {
    name: Preset(
        name=name,
        ramp=ramp,
        ascii_only=_is_pure_ascii(ramp),
        description=description,
    )
    for name, (ramp, description) in _RAW_PRESETS.items()
}


# A stable default name used across the package and the CLI.
DEFAULT_PRESET = "default"


def get_ramp(name):
    """Return the character ramp string for a preset name.

    Args:
        name: A key in ``PRESETS`` (e.g. "high-contrast").

    Returns:
        The dark->light character ramp string.

    Raises:
        KeyError: If ``name`` is not a known preset. The message lists the
                  valid names so the CLI can surface them.
    """
    if name not in PRESETS:
        valid = ", ".join(sorted(PRESETS))
        raise KeyError(f"Unknown preset '{name}'. Available presets: {valid}")
    return PRESETS[name].ramp


def preset_names():
    """Return a sorted list of all preset names (for CLI choices/help)."""
    return sorted(PRESETS)


def describe_presets():
    """Return a list of (name, ramp_preview, description) for ``--list-presets``.

    The preview shows the first ~24 characters of the ramp so the user can
    eyeball the density without the full 70-char ramps blowing up the table.
    """
    rows = []
    for name in sorted(PRESETS):
        preset = PRESETS[name]
        preview = preset.ramp[:24]
        if len(preset.ramp) > 24:
            preview += "..."
        tag = "" if preset.ascii_only else "  [unicode]"
        rows.append((name, preview + tag, preset.description))
    return rows
