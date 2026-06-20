"""Root-level launcher for the SEKSOV Telegram bot.

Use this file when you want the simplest possible command from the
repository root:

    python run.py

The package entry point `seksov-bot` remains available after installing the
project with `pip install -e .`.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from seksov_bot.main import main


if __name__ == "__main__":
    main()
