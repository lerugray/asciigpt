"""Tests for the named gradient presets."""

import pytest

from asciigpt import gradients


def test_expected_presets_present():
    """The asciiart.eu-derived set plus our themed ramps should all exist."""
    expected = {
        "default", "normal", "normal2", "high-contrast", "extended-high",
        "smooth", "minimalist", "minimal", "grayscale", "alphabetic",
        "numerical", "alphanumeric", "math", "retro-green-screen",
        "mechanical", "organic", "max-bw", "blocks", "code-page-437", "arrow",
    }
    assert expected <= set(gradients.PRESETS)


def test_at_least_a_dozen_presets():
    """Brief asks for ~a dozen; we ship comfortably more."""
    assert len(gradients.PRESETS) >= 12


def test_get_ramp_returns_string():
    ramp = gradients.get_ramp("high-contrast")
    assert isinstance(ramp, str)
    assert len(ramp) > 2


def test_get_ramp_unknown_raises_with_listing():
    with pytest.raises(KeyError) as exc:
        gradients.get_ramp("does-not-exist")
    # The error should enumerate valid names so the CLI can surface them.
    assert "default" in str(exc.value)


def test_ascii_only_flag_is_accurate():
    """ascii_only must match the actual content of each ramp."""
    for name, preset in gradients.PRESETS.items():
        pure = all(0x20 <= ord(ch) <= 0x7E for ch in preset.ramp)
        assert preset.ascii_only == pure, name


def test_ascii_presets_are_truly_ascii():
    """A spot-check that the everyday presets contain no Unicode."""
    for name in ("default", "high-contrast", "minimal", "grayscale"):
        ramp = gradients.get_ramp(name)
        assert all(ord(ch) <= 0x7E for ch in ramp), name


def test_unicode_presets_flagged():
    """blocks / code-page-437 / arrow are Unicode and must be flagged so."""
    for name in ("blocks", "code-page-437", "arrow"):
        assert gradients.PRESETS[name].ascii_only is False


def test_ramps_ordered_dark_to_light_end_in_space_or_light():
    """Most ramps end on the lightest glyph; the common ones end in space."""
    for name in ("default", "high-contrast", "normal", "grayscale", "minimal"):
        assert gradients.get_ramp(name).endswith(" "), name


def test_preset_names_sorted_and_complete():
    names = gradients.preset_names()
    assert names == sorted(names)
    assert set(names) == set(gradients.PRESETS)


def test_describe_presets_shape():
    rows = gradients.describe_presets()
    assert len(rows) == len(gradients.PRESETS)
    for name, preview, desc in rows:
        assert name in gradients.PRESETS
        assert isinstance(preview, str) and preview
        assert isinstance(desc, str) and desc
