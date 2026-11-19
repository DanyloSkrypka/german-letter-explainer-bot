"""Record the portfolio video (demo.mp4) and 3 screenshots from the local emulator.

Needs the emulator running with a fixed demo date and local rules:
    DEMO_TODAY=2026-11-19 LLM_ENABLED=0 .venv/bin/python -m app.web
Then:
    .venv/bin/python scripts/record_demo.py
Uses the installed Google Chrome (channel="chrome") and records frames through the Chrome DevTools screencast +
system ffmpeg, so no Playwright browser/ffmpeg download is needed.
"""
from __future__ import annotations

import base64
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "http://127.0.0.1:8091/"
W, H = 1440, 900

CURSOR_JS = """
(() => {
  const c = document.createElement('div');
  c.id = '__cursor';
  Object.assign(c.style, {position:'fixed', left:'0px', top:'0px', width:'22px', height:'22px', borderRadius:'50%',
    background:'rgba(255,255,255,.85)', border:'2px solid rgba(0,0,0,.55)', zIndex: 99999, pointerEvents:'none',
    transform:'translate(-50%,-50%)', transition:'width .12s, height .12s, background .12s',
    boxShadow:'0 2px 8px rgba(0,0,0,.35)'});
  document.addEventListener('DOMContentLoaded', () => document.body.appendChild(c));
  if (document.body) document.body.appendChild(c);
  window.addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; });
  window.addEventListener('mousedown', () => { c.style.width = c.style.height = '16px'; c.style.background = 'rgba(51,144,236,.9)'; });
  window.addEventListener('mouseup', () => { c.style.width = c.style.height = '22px'; c.style.background = 'rgba(255,255,255,.85)'; });
})();
"""


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="lettervid_"))
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1)
        ctx.add_init_script(CURSOR_JS)
        page = ctx.new_page()
        frames: list[tuple[float, Path]] = []
        cdp = ctx.new_cdp_session(page)

        def on_frame(ev):
            f = tmp / f"f{len(frames):05d}.jpg"
            f.write_bytes(base64.b64decode(ev["data"]))
            frames.append((ev["metadata"]["timestamp"], f))
            try:
                cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
            except Exception:
                pass

        cdp.on("Page.screencastFrame", on_frame)
        page.goto(URL)
        page.wait_for_timeout(800)
        cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": W, "maxHeight": H,
                                          "everyNthFrame": 1})
        page.wait_for_timeout(900)
        page.mouse.move(W / 2, H / 2)

        def shot(name):
            page.evaluate("document.getElementById('__cursor').style.display='none'")
            page.screenshot(path=str(ROOT / name))
            page.evaluate("document.getElementById('__cursor').style.display=''")

        def step(n):
            page.evaluate(f"window.demo.setStep({n})")

        def click(loc, pause=350):
            box = loc.bounding_box()
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=18)
            page.wait_for_timeout(120)
            page.mouse.down()
            page.wait_for_timeout(70)
            page.mouse.up()
            page.wait_for_timeout(pause)

        def count():
            return page.locator(".row.in").count()

        def wait_in(n, extra=700):
            page.wait_for_function(f"document.querySelectorAll('.row.in').length >= {n}")
            page.wait_for_timeout(extra)

        def type_send(text):
            inp = page.locator("#inp")
            click(inp, 150)
            inp.type(text, delay=60)
            page.wait_for_timeout(250)
            click(page.locator("#send"), 100)

        def smooth_scroll(px, steps=6, pause=650):
            for _ in range(steps):
                page.evaluate(f"window.demo.scrollChatBy({px // steps})")
                page.wait_for_timeout(pause)

        def send_letter(title_part):
            click(page.locator("#clip"), 600)
            click(page.locator(".tile", has_text=title_part), 450)
            return

        page.set_default_timeout(20000)
        try:
            # 1. /start -> greeting, RDG disclaimer, language buttons
            step(1)
            n = count()
            type_send("/start")
            wait_in(n + 3, 1500)
            click(page.locator(".kb button", has_text="Русский").last, 200)
            wait_in(n + 4, 900)

            # 2. attach a letter from the gallery
            step(2)
            send_letter("Krankenkasse")
            shot("screenshot-1-gallery.png")
            page.wait_for_timeout(300)
            click(page.locator("#sendphoto"), 200)

            # 3. OCR runs (scan animation on the right)
            step(3)
            page.wait_for_function("document.querySelector('#f-sender.hit')")  # answer arrived
            page.wait_for_timeout(1400)

            # 4. deadline + amount with quotes
            step(4)
            page.mouse.move(W - 60, H - 60, steps=12)
            page.wait_for_timeout(1600)
            shot("screenshot-2-answer-ru.png")
            smooth_scroll(330, steps=4, pause=700)

            # 5. steps + German draft + disclaimer
            step(5)
            page.wait_for_timeout(600)
            smooth_scroll(520, steps=6, pause=650)
            page.wait_for_timeout(900)
            smooth_scroll(600, steps=5, pause=600)
            page.wait_for_timeout(1200)

            # 6. switch to Ukrainian from the last message, send the landlord letter
            step(6)
            n = count()
            click(page.locator(".kb button", has_text="Українська").last, 200)
            wait_in(n + 1, 800)
            send_letter("Nebenkosten")
            click(page.locator("#sendphoto"), 200)
            page.wait_for_function("document.querySelector('#f-sender.hit')")
            page.wait_for_timeout(2600)
            smooth_scroll(420, steps=5, pause=650)
            page.wait_for_timeout(500)
            smooth_scroll(520, steps=5, pause=600)
            page.wait_for_timeout(700)
            shot("screenshot-3-answer-ua-draft.png")
            page.wait_for_timeout(1800)

        except Exception:
            page.screenshot(path=str(tmp.parent / "record_fail.png"))
            print("FAILED, screenshot:", tmp.parent / "record_fail.png")
            raise
        cdp.send("Page.stopScreencast")
        page.wait_for_timeout(300)
        ctx.close()
        browser.close()

    # screencast frames come only when the page changes -> concat with real durations, resample to 30 fps
    lst = tmp / "frames.txt"
    with lst.open("w") as f:
        for i, (ts, path) in enumerate(frames):
            dur = (frames[i + 1][0] - ts) if i + 1 < len(frames) else 2.0
            f.write(f"file '{path}'\nduration {max(dur, 0.001):.4f}\n")
        f.write(f"file '{frames[-1][1]}'\n")
    out = ROOT / "demo.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-vf", f"fps=30,scale={W}:{H}:flags=lanczos,format=yuv420p", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "18", "-movflags", "+faststart", str(out)], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("saved", out)


if __name__ == "__main__":
    sys.exit(main())
