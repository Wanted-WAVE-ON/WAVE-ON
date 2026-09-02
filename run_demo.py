from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if __name__ == "__main__":
    os.chdir(ROOT)
    uvicorn.run(
        "silent_orchestra.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        app_dir=str(SRC),
    )
