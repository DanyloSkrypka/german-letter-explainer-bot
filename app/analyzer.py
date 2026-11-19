"""Letter analysis behind one interface.

- RuleAnalyzer: free, local, deterministic. Finds sender, letter type, deadline (Frist), amount, reference number,
  document list and scam signals with regex + scoring. Always quotes the source line so the user can check.
- ClaudeAnalyzer: used only when ANTHROPIC_API_KEY is set. Same output shape; falls back to rules on any error.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

log = logging.getLogger("letter-bot.analyzer")


@dataclass
class Analysis:
    sender: str = "other"
    org_name: str = ""
    letter_type: str = "other"
    letter_date: date | None = None
    deadline: date | None = None
    deadline_quote: str = ""
    deadline_approx: bool = False
    amount: Decimal | None = None
    amount_quote: str = ""
    ref_label: str = ""
    ref: str = ""
    items: list[str] = field(default_factory=list)
    scam: list[str] = field(default_factory=list)
    engine: str = "rules"
    # optional ready texts (LLM); rules leave them empty and the renderer uses templates
    summary: str = ""
    steps: list[str] = field(default_factory=list)
    miss: str = ""
    reply_de: str = ""


# ---------------------------------------------------------------- helpers
MONTHS = {"januar": 1, "jänner": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5, "juni": 6,
          "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12}

# tolerant to OCR noise like "21 „12.2026" or "04. 12.2026"
DATE_RE = re.compile(r"(?<![\d/])(\d{1,2})\s?[.,„‚\"'’`´:;]{1,2}\s?(\d{1,2})\s?[.,„‚'’`´]{1,2}\s?(20\d{2})(?!\d)")
DATE_WORD_RE = re.compile(r"(?<!\d)(\d{1,2})\.?\s+(" + "|".join(MONTHS) + r")\s+(20\d{2})", re.I)
AMOUNT_RE = re.compile(
    r"(?:(?:€|EUR)\s?)?(?<![\d.,])(\d{1,3}(?:[.\s]\d{3})+|\d{1,6}),(\d{2})(?!\d)\s?(€|EUR|Euro)?", re.I)

NUM_WORDS = {"einem": 1, "einer": 1, "eines": 1, "ein": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "sechs": 6,
             "sieben": 7, "acht": 8, "zehn": 10, "vierzehn": 14, "dreißig": 30}
REL_RE = re.compile(r"innerhalb\s+(?:von\s+)?(\d{1,3}|" + "|".join(NUM_WORDS) + r")\s+(Tag\w*|Woche\w*|Monat\w*)",
                    re.I)

SENDER_KW = {
    "jobcenter": [(r"jobcenter", 3), (r"sgb\s*ii\b", 2), (r"bürgergeld", 2), (r"bg-nummer", 2),
                  (r"weiterbewilligung", 1), (r"arbeitsuchende", 1)],
    "finanzamt": [(r"finanzamt", 3), (r"steuernummer", 2), (r"einkommensteuer", 2), (r"steuerbescheid", 2)],
    "krankenkasse": [(r"krankenkasse", 3), (r"gesundheitskasse", 3), (r"krankenversicherung", 1),
                     (r"\b(aok|barmer|dak|ikk|bkk|hkk)\b", 3), (r"techniker krankenkasse", 3),
                     (r"versichertenn", 2), (r"beitragsrückstand", 1), (r"pflegeversicherung", 1)],
    "vermieter": [(r"vermieter", 2), (r"hausverwaltung", 3), (r"immobilien", 1), (r"betriebskosten", 2),
                  (r"nebenkosten", 2), (r"mieternummer|mietvertrag", 2), (r"\bmiete\b", 1)],
    "auslaenderbehoerde": [(r"ausländerbehörde|auslaenderbehoerde", 4), (r"aufenthaltserlaubnis", 2),
                           (r"aufenthaltstitel", 2), (r"aufenthg", 2), (r"fiktionsbescheinigung", 2)],
    "rundfunk": [(r"beitragsservice", 4), (r"rundfunkbeitrag", 3)],
    "familienkasse": [(r"familienkasse", 4), (r"kindergeld", 2)],
}
TYPE_KW = {
    "mahnung": [(r"\bmahnung\b", 3), (r"zahlungserinnerung", 3), (r"rückstand", 2), (r"säumniszuschlag\b", 1),
                (r"mahnverfahren", 1), (r"offene[nr]? betrag", 1)],
    "bescheid": [(r"\bbescheid\b", 2), (r"festgesetzt", 2), (r"steuerbescheid", 3), (r"rechtsbehelfsbelehrung", 1)],
    "abrechnung": [(r"(betriebs|neben)kostenabrechnung", 4), (r"\babrechnung\b", 2)],
    "mitwirkung": [(r"mitwirkung", 4), (r"unterlagen", 1), (r"einreichen|reichen sie", 1)],
    "termin": [(r"einladung", 3), (r"termin am", 3), (r"vorsprache", 2)],
}
REF_RE = re.compile(
    r"(BG-Nummer|Steuernummer|Aktenzeichen|Az\.|Versichertennr\.?|Versichertennummer|Kundennummer|Mieternummer|"
    r"Vertragsnummer|Beitragsnummer|Kindergeldnummer)\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-.]{3,})", re.I)
AUTHORITIES = {"jobcenter", "finanzamt", "krankenkasse", "auslaenderbehoerde", "rundfunk", "familienkasse"}
SCAM_KW = [r"bitcoin", r"krypto", r"gutschein", r"google[- ]play", r"western union", r"paysafe",
           r"innerhalb von 24 stunden", r"haftbefehl", r"verhaftung"]


def _mkdate(d: str, m: str, y: str) -> date | None:
    try:
        return date(int(y), int(m), int(d))
    except ValueError:
        return None


def find_dates(line: str) -> list[tuple[date, int, int]]:
    out = []
    for m in DATE_RE.finditer(line):
        dt = _mkdate(*m.groups())
        if dt:
            out.append((dt, m.start(), m.end()))
    for m in DATE_WORD_RE.finditer(line):
        dt = _mkdate(m.group(1), str(MONTHS[m.group(2).lower()]), m.group(3))
        if dt:
            out.append((dt, m.start(), m.end()))
    return sorted(out, key=lambda t: t[1])


def normalize_dates(line: str) -> str:
    """Rewrite OCR-noisy dates in a quote ("21 „12.2026") as 21.12.2026."""
    def fix(m):
        dt = _mkdate(*m.groups())
        return dt.strftime("%d.%m.%Y") if dt else m.group(0)
    return DATE_RE.sub(fix, line)


def parse_amount(intpart: str, cents: str) -> Decimal:
    return Decimal(re.sub(r"[.\s]", "", intpart) + "." + cents)


def clean_lines(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]


def _score(text: str, table: dict, header: str) -> tuple[str, int]:
    best, best_s = "other", 0
    low, hlow = text.lower(), header.lower()
    for key, kws in table.items():
        s = 0
        for pat, w in kws:
            s += w * min(len(re.findall(pat, low)), 3)
            if re.search(pat, hlow):
                s += w  # letterhead counts double
        if s > best_s:
            best, best_s = key, s
    return best, best_s


# ---------------------------------------------------------------- rules
class RuleAnalyzer:
    name = "rules"

    def analyze(self, text: str, lang: str = "ru", today: date | None = None) -> Analysis:
        lines = clean_lines(text)
        nonempty = [ln for ln in lines if ln]
        header = "\n".join(nonempty[:8])
        a = Analysis(engine="rules")
        a.sender, _ = _score(text, SENDER_KW, header)
        a.letter_type, _ = _score(text, TYPE_KW, header)
        if nonempty and len(nonempty[0]) < 60 and not nonempty[0][0].isdigit():
            a.org_name = re.sub(r"\s+[A-Z]{1,3}$", "", nonempty[0])  # drop a logo mark like "JC"
        a.letter_date = self._letter_date(nonempty)
        self._deadline(a, lines, today or date.today())
        self._amount(a, lines)
        m = REF_RE.search(text)
        if m:
            a.ref_label, a.ref = m.group(1).rstrip(".:"), m.group(2).rstrip(".")
        a.items = self._items(lines)
        a.scam = self._scam(text, a.sender)
        return a

    @staticmethod
    def _letter_date(lines: list[str]) -> date | None:
        for ln in lines[:25]:
            m = re.search(r"Datum\s*[:.]?\s*(.+)", ln)
            if m:
                ds = find_dates(m.group(1))
                if ds:
                    return ds[0][0]
        for ln in lines[:25]:
            m = re.match(r"^[A-ZÄÖÜ][\wäöüß\- ]{2,30},\s*(den\s+)?(.+)$", ln)
            if m:
                ds = find_dates(m.group(2))
                if ds and ds[0][1] == 0:
                    return ds[0][0]
        return None

    def _deadline(self, a: Analysis, lines: list[str], today: date) -> None:
        best = None  # (score, date, quote)
        for i, ln in enumerate(lines):
            if not ln:
                continue
            # a keyword at the end of a line may have its date on the next line
            joined = ln + (" " + lines[i + 1] if i + 1 < len(lines) and lines[i + 1] else "")
            for dt, s, _e in find_dates(joined):
                if s >= len(ln) + 1 and not re.search(r"(bis|zum|am|spätestens)\s*$", ln, re.I):
                    continue  # date belongs to the next line and nothing here points to it
                before = joined[max(0, s - 48):s].lower()
                if re.search(r"gültig|zeitraum|geboren|erklärung vom|datum|ab dem|\bvom\s*$|beträgt", before):
                    continue
                if re.search(r"\d{4}\s*(bis|–|-)\s*$", before):
                    continue  # second half of a range "01.01.2027 bis 30.06.2027"
                if re.search(r"bis\s+zum|bis\s+spätestens|spätestens|fällig|zahlbar\s+bis|frist|einzureichen bis",
                             before):
                    score = 5
                elif re.search(r"termin\s+(am|ist)|vorsprache\s+am|vorsprechen|erscheinen sie am", before):
                    score = 4
                elif re.search(r"\bbis\s*$", before):
                    score = 2
                else:
                    continue
                cand = (score, dt, ln if s < len(ln) else joined)
                if best is None or cand[0] > best[0] or (cand[0] == best[0] and cand[1] < best[1]):
                    best = cand
        if best:
            a.deadline, a.deadline_quote = best[1], normalize_dates(best[2])
            return
        for ln in lines:
            m = REL_RE.search(ln)
            if not m or re.search(r"einspruch|widerspruch|rechtsbehelf|klage", ln, re.I):
                continue
            n_raw = m.group(1).lower()
            n = int(n_raw) if n_raw.isdigit() else NUM_WORDS.get(n_raw, 0)
            unit = m.group(2).lower()
            base = a.letter_date or today
            if unit.startswith("tag"):
                dl = base + timedelta(days=n)
            elif unit.startswith("woche"):
                dl = base + timedelta(weeks=n)
            else:
                mo = base.month - 1 + n
                y, mo = base.year + mo // 12, mo % 12 + 1
                day = min(base.day, [31, 29 if y % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo - 1])
                dl = date(y, mo, day)
            a.deadline, a.deadline_quote, a.deadline_approx = dl, ln, True
            return

    @staticmethod
    def _amount(a: Analysis, lines: list[str]) -> None:
        best = None  # (score, amount, quote)
        for i, ln in enumerate(lines):
            if not ln:
                continue
            for m in AMOUNT_RE.finditer(ln):
                has_cur = bool(m.group(3)) or ln[max(0, m.start() - 4):m.start()].strip().upper() in ("€", "EUR")
                val = parse_amount(m.group(1), m.group(2))
                low = ln.lower()
                ctx = low
                if not re.search(r"[a-zäöü]{4}", ctx) and i > 0:
                    ctx = (lines[i - 1] + " " + ln).lower()  # table value on its own line: use the label above
                score = 0
                if re.search(r"nachzahlung|zu zahlen|zahlen sie|überweisen|gesamtbetrag|offene[nr]? betrag|"
                             r"gebühr|zahlbetrag|rückstand gesamt|fordern|erstattungsbetrag", ctx):
                    score += 3
                if re.search(r"bitte (zahlen|überweisen)|bis (zum|spätestens)", ctx):
                    score += 2
                if re.search(r"vorauszahlung|regelbedarf|abzüglich|monatlich|gesamtkosten|festgesetzte|"
                             r"steuerabzug|kosten|beitrag (januar|februar|märz|april|mai|juni|juli|august|"
                             r"september|oktober|november|dezember)", ctx):
                    score -= 3
                if not has_cur:
                    score -= 1
                if score <= 0 or val == 0:
                    continue
                cand = (score, val, ln if re.search(r"[a-zäöü]{4}", low) else (lines[i - 1] + " " + ln).strip())
                if best is None or cand[0] > best[0]:
                    best = cand
        if best:
            a.amount, a.amount_quote = best[1], normalize_dates(best[2])

    @staticmethod
    def _items(lines: list[str]) -> list[str]:
        items: list[str] = []
        for i, ln in enumerate(lines):
            if ln.endswith(":") and re.search(r"unterlagen|mitbringen|bringen sie|benötigen|folgende", ln, re.I):
                for nxt in lines[i + 1:i + 14]:
                    if not nxt:
                        continue
                    bullet = re.match(r"^([•·\-–—*o°«»e©®+„‚\"']|\d+[.)])\s", nxt)
                    if not bullet and (len(nxt) > 70 or nxt.endswith((".", ":"))):
                        break  # back to normal paragraph text
                    item = re.sub(r"^([•·\-–—*o°«»e©®+„‚\"']|\d+[.)])\s*", "", nxt).strip()
                    if len(item) >= 4:
                        items.append(item)
                if items:
                    break
        return items[:6]

    @staticmethod
    def _scam(text: str, sender: str) -> list[str]:
        flags = []
        low = text.lower()
        for pat in SCAM_KW:
            m = re.search(pat, low)
            if m:
                flags.append(m.group(0))
        if sender in AUTHORITIES:
            for m in re.finditer(r"\bIBAN[:\s]*([A-Z]{2})\d{2}", text):
                if m.group(1) != "DE":
                    flags.append(f"IBAN {m.group(1)}…")
        return flags


# ---------------------------------------------------------------- Claude
SCHEMA = {
    "type": "object",
    "properties": {
        "sender": {"type": "string", "enum": ["jobcenter", "finanzamt", "krankenkasse", "vermieter",
                                              "auslaenderbehoerde", "rundfunk", "familienkasse", "other"]},
        "org_name": {"type": "string"},
        "letter_type": {"type": "string", "enum": ["mahnung", "bescheid", "abrechnung", "mitwirkung", "termin",
                                                   "other"]},
        "letter_date": {"type": ["string", "null"], "description": "YYYY-MM-DD"},
        "deadline": {"type": ["string", "null"], "description": "YYYY-MM-DD, the main action deadline"},
        "deadline_quote": {"type": "string", "description": "exact line from the letter"},
        "deadline_approx": {"type": "boolean"},
        "amount": {"type": ["string", "null"], "description": "amount the reader must pay, like 158.80"},
        "amount_quote": {"type": "string"},
        "ref_label": {"type": "string"},
        "ref": {"type": "string"},
        "items": {"type": "array", "items": {"type": "string"}},
        "scam": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
        "steps": {"type": "array", "items": {"type": "string"}},
        "miss": {"type": "string"},
        "reply_de": {"type": "string"},
    },
    "required": ["sender", "org_name", "letter_type", "letter_date", "deadline", "deadline_quote", "deadline_approx",
                 "amount", "amount_quote", "ref_label", "ref", "items", "scam", "summary", "steps", "miss",
                 "reply_de"],
    "additionalProperties": False,
}

SYSTEM = """You explain German official letters to people who read Russian or Ukrainian.
You get OCR text of one letter (may contain OCR errors). Extract facts only from the text; never invent.
- deadline: the main date by which the reader must act (pay, send documents, appear). If the letter gives only a
  relative period ("innerhalb von 30 Tagen nach Erhalt"), count it from the letter date and set deadline_approx=true.
  Ignore validity dates, periods ("Zeitraum"), birth dates and appeal periods unless nothing else exists.
