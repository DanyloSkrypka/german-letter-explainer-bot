"""Messenger-agnostic core: language choice, photo -> OCR -> analysis -> reply messages, privacy cleanup.

Used by the Telegram bot (app/bot.py) and the local web emulator (app/web.py), so both behave the same.
"""
from __future__ import annotations

import asyncio
import html
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

from .analyzer import Analysis, get_analyzer
from .ocr import OCRError, ocr_image
from .texts import (DRAFT_FOOT, DRAFT_HEAD, DRAFTS, LANGS, MISS_OVERRIDE, SENDERS, TYPES, UI, days_left_text)

log = logging.getLogger("letter-bot")


@dataclass
class Out:
    text: str  # Telegram HTML subset: <b> <i> <code> <pre> <blockquote>
    buttons: list[tuple[str, str]] = field(default_factory=list)  # (title, callback data)


def fmt_date(d: date | None) -> str:
    return d.strftime("%d.%m.%Y") if d else "—"


def fmt_amount(a: Decimal | None) -> str:
    if a is None:
        return ""
    s = f"{a:,.2f}"  # 1,918.15
    return s.replace(",", " ").replace(".", ",").replace(" ", ".") + " €"


def lang_buttons(lang: str = "ru") -> list[tuple[str, str]]:
    return [(UI[lang]["btn_ru"], "lang:ru"), (UI[lang]["btn_uk"], "lang:uk")]


def guess_lang(code: str | None) -> str:
    return "uk" if (code or "").lower().startswith("uk") else "ru"


def render(a: Analysis, lang: str, today: date) -> list[Out]:
    t = UI[lang]
    e = html.escape
    tpl = TYPES[lang].get(a.letter_type, TYPES[lang]["other"])
    amount = fmt_amount(a.amount)
    dl = fmt_date(a.deadline)
    tm = re.search(r"\bum\s+(\d{1,2})[:.](\d{2})\s*Uhr", a.deadline_quote or "")
    if a.deadline and tm:
        dl += f", {int(tm.group(1)):02d}:{tm.group(2)}"
    ref = f"{a.ref_label} {a.ref}".strip() or "—"
    fill = {"amount": amount or "—", "deadline": dl, "ref": e(ref)}

    summary = e(a.summary) if a.summary else tpl["summary"].format(**fill)
    steps = [e(s) for s in a.steps] if a.steps else [s.format(**fill) for s in tpl["steps"]]
    miss = e(a.miss) if a.miss else MISS_OVERRIDE[lang].get((a.sender, a.letter_type), tpl["miss"])

    lines = [f"📄 <b>{t['who']}:</b> {e(SENDERS[lang].get(a.sender, SENDERS[lang]['other']))}"]
    if a.org_name and a.sender != "other":
        lines[-1] += f"\n<i>{e(a.org_name)}</i>"
    lines.append(f"💡 <b>{t['what']}:</b> {summary}")
    if a.deadline:
        left = days_left_text((a.deadline - today).days, lang)
        approx = f" ({t['approx']})" if a.deadline_approx else ""
        lines.append(f"⏰ <b>{t['deadline']}: {dl}</b> — {left}{approx}\n"
                     f"<blockquote>{t['quote']}: «{e(a.deadline_quote)}»</blockquote>")
    else:
        lines.append(f"⏰ <b>{t['deadline']}:</b> {t['no_deadline']}")
    if a.amount is not None:
        same = a.amount_quote == a.deadline_quote  # one sentence holds both: don't quote it twice
        quote = "" if same else f"\n<blockquote>{t['quote']}: «{e(a.amount_quote)}»</blockquote>"
        lines.append(f"💶 <b>{t['amount']}: {amount}</b>{quote}")
    else:
        lines.append(f"💶 <b>{t['amount']}:</b> {t['no_amount']}")
    if a.ref:
        lines.append(f"🔖 <b>{t['ref']}:</b> <code>{e(ref)}</code>")
    if a.items:
        lines.append(f"📋 <b>{t['list']}:</b>\n" + "\n".join(f"• {e(i)}" for i in a.items))
    lines.append(f"✅ <b>{t['todo']}:</b>\n" + "\n".join(f"{n}. {s}" for n, s in enumerate(steps, 1)))
    lines.append(f"⚠️ <b>{t['miss']}:</b> {miss}")
    if a.scam:
        lines.append(f"{t['scam']} " + ", ".join(e(s) for s in a.scam))
    card = "\n\n".join(lines)

    reply = a.reply_de or build_draft(a)
    draft = f"{t['draft']}\n<pre>{e(reply)}</pre>"
    engine = t["engine_llm"] if a.engine == "claude" else t["engine_rules"]
    footer = f"{t['disclaimer']}\n\n{t['deleted']}\n<i>{engine}</i>"
    return [Out(card), Out(draft), Out(footer, buttons=lang_buttons(lang))]


