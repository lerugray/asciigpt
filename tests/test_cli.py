"""Tests for the CLI: argument parsing + end-to-end invocations."""

import pytest

from asciigpt import cli

from _fixtures import gradient_image, shapes_image, color_image, solid_image


# ---------------------------------------------------------------------------
# Pure parser tests (no conversion).
# ---------------------------------------------------------------------------

def test_parser_defaults():
    args = cli.build_parser().parse_args(["pic.png"])
    assert args.image == "pic.png"
    assert args.width == 80
    assert args.height is None
    assert args.preset == "default"
    assert args.dither == "floyd-steinberg"
    assert args.edges is False
    assert args.output_format == "text"
    assert args.background == "#000000"


def test_parser_jp2a_style_flags():
    args = cli.build_parser().parse_args(
        ["pic.png", "--width", "120", "--height", "40", "--invert",
         "--background", "#ffffff"]
    )
    assert args.width == 120
    assert args.height == 40
    assert args.invert is True
    assert args.background == "#ffffff"


def test_parser_custom_chars_and_preset():
    args = cli.build_parser().parse_args(
        ["pic.png", "--chars", " .:-=+*#%@", "--preset", "high-contrast"]
    )
    assert args.chars == " .:-=+*#%@"
    assert args.preset == "high-contrast"


def test_parser_edges_and_dither_and_format():
    args = cli.build_parser().parse_args(
        ["pic.png", "--edges", "--edge-threshold", "60",
         "--dither", "atkinson", "--format", "html"]
    )
    assert args.edges is True
    assert args.edge_threshold == 60.0
    assert args.dither == "atkinson"
    assert args.output_format == "html"


def test_parser_preprocessing_flags():
    args = cli.build_parser().parse_args(
        ["pic.png", "--brightness", "1.2", "--contrast", "0.8",
         "--sharpness", "2.0", "--gamma", "1.5", "--threshold", "128"]
    )
    assert args.brightness == 1.2
    assert args.contrast == 0.8
    assert args.sharpness == 2.0
    assert args.gamma == 1.5
    assert args.threshold == 128


def test_parser_text_flags():
    args = cli.build_parser().parse_args(
        ["--text", "HELLO", "--font", "slant"]
    )
    assert args.text == "HELLO"
    assert args.font == "slant"


def test_parser_rejects_unknown_dither():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["pic.png", "--dither", "nope"])


def test_parser_rejects_unknown_format():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["pic.png", "--format", "jpeg"])


# ---------------------------------------------------------------------------
# End-to-end main() tests (real conversion, real output capture).
# ---------------------------------------------------------------------------

def test_main_no_input_returns_error(capsys):
    code = cli.main([])
    assert code == 1
    err = capsys.readouterr().err
    # The error names all three input modes: prompt, image, and --text.
    assert "an image to convert" in err.lower()
    assert "--prompt" in err.lower()


def test_main_list_presets(capsys):
    code = cli.main(["--list-presets"])
    assert code == 0
    out = capsys.readouterr().out
    assert "default" in out
    assert "high-contrast" in out


def test_main_convert_text(tmp_path, capsys):
    img = gradient_image(tmp_path)
    code = cli.main([img, "--width", "30"])
    assert code == 0
    out = capsys.readouterr().out.rstrip("\n")
    lines = out.split("\n")
    # Width respected on every line.
    assert all(len(ln) <= 30 for ln in lines)
    # Non-empty content.
    assert any(ln.strip() for ln in lines)


def test_main_convert_to_file(tmp_path):
    img = gradient_image(tmp_path)
    out_file = tmp_path / "out.txt"
    code = cli.main([img, "--width", "20", "-o", str(out_file)])
    assert code == 0
    text = out_file.read_text()
    assert text.strip()


def test_main_edges_mode_only_directional_glyphs(tmp_path, capsys):
    img = shapes_image(tmp_path)
    code = cli.main([img, "--width", "40", "--edges"])
    assert code == 0
    out = capsys.readouterr().out
    allowed = set(" -|/\\\n")
    assert set(out) <= allowed
    # And at least some real edges were drawn.
    assert any(ch in "-|/\\" for ch in out)


def test_main_ansi_format(tmp_path, capsys):
    img = color_image(tmp_path)
    code = cli.main([img, "--width", "20", "--format", "ansi"])
    assert code == 0
    out = capsys.readouterr().out
    assert "\x1b[38;2;" in out  # truecolor escapes present


def test_main_html_format_to_file(tmp_path):
    img = color_image(tmp_path)
    out_file = tmp_path / "art.html"
    code = cli.main([img, "--width", "20", "--format", "html",
                     "-o", str(out_file)])
    assert code == 0
    html = out_file.read_text()
    assert html.startswith("<!DOCTYPE html>")
    assert "<pre" in html


def test_main_custom_chars(tmp_path, capsys):
    img = gradient_image(tmp_path)
    code = cli.main([img, "--width", "30", "--chars", " .:#@", "--dither", "none"])
    assert code == 0
    out = capsys.readouterr().out
    # Only characters from the custom ramp (+ newline) should appear.
    assert set(out) <= set(" .:#@\n")


def test_main_unknown_preset_errors(tmp_path, capsys):
    img = gradient_image(tmp_path)
    code = cli.main([img, "--preset", "nonexistent"])
    assert code == 1
    assert "preset" in capsys.readouterr().err.lower()


def test_main_missing_image_errors(capsys):
    code = cli.main(["/no/such/file.png"])
    assert code == 1
    assert "not found" in capsys.readouterr().err.lower()


def test_main_text_banner_standalone(capsys):
    code = cli.main(["--text", "HI"])
    assert code == 0
    out = capsys.readouterr().out
    # FIGlet 'standard' font renders multi-line block letters.
    assert len(out.split("\n")) > 1
    assert out.strip()


def test_main_image_flag_equivalent_to_positional(tmp_path, capsys):
    img = gradient_image(tmp_path)
    code = cli.main(["--image", img, "--width", "20"])
    assert code == 0
    assert capsys.readouterr().out.strip()


def test_main_invert_changes_output(tmp_path, capsys):
    """--invert should flip which end of the ramp dominates."""
    img = gradient_image(tmp_path)
    cli.main([img, "--width", "30", "--dither", "none"])
    normal = capsys.readouterr().out
    cli.main([img, "--width", "30", "--dither", "none", "--invert"])
    inverted = capsys.readouterr().out
    assert normal != inverted


def test_main_threshold_produces_bilevel(tmp_path, capsys):
    """With max-bw preset + threshold, output is just '@' and space."""
    img = gradient_image(tmp_path)
    code = cli.main([img, "--width", "30", "--preset", "max-bw",
                     "--threshold", "128", "--dither", "none"])
    assert code == 0
    out = capsys.readouterr().out
    assert set(out) <= set("@ \n")
