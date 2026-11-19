"""Local, free OCR. Tesseract (German) first; macOS Vision (pyobjc) as a fallback.

Nothing leaves the machine. The caller deletes the image afterwards.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL_TESSDATA = ROOT / "tessdata"


class OCRError(RuntimeError):
    pass


def _tessdata_dir() -> str | None:
    env = os.getenv("TESSDATA_DIR")
    if env:
        return env
    if (LOCAL_TESSDATA / "deu.traineddata").exists():
        return str(LOCAL_TESSDATA)
    return None  # use tesseract's own folder (brew install tesseract-lang)


def tesseract_available() -> bool:
    return shutil.which(os.getenv("TESSERACT_CMD", "tesseract")) is not None


def ocr_tesseract(path: str | Path) -> str:
    # psm 6 (one uniform block) keeps table rows "label ... amount" on one line, also on slightly rotated photos
    psm = os.getenv("TESSERACT_PSM", "6")
    cmd = [os.getenv("TESSERACT_CMD", "tesseract"), str(path), "-", "-l", "deu", "--psm", psm]
    td = _tessdata_dir()
    if td:
        cmd += ["--tessdata-dir", td]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if r.returncode != 0:
        raise OCRError(r.stderr.strip()[:300] or "tesseract failed")
    return r.stdout


def ocr_vision(path: str | Path) -> str:  # pragma: no cover - macOS-only fallback
    """Apple Vision text recognition (needs `pip install pyobjc-framework-Vision`)."""
    try:
        import Quartz  # type: ignore
        import Vision  # type: ignore
        from Foundation import NSURL  # type: ignore
    except ImportError as e:
        raise OCRError("no OCR engine: install tesseract or pyobjc-framework-Vision") from e
    url = NSURL.fileURLWithPath_(str(path))
    src = Quartz.CGImageSourceCreateWithURL(url, None)
    img = Quartz.CGImageSourceCreateImageAtIndex(src, 0, None)
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLanguages_(["de-DE"])
    req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(img, None)
    ok, err = handler.performRequests_error_([req], None)
    if not ok:
        raise OCRError(str(err))
    lines = [obs.topCandidates_(1)[0].string() for obs in req.results()]
    return "\n".join(lines)


def ocr_image(path: str | Path) -> str:
    if tesseract_available():
        return ocr_tesseract(path)
    return ocr_vision(path)
