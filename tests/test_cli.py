"""Tests for bumper CLI core functions."""
import os
import tempfile

import pytest
import yaml
from PIL import ImageFont

# Set working directory before importing cli so BASE resolves correctly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

from adult_swim_bumper.cli import (
    _wrap_text,
    _is_sandwich,
    get_font,
    get_timings,
    make_card_image,
    slugify,
    load_bumpers,
)


# ── unit tests ────────────────────────────────────────────────────────────────

def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"


def test_slugify_punctuation():
    assert slugify("it's friday night.") == "its-friday-night"


def test_slugify_truncates():
    long = "a" * 100
    assert len(slugify(long)) <= 50


def test_get_timings_divides_evenly():
    timings = get_timings(4, total=8.0)
    assert len(timings) == 4
    # Each start should be at 0, 2, 4, 6
    assert timings[0][0] == 0.0
    assert timings[1][0] == 2.0
    assert timings[2][0] == 4.0
    assert timings[3][0] == 6.0


def test_get_timings_gap_applied():
    timings = get_timings(2, total=4.0, gap=0.2)
    # First card: 0.0 → 1.8 (2.0 - 0.2)
    assert timings[0][1] == pytest.approx(1.8, abs=0.01)


def test_wrap_text_short_stays_one_line():
    font = get_font(60)
    lines = _wrap_text("Hi.", font, 1920)
    assert lines == ["Hi."]


def test_wrap_text_long_wraps():
    font = get_font(60)
    # Force a long line that can't fit at 300px
    long = "This is a very long sentence that should wrap onto multiple lines"
    lines = _wrap_text(long, font, 300)
    assert len(lines) > 1


def test_wrap_text_empty():
    font = get_font(60)
    assert _wrap_text("", font, 1920) == [""]


def test_make_card_image_creates_file():
    font = get_font(60)
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "card.png")
        make_card_image("test card", path, font)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


def test_make_card_image_correct_dimensions():
    from PIL import Image
    font = get_font(60)
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "card.png")
        make_card_image("hello", path, font)
        img = Image.open(path)
        assert img.size == (1920, 1080)


# ── bumpers.yaml integrity ────────────────────────────────────────────────────

def test_bumpers_yaml_parses():
    bumpers = load_bumpers()
    assert isinstance(bumpers, list)
    assert len(bumpers) > 0


def test_all_bumpers_have_required_fields():
    bumpers = load_bumpers()
    for b in bumpers:
        assert "name" in b, f"missing name: {b}"
        assert "music" in b, f"missing music: {b['name']}"
        if _is_sandwich(b):
            has_content = b.get("intro_cards") or b.get("outro_cards")
            assert has_content, f"sandwich bumper has no intro_cards or outro_cards: {b['name']}"
            assert b.get("video"), f"sandwich bumper missing video: {b['name']}"
        else:
            assert "cards" in b and b["cards"], f"missing cards: {b['name']}"


def test_sandwich_detection():
    assert _is_sandwich({"intro_cards": ["hi"], "video": "v.mp4", "music": "m.mp3"})
    assert _is_sandwich({"outro_cards": ["bye"], "video": "v.mp4", "music": "m.mp3"})
    assert not _is_sandwich({"cards": ["hi"], "music": "m.mp3"})


def test_all_bumper_names_unique():
    bumpers = load_bumpers()
    names = [b["name"] for b in bumpers]
    assert len(names) == len(set(names)), "duplicate bumper names detected"


def test_all_music_paths_exist():
    bumpers = load_bumpers()
    for b in bumpers:
        path = os.path.join(BASE_DIR, b["music"])
        assert os.path.exists(path), f"{b['name']}: music not found: {b['music']}"


def test_all_video_paths_exist_when_set():
    bumpers = load_bumpers()
    for b in bumpers:
        if b.get("video"):
            path = os.path.join(BASE_DIR, b["video"])
            assert os.path.exists(path), f"{b['name']}: video not found: {b['video']}"
