import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"

# tests always use the free local rules, never a paid API
os.environ["LLM_ENABLED"] = "0"


@pytest.fixture(scope="session")
def expected():
    return json.loads((SAMPLES / "expected.json").read_text(encoding="utf-8"))
