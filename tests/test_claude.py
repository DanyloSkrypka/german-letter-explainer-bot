"""ClaudeAnalyzer with a mocked SDK client (no key, no network): JSON mapping + fallback to rules."""
import json
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.analyzer import ClaudeAnalyzer, RuleAnalyzer, get_analyzer

TEXT = "Finanzamt Lindenau\nDatum: 18.11.2026\nBitte zahlen Sie 487,00 € bis zum 21.12.2026."


def make(create):
    a = ClaudeAnalyzer.__new__(ClaudeAnalyzer)
    a.model, a.fallback = "claude-opus-5-5", RuleAnalyzer()
    a.client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    return a


def test_maps_structured_output():
    payload = {"sender": "finanzamt", "org_name": "Finanzamt Lindenau", "letter_type": "bescheid",
               "letter_date": "2026-11-18", "deadline": "2026-12-21", "deadline_quote": "bis zum 21.12.2026",
               "deadline_approx": False, "amount": "487.00", "amount_quote": "487,00 €", "ref_label": "",
               "ref": "", "items": [], "scam": [], "summary": "Налог.", "steps": ["Оплатить."], "miss": "Пени.",
               "reply_de": "Sehr geehrte Damen und Herren, ..."}
    seen = {}

    def create(**kw):
        seen.update(kw)
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(payload))])

    a = make(create).analyze(TEXT, "ru", today=date(2026, 11, 19))
    assert a.engine == "claude" and a.deadline == date(2026, 12, 21) and a.amount == Decimal("487.00")
    assert seen["output_config"]["format"]["type"] == "json_schema" and seen["model"] == "claude-opus-5-5"


def test_falls_back_to_rules_on_error():
    def create(**kw):
        raise RuntimeError("network down")

    a = make(create).analyze(TEXT, "ru", today=date(2026, 11, 19))
    assert a.engine == "rules" and a.amount == Decimal("487.00")


def test_no_key_means_rules(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert isinstance(get_analyzer(), RuleAnalyzer)
