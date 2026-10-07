from __future__ import annotations

import os
from pathlib import Path


def _local_app_data() -> Path:
    value = os.environ.get("LOCALAPPDATA")

    if value:
        return Path(value)

    return Path.home() / ".duet"


DUET_LOCAL_ROOT = _local_app_data() / "DUET"
WORKSPACES_ROOT = DUET_LOCAL_ROOT / "Workspaces"
DEVELOPER_TOOLS_ROOT = DUET_LOCAL_ROOT / "DeveloperTools"
LOG_FILE = DEVELOPER_TOOLS_ROOT / "bridge.log"


def workspace_root(project_id: int) -> Path:
    """Workspace físico local de um AutomationProject."""

    return WORKSPACES_ROOT / str(project_id)
