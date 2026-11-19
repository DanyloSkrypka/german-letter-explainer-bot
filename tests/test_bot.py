"""Telegram handlers with a fake Bot/Message (no token, no network): photo is downloaded, answered, deleted."""
import shutil
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import app.bot as botmod
from app.analyzer import RuleAnalyzer
from app.core import LetterAssistant

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def fake_message(downloaded: list):
    async def download(file_id, destination):
        shutil.copy(SAMPLES / "02_finanzamt_photo.jpg", destination)
        downloaded.append(Path(destination))

    status = SimpleNamespace(delete=AsyncMock())
    msg = SimpleNamespace(
        from_user=SimpleNamespace(id=42, language_code="ru"),
        chat=SimpleNamespace(id=42),
        photo=[SimpleNamespace(file_id="small", file_size=1000), SimpleNamespace(file_id="big", file_size=200_000)],
        bot=SimpleNamespace(download=download, send_chat_action=AsyncMock()),
        answer=AsyncMock(side_effect=[status] + [None] * 10),
    )
    return msg, status


async def test_photo_handler_answers_and_deletes():
    botmod.assistant = LetterAssistant(analyzer=RuleAnalyzer(), today_fn=lambda: date(2026, 11, 19))
    downloaded = []
    msg, status = fake_message(downloaded)
    await botmod.on_photo(msg)
    texts = [c.args[0] for c in msg.answer.call_args_list]
    assert texts[0].startswith("🔎")
    status.delete.assert_awaited()
    assert any("21.12.2026" in t and "487,00 €" in t for t in texts)
    assert any("не юридическая консультация" in t for t in texts)
    assert downloaded and not downloaded[0].exists()  # temp photo removed
    # language buttons are attached to the last message
    assert msg.answer.call_args_list[-1].kwargs["reply_markup"] is not None


async def test_pdf_is_politely_refused():
    botmod.assistant = LetterAssistant(analyzer=RuleAnalyzer())
    msg = SimpleNamespace(from_user=SimpleNamespace(id=1), answer=AsyncMock(),
                          document=SimpleNamespace(mime_type="application/pdf", file_id="x", file_size=10))
    await botmod.on_document(msg)
    assert "PDF" in msg.answer.call_args.args[0]
