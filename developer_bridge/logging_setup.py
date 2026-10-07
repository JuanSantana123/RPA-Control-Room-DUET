from __future__ import annotations

import logging

from developer_bridge.config import DEVELOPER_TOOLS_ROOT, LOG_FILE


def configure_logging() -> None:
    """Configura log local; pythonw.exe normalmente não possui console."""

    DEVELOPER_TOOLS_ROOT.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
        force=True,
    )
