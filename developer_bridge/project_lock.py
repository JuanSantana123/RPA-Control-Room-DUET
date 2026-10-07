from __future__ import annotations

import msvcrt
from pathlib import Path


class ProjectBridgeLock:
    """Evita dois watchers concorrentes para o mesmo projeto."""

    def __init__(self, workspace: Path):
        self.meta_dir = workspace / ".duet"
        self.path = self.meta_dir / "bridge.lock"
        self.handle = None

    def acquire(self) -> bool:
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+b")
        self.handle.seek(0)

        if self.path.stat().st_size == 0:
            self.handle.write(b"0")
            self.handle.flush()

        self.handle.seek(0)

        try:
            msvcrt.locking(
                self.handle.fileno(),
                msvcrt.LK_NBLCK,
                1,
            )
            return True
        except OSError:
            self.handle.close()
            self.handle = None
            return False

    def release(self) -> None:
        if not self.handle:
            return

        try:
            self.handle.seek(0)
            msvcrt.locking(
                self.handle.fileno(),
                msvcrt.LK_UNLCK,
                1,
            )
        finally:
            self.handle.close()
            self.handle = None
