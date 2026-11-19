"""Unit tests for the rule engine on tricky text (no OCR)."""
from datetime import date
from decimal import Decimal

from app.analyzer import RuleAnalyzer, find_dates

TODAY = date(2026, 11, 19)
R = RuleAnalyzer()


def test_ocr_noise_in_dates():
    assert find_dates("bis zum 21 „12.2026 auf")[0][0] == date(2026, 12, 21)
    assert find_dates("spätestens 30.11 ‚2026.")[0][0] == date(2026, 11, 30)
    assert find_dates("bis 5. Januar 2027")[0][0] == date(2027, 1, 5)


def test_ranges_and_validity_are_not_deadlines():
    t = ("Jobcenter Musterstadt\nDatum: 01.11.2026\nBewilligungszeitraum 01.01.2027 bis 30.06.2027\n"
         "Ihr Titel ist gültig bis 04.03.2027.\nBitte senden Sie die Unterlagen bis zum 20.11.2026.")
    a = R.analyze(t, today=TODAY)
    assert a.deadline == date(2026, 11, 20)


def test_amount_prefers_total_over_positions():
    t = ("Krankenkasse\nBeitrag Oktober 2026 78,40 €\nSäumniszuschlag 2,00 €\nGesamtbetrag 80,40 €\n"
         "Ab Januar beträgt Ihr monatlicher Beitrag 81,00 €.")
    assert R.analyze(t, today=TODAY).amount == Decimal("80.40")


def test_thousands_separator():
    t = "Finanzamt\nBitte zahlen Sie 1.234,56 € bis zum 01.12.2026."
    a = R.analyze(t, today=TODAY)
    assert a.amount == Decimal("1234.56") and a.deadline == date(2026, 12, 1)


def test_relative_weeks_from_letter_date():
    t = "Hausverwaltung Muster\nMusterstadt, 02.11.2026\nBitte zahlen Sie innerhalb von zwei Wochen."
    a = R.analyze(t, today=TODAY)
    assert a.deadline == date(2026, 11, 16) and a.deadline_approx


def test_appeal_period_is_not_main_deadline():
    t = "Finanzamt\nDatum: 18.11.2026\nDer Einspruch ist innerhalb eines Monats nach Bekanntgabe einzulegen."
    assert R.analyze(t, today=TODAY).deadline is None


def test_scam_signals():
    t = "Finanzamt Berlin\nZahlen Sie sofort per Google-Play Karte. IBAN: LT12 3456 7890 1234 5678"
    flags = R.analyze(t, today=TODAY).scam
    assert any("google" in f for f in flags) and any(f.startswith("IBAN LT") for f in flags)


def test_unknown_sender():
    assert R.analyze("Hallo, dies ist ein Brief ohne Absender.", today=TODAY).sender == "other"
