"""Telegram bot (aiogram 3). Long polling; run:  .venv/bin/python -m app.bot

Needs BOT_TOKEN in .env. Optional ANTHROPIC_API_KEY enables Claude analysis; without it the free local rules run.
Privacy: the photo is downloaded to a temp file, read, answered and deleted. Nothing about the letter is logged.
"""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

from .core import LetterAssistant, Out

log = logging.getLogger("letter-bot")
router = Router()
assistant: LetterAssistant | None = None
MAX_BYTES = 15 * 1024 * 1024


def kb(out: Out) -> InlineKeyboardMarkup | None:
    if not out.buttons:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d)
                                                  for t, d in out.buttons]])


async def send_all(msg: Message, outs: list[Out]) -> None:
    for o in outs:
        await msg.answer(o.text, reply_markup=kb(o))


def uid(msg: Message | CallbackQuery) -> str:
    return str(msg.from_user.id)


@router.message(CommandStart())
async def on_start(msg: Message):
    await send_all(msg, assistant.start(uid(msg), msg.from_user.language_code))


@router.message(Command("lang"))
async def on_lang(msg: Message):
    await send_all(msg, assistant.choose_lang(uid(msg)))


@router.callback_query(F.data.startswith("lang:"))
async def on_lang_pick(cb: CallbackQuery):
    outs = assistant.set_lang(uid(cb), cb.data.split(":", 1)[1])
    await cb.answer()
    await send_all(cb.message, outs)


async def _process(msg: Message, file_id: str, size: int | None):
    user = uid(msg)
    if size and size > MAX_BYTES:
        await send_all(msg, assistant.text(user))
        return
    status = await msg.answer(assistant.reading(user))
    await msg.bot.send_chat_action(msg.chat.id, ChatAction.TYPING)
    fd, tmp = tempfile.mkstemp(prefix="letter_", suffix=".img")
    os.close(fd)
    try:
        await msg.bot.download(file_id, destination=tmp)
        outs = await assistant.handle_image(user, tmp)  # deletes tmp
    finally:
        Path(tmp).unlink(missing_ok=True)
    await status.delete()
    await send_all(msg, outs)


@router.message(F.photo)
async def on_photo(msg: Message):
    p = msg.photo[-1]  # largest size
    await _process(msg, p.file_id, p.file_size)


@router.message(F.document)
async def on_document(msg: Message):
    mime = msg.document.mime_type or ""
    if mime.startswith("image/"):
        await _process(msg, msg.document.file_id, msg.document.file_size)
    elif mime == "application/pdf":
        await send_all(msg, assistant.pdf(uid(msg)))
    else:
        await send_all(msg, assistant.text(uid(msg)))


@router.message()
async def on_other(msg: Message):
    await send_all(msg, assistant.text(uid(msg)))


async def main() -> None:
    global assistant
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("BOT_TOKEN is not set (copy .env.example to .env)")
    assistant = LetterAssistant()
    log.info("analyzer: %s", assistant.analyzer.name)
    bot = Bot(token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