def build_draft(a: Analysis) -> str:
    ref_part = f" – {a.ref_label} {a.ref}" if a.ref else ""
    head = DRAFT_HEAD.format(org=a.org_name or "[Absender]", letter_date=fmt_date(a.letter_date) if a.letter_date
                             else "[Datum]", ref_part=ref_part)
    items = "\n".join(f"– {i}" for i in a.items) if a.items else "– [Unterlage 1]\n– [Unterlage 2]"
    body = DRAFTS.get(a.letter_type, DRAFTS["other"]).format(
        amount=fmt_amount(a.amount) or "[Betrag]", deadline=fmt_date(a.deadline), items=items)
    return head + body + DRAFT_FOOT


class LetterAssistant:
    """Holds only the chosen language per user. Letters and photos are never stored."""

    def __init__(self, analyzer=None, today_fn=date.today):
        self.analyzer = analyzer or get_analyzer()
        self.today_fn = today_fn
        self.langs: dict[str, str] = {}

    def lang(self, user: str) -> str:
        return self.langs.get(user, "ru")

    def start(self, user: str, lang_code: str | None = None) -> list[Out]:
        lang = self.langs.setdefault(user, guess_lang(lang_code))
        t = UI[lang]
        return [Out(t["hello"]), Out(t["disclaimer"]), Out(t["choose"], buttons=lang_buttons(lang))]

    def choose_lang(self, user: str) -> list[Out]:
        return [Out(UI[self.lang(user)]["choose"], buttons=lang_buttons(self.lang(user)))]

    def set_lang(self, user: str, lang: str) -> list[Out]:
        if lang not in LANGS:
            lang = "ru"
        self.langs[user] = lang
        return [Out(UI[lang]["lang_set"])]

    def text(self, user: str) -> list[Out]:
        return [Out(UI[self.lang(user)]["send_photo"])]

    def pdf(self, user: str) -> list[Out]:
        return [Out(UI[self.lang(user)]["pdf"])]

    def reading(self, user: str) -> str:
        return UI[self.lang(user)]["reading"]

    async def handle_image(self, user: str, path: str | Path) -> list[Out]:
        return (await self.handle_image_facts(user, path))[0]

    async def handle_image_facts(self, user: str, path: str | Path) -> tuple[list[Out], dict]:
        """OCR + analysis. ALWAYS deletes the image file, also on errors (DSGVO: no storage of letters).

        Returns the reply messages and a few non-personal facts (for the demo page side panel)."""
        lang = self.lang(user)
        try:
            text = await asyncio.to_thread(ocr_image, path)
            if len(text.strip()) < 40:
                return [Out(UI[lang]["ocr_fail"])], {}
            analysis = await asyncio.to_thread(self.analyzer.analyze, text, lang, self.today_fn())
            del text  # the letter text lives only in memory for this call
            facts = {"sender": analysis.sender, "deadline": fmt_date(analysis.deadline),
                     "amount": fmt_amount(analysis.amount), "engine": analysis.engine}
            return render(analysis, lang, self.today_fn()), facts
        except OCRError:
            log.warning("OCR failed")  # no letter content in logs
            return [Out(UI[lang]["ocr_fail"])], {}
        finally:
            Path(path).unlink(missing_ok=True)
