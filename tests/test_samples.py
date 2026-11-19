"""End-to-end on the 5 fictional sample letters: image -> OCR (tesseract deu) -> rules -> deadline/sender/amount.

Each letter is tested twice: a clean scan (PNG) and a 'phone photo' (rotated, soft, uneven light, JPEG).
"""
import json
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

import pytest

from app.analyzer import RuleAnalyzer
from app.ocr import ocr_image

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
EXPECTED = json.loads((SAMPLES / "expected.json").read_text(encoding="utf-8"))
TODAY = date(2026, 11, 19)
CASES = [(k, suf) for k in EXPECTED for suf in (".png", "_photo.jpg")]


@lru_cache(maxsize=None)
def analysis(key, suffix):
    return RuleAnalyzer().analyze(ocr_image(SAMPLES / f"{key}{suffix}"), "ru", today=TODAY)


@pytest.mark.parametrize("key,suffix", CASES)
def test_sender(key, suffix):
    assert analysis(key, suffix).sender == EXPECTED[key]["sender"]


@pytest.mark.parametrize("key,suffix", CASES)
def test_deadline(key, suffix):
    a = analysis(key, suffix)
    assert a.deadline == date.fromisoformat(EXPECTED[key]["deadline"])
    assert a.deadline_quote, "deadline must come with a quote from the letter"


@pytest.mark.parametrize("key,suffix", CASES)
def test_amount(key, suffix):
    a = analysis(key, suffix)
    exp = EXPECTED[key]["amount"]
    if exp is None:
        assert a.amount is None
    else:
        assert a.amount == Decimal(exp)
        assert a.amount_quote


@pytest.mark.parametrize("key,suffix", CASES)
def test_letter_type(key, suffix):
    assert analysis(key, suffix).letter_type == EXPECTED[key]["type"]


def test_relative_deadline_is_marked_approx():
    a = analysis("04_vermieter", ".png")
    assert a.deadline_approx and a.letter_date == date(2026, 11, 16)


def test_document_list_extracted():
    items = analysis("01_jobcenter", ".png").items
    assert len(items) == 3 and items[0].startswith("Kontoauszüge")


def test_no_scam_flags_on_genuine_samples():
    assert all(not analysis(k, ".png").scam for k in EXPECTED)
