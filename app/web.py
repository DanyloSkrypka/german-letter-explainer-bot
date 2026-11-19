"""Local Telegram-style emulator for the portfolio demo. Same core as the real bot.

Run:  .venv/bin/python -m app.web   ->  http://127.0.0.1:8091/
Binds to 127.0.0.1 only. Uploaded images go to a temp file and are deleted right after the answer.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import asdict
from datetime import date
from pathlib import Path

from aiohttp import web
from dotenv import load_dotenv

from .core import LetterAssistant

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"
MAX_BYTES = 15 * 1024 * 1024


def make_app(assistant: LetterAssistant | None = None) -> web.Application:
    load_dotenv()
    demo_today = os.getenv("DEMO_TODAY")  # e.g. 2026-11-19 so "days left" in the video stays stable
    assistant = assistant or LetterAssistant(
        today_fn=(lambda: date.fromisoformat(demo_today)) if demo_today else date.today)
    app = web.Application(client_max_size=MAX_BYTES)

    def reply(outs, **extra):
        return web.json_response({"messages": [asdict(o) for o in outs], **extra})

    async def index(_):
        return web.FileResponse(ROOT / "demo" / "index.html")

    async def start(req):
        d = await req.json()
        return reply(assistant.start(d.get("user", "demo"), d.get("lang_code")))

    async def command(req):
        d = await req.json()
        user = d.get("user", "demo")
        if d.get("callback", "").startswith("lang:"):
            return reply(assistant.set_lang(user, d["callback"].split(":", 1)[1]))
        if d.get("text", "").strip() == "/lang":
            return reply(assistant.choose_lang(user))
        if d.get("text", "").strip() == "/start":
            return reply(assistant.start(user))
        return reply(assistant.text(user))

    async def photo(req):
        fd, tmp = tempfile.mkstemp(prefix="letter_", suffix=".img")
        os.close(fd)
        if req.content_type.startswith("multipart/"):
            form = await req.post()
            user = str(form.get("user", "demo"))
            f = form.get("file")
            if f is None:
                Path(tmp).unlink(missing_ok=True)
                return web.json_response({"error": "no file"}, status=400)
            with open(tmp, "wb") as out:
                shutil.copyfileobj(f.file, out)
        else:
            d = await req.json()
            user = d.get("user", "demo")
            name = Path(d.get("sample", "")).name  # no path traversal
            src = SAMPLES / name
            if not src.is_file() or src.suffix not in (".png", ".jpg"):
                Path(tmp).unlink(missing_ok=True)
                return web.json_response({"error": "unknown sample"}, status=404)
            shutil.copy(src, tmp)  # the sample itself stays; the copy is processed and deleted
        outs, facts = await assistant.handle_image_facts(user, tmp)
        return reply(outs, deleted=not Path(tmp).exists(), facts=facts)

    async def samples(_):
        import json
        exp = json.loads((SAMPLES / "expected.json").read_text(encoding="utf-8"))
        return web.json_response([{"id": k, "title": v["title"], "photo": f"/samples/{k}_photo.jpg"}
                                  for k, v in exp.items()])

    app.router.add_get("/", index)
    app.router.add_get("/demo/", index)
    app.router.add_post("/api/emu/start", start)
    app.router.add_post("/api/emu/send", command)
    app.router.add_post("/api/emu/photo", photo)
    app.router.add_get("/api/emu/samples", samples)
    app.router.add_static("/samples/", SAMPLES)
    return app


if __name__ == "__main__":
    web.run_app(make_app(), host="127.0.0.1", port=int(os.getenv("PORT", "8091")))
