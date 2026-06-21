"""Root-level launcher for the SEKSOV Telegram Mini App web server.

Use locally with:

    python run_web.py

For Telegram Mini App production use, expose it through HTTPS and put the
public URL into WEB_APP_URL in .env.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from seksov_bot.web_main import main


if __name__ == "__main__":
    main()
