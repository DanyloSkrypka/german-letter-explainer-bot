"""Emulator API: sample letter end-to-end, path traversal blocked, upload deleted."""
from datetime import date
from pathlib import Path

from aiohttp import FormData
from aiohttp.test_utils import TestClient, TestServer

from app.analyzer import RuleAnalyzer
from app.core import LetterAssistant
from app.web import make_app

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


async def client():
    app = make_app(LetterAssistant(analyzer=RuleAnalyzer(), today_fn=lambda: date(2026, 11, 19)))
    c = TestClient(TestServer(app))
    await c.start_server()
    return c


async def test_sample_photo_flow():
    c = await client()
    try:
        r = await c.post("/api/emu/send", json={"user": "w", "callback": "lang:uk"})
        assert "українська" in (await r.json())["messages"][0]["text"]
        r = await c.post("/api/emu/photo", json={"user": "w", "sample": "05_auslaenderbehoerde_photo.jpg"})
        d = await r.json()
        assert d["deleted"] is True
        assert d["facts"] == {"sender": "auslaenderbehoerde", "deadline": "08.12.2026", "amount": "93,00 €",
                              "engine": "rules"}
        assert "08.12.2026, 09:30" in d["messages"][0]["text"]
        assert (SAMPLES / "05_auslaenderbehoerde_photo.jpg").exists()  # original sample untouched
    finally:
        await c.close()


async def test_path_traversal_blocked():
    c = await client()
    try:
        r = await c.post("/api/emu/photo", json={"user": "w", "sample": "../app/web.py"})
        assert r.status == 404
    finally:
        await c.close()


async def test_upload_own_photo():
    c = await client()
    try:
        fd = FormData()
        fd.add_field("user", "w")
        fd.add_field("file", (SAMPLES / "01_jobcenter_photo.jpg").read_bytes(), filename="x.jpg",
                     content_type="image/jpeg")
        d = await (await c.post("/api/emu/photo", data=fd)).json()
        assert d["deleted"] and d["facts"]["sender"] == "jobcenter" and d["facts"]["amount"] == ""
    finally:
        await c.close()
