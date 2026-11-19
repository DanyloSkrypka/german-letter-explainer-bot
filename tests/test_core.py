"""Core behaviour: disclaimer, languages, photo deletion, rendering."""
import shutil
from datetime import date
from pathlib import Path

from app.analyzer import RuleAnalyzer
from app.core import LetterAssistant, build_draft, fmt_amount
from decimal import Decimal

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def bot():
    return LetterAssistant(analyzer=RuleAnalyzer(), today_fn=lambda: date(2026, 11, 19))


def test_start_has_rdg_disclaimer_and_lang_buttons():
    out = bot().start("u1", "de")
    joined = " ".join(o.text for o in out)
    assert "не юридическая консультация" in joined and "RDG" in joined
    assert ("🇺🇦 Українська", "lang:uk") in out[-1].buttons


def test_telegram_language_code_uk_preselects_ukrainian():
    b = bot()
    out = b.start("u2", "uk")
    assert "Це не юридична консультація" in " ".join(o.text for o in out)


async def test_photo_is_deleted_after_answer(tmp_path):
    b = bot()
    b.set_lang("u3", "uk")
    img = tmp_path / "letter.jpg"
    shutil.copy(SAMPLES / "03_krankenkasse_photo.jpg", img)
    out = await b.handle_image("u3", img)
    assert not img.exists()
    card, draft, footer = (o.text for o in out)
    assert "30.11.2026" in card and "158,80 €" in card and "Krankenkasse" in card
    assert "Ratenzahlung" in draft
    assert "Це не юридична консультація" in footer and "видалено" in footer


async def test_photo_deleted_even_if_unreadable(tmp_path):
    img = tmp_path / "blank.png"
    img.write_bytes(b"not an image")
    out = await bot().handle_image("u4", img)
    assert not img.exists() and "Не получилось" in out[0].text


def test_draft_has_placeholders_not_personal_data():
    a = RuleAnalyzer().analyze("Hausverwaltung X\nDatum: 16.11.2026\nNachzahlung 238,15 €\n"
                               "Betriebskostenabrechnung 2025", today=date(2026, 11, 19))
    d = build_draft(a)
    assert "[Vorname Nachname]" in d and "§ 259 BGB" in d and "238,15 €" in d


def test_amount_format():
    assert fmt_amount(Decimal("1918.15")) == "1.918,15 €"