- amount: only what the reader must pay now (total), not single positions or prepayments. null if nothing to pay.
- deadline_quote / amount_quote: copy the exact source line.
- summary (2 short sentences), steps (3 short steps), miss (what happens if ignored): in the language given,
  plain words, no legal advice, no guarantees. Keep German terms like Bescheid, Einspruch in German.
- reply_de: a short polite German reply draft with [placeholders] for the reader's name and address. Do not copy
  the reader's personal data from the letter.
- scam: list concrete warning signs if the letter looks fake (foreign IBAN for an authority, gift cards, crypto,
  threats of arrest); else empty."""


class ClaudeAnalyzer:
    name = "claude"

    def __init__(self, model: str | None = None):
        import anthropic  # optional dependency

        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        self.model = model or os.getenv("LLM_MODEL", "claude-opus-5-5")
        self.fallback = RuleAnalyzer()

    def analyze(self, text: str, lang: str = "ru", today: date | None = None) -> Analysis:
        try:
            return self._analyze(text, lang, today or date.today())
        except Exception as e:  # network, refusal, bad JSON -> never leave the user without an answer
            log.warning("Claude analysis failed (%s), using local rules", type(e).__name__)
            return self.fallback.analyze(text, lang, today)

    def _analyze(self, text: str, lang: str, today: date) -> Analysis:
        language = "Ukrainian" if lang == "uk" else "Russian"
        resp = self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            system=SYSTEM,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": f"Today: {today.isoformat()}. Answer language: {language}.\n\n"
                                                  f"<letter_ocr>\n{text}\n</letter_ocr>"}],
        )
        if resp.stop_reason == "refusal":
            raise RuntimeError("refusal")
        raw = next(b.text for b in resp.content if b.type == "text")
        d = json.loads(raw)

        def _d(s):
            try:
                return date.fromisoformat(s) if s else None
            except ValueError:
                return None

        amount = None
        if d.get("amount"):
            try:
                amount = Decimal(str(d["amount"]).replace(",", "."))
            except Exception:
                amount = None
        return Analysis(
            sender=d["sender"], org_name=d["org_name"], letter_type=d["letter_type"],
            letter_date=_d(d["letter_date"]), deadline=_d(d["deadline"]), deadline_quote=d["deadline_quote"],
            deadline_approx=bool(d["deadline_approx"]), amount=amount, amount_quote=d["amount_quote"],
            ref_label=d["ref_label"], ref=d["ref"], items=d["items"][:6], scam=d["scam"], engine="claude",
            summary=d["summary"], steps=d["steps"][:5], miss=d["miss"], reply_de=d["reply_de"],
        )


def get_analyzer():
    """Claude if a key is configured (and LLM_ENABLED is not 0), otherwise the free local rules."""
    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("LLM_ENABLED", "1") != "0":
        try:
            return ClaudeAnalyzer()
        except ImportError:
            log.warning("anthropic package not installed, using local rules")
    return RuleAnalyzer()
