"""Tests for the prompt -> image -> ASCII generation seam (asciigpt.generate).

These never touch the network: the default ProceduralBackend draws with
Pillow, so the whole prompt -> image -> ASCII path is exercised offline and
deterministically.
"""

import pytest
from PIL import Image

import asciigpt
from asciigpt import generate as gen
from asciigpt.cli import main


# --- the procedural backend ------------------------------------------------

def test_procedural_backend_returns_rgb_image_of_requested_size():
    img = gen.ProceduralBackend().generate("a shaded sphere", size=128)
    assert isinstance(img, Image.Image)
    assert img.size == (128, 128)
    assert img.mode == "RGB"


def test_procedural_backend_is_deterministic():
    a = gen.ProceduralBackend().generate("dragon over a castle", size=96)
    b = gen.ProceduralBackend().generate("dragon over a castle", size=96)
    assert a.tobytes() == b.tobytes()


def test_different_prompts_make_different_images():
    sphere = gen.ProceduralBackend().generate("sphere", size=96)
    house = gen.ProceduralBackend().generate("house", size=96)
    assert sphere.tobytes() != house.tobytes()


def test_empty_prompt_is_rejected():
    with pytest.raises(ValueError):
        gen.ProceduralBackend().generate("   ", size=64)


def test_keyword_matching_picks_a_known_scene():
    assert "sphere" in gen.procedural_caption("a lone sphere in space").lower()
    assert "house" in gen.procedural_caption("a cosy home").lower()


def test_unknown_prompt_falls_back_to_abstract():
    assert "abstract" in gen.procedural_caption("xyzzy quux").lower()


# --- backend registry ------------------------------------------------------

def test_get_backend_default_is_procedural():
    assert isinstance(gen.default_backend(), gen.ProceduralBackend)
    assert gen.get_backend("procedural").name == "procedural"


def test_get_backend_unknown_raises():
    with pytest.raises(KeyError):
        gen.get_backend("does-not-exist")


# --- the end-to-end prompt_to_ascii path -----------------------------------

def test_prompt_to_ascii_end_to_end_text():
    art = asciigpt.prompt_to_ascii("a shaded sphere", width=40)
    lines = art.split("\n")
    assert lines
    assert max(len(line) for line in lines) <= 40
    assert len(lines) >= 5


def test_prompt_to_ascii_is_deterministic():
    a = asciigpt.prompt_to_ascii("a little house", width=50, preset="default")
    b = asciigpt.prompt_to_ascii("a little house", width=50, preset="default")
    assert a == b


def test_prompt_to_ascii_forwards_edge_mode():
    # Edge mode should run through the prompt path and emit directional glyphs
    # from the generated image's outlines (no luminance ramp characters).
    art = asciigpt.prompt_to_ascii("a little house", width=50, edges=True)
    assert art.strip()
    assert any(ch in art for ch in "-|/\\")


def test_prompt_to_ascii_forwards_html_format():
    html = asciigpt.prompt_to_ascii("sphere", width=30, output_format="html")
    assert "<" in html and "html" in html.lower()


def test_prompt_to_ascii_rejects_empty_prompt():
    with pytest.raises(ValueError):
        asciigpt.prompt_to_ascii("", width=20)


# --- CLI wiring ------------------------------------------------------------

def test_cli_prompt_mode_prints_art(capsys):
    code = main(["--prompt", "a shaded sphere", "--width", "40"])
    assert code == 0
    out = capsys.readouterr().out
    assert out.strip()
    assert max(len(line) for line in out.split("\n") if line) <= 40


def test_cli_prompt_overrides_image_with_note(capsys):
    code = main(["--prompt", "sphere", "--image", "nope.png", "--width", "30"])
    assert code == 0
    err = capsys.readouterr().err
    assert "ignoring the image" in err.lower()


def test_cli_no_input_is_an_error(capsys):
    code = main([])
    assert code == 1
    err = capsys.readouterr().err
    assert "prompt" in err.lower()
