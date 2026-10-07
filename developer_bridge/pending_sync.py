from __future__ import annotations

import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator


STATE_VERSION = 1
LOCK_RETRY_SECONDS = 0.05
LOCK_TIMEOUT_SECONDS = 10.0


class PendingSyncStore:
    """
    Fila persistente das alterações locais que ainda precisam chegar
    ao Workspace oficial do DUET.

    O arquivo fica dentro de .duet, portanto:
    - não faz parte do código do Robot;
    - não é enviado ao Control Room;
    - sobrevive a reinício do Bridge e da IDE.

    As operações armazenam somente metadados. Para um arquivo alterado,
    o conteúdo continua sendo o próprio arquivo local do Workspace.
    """

    def __init__(
        self,
        workspace: Path,
    ) -> None:
        self.workspace = workspace.resolve()
        self.state_dir = self.workspace / ".duet"
        self.state_file = self.state_dir / "pending_changes.json"
        self.lock_file = self.state_dir / "pending_changes.lock"
        self._thread_lock = threading.RLock()

    # ============================================================
    # LOCK ENTRE THREADS / PROCESSOS
    # ============================================================

    @contextmanager
    def _process_lock(self) -> Iterator[None]:
        """
        Serializa alterações no JSON inclusive quando dois processos
        do Developer Bridge acessam o mesmo Workspace.

        Windows usa msvcrt; outros sistemas usam fcntl.
        """

        self.state_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        handle = self.lock_file.open("a+b")

        try:
            # O byte bloqueado precisa existir.
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()

            deadline = (
                time.monotonic()
                + LOCK_TIMEOUT_SECONDS
            )

            while True:
                try:
                    handle.seek(0)

                    if os.name == "nt":
                        import msvcrt

                        msvcrt.locking(
                            handle.fileno(),
                            msvcrt.LK_NBLCK,
                            1,
                        )
                    else:
                        import fcntl

                        fcntl.flock(
                            handle.fileno(),
                            fcntl.LOCK_EX
                            | fcntl.LOCK_NB,
                        )

                    break

                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            "Não foi possível bloquear o estado "
                            "de sincronização do Developer Bridge."
                        )

                    time.sleep(
                        LOCK_RETRY_SECONDS
                    )

            try:
                yield
            finally:
                handle.seek(0)

                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(
                        handle.fileno(),
                        msvcrt.LK_UNLCK,
                        1,
                    )
                else:
                    import fcntl

                    fcntl.flock(
                        handle.fileno(),
                        fcntl.LOCK_UN,
                    )

        finally:
            handle.close()

    @contextmanager
    def _locked(self) -> Iterator[None]:
        with self._thread_lock:
            with self._process_lock():
                yield

    # ============================================================
    # PERSISTÊNCIA
    # ============================================================

    @staticmethod
    def _normalize_path(
        value: str,
    ) -> str:
        normalized = (
            str(value)
            .replace("\\", "/")
            .strip("/")
        )

        if (
            not normalized
            or normalized == "."
            or normalized.startswith("../")
            or "/../" in normalized
        ):
            raise ValueError(
                "Caminho inválido para sincronização pendente."
            )

        return normalized

    def _read_unlocked(self) -> list[dict]:
        if not self.state_file.exists():
            return []

        try:
            payload = json.loads(
                self.state_file.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            # Nunca descartamos silenciosamente um arquivo de estado
            # ilegível. A exceção deixa o problema visível no log.
            raise RuntimeError(
                "O estado de sincronização pendente está inválido: "
                f"{self.state_file}"
            )

        if payload.get("version") != STATE_VERSION:
            raise RuntimeError(
                "Versão de estado de sincronização não suportada."
            )

        operations = payload.get(
            "operations",
            [],
        )

        if not isinstance(
            operations,
            list,
        ):
            raise RuntimeError(
                "Lista de operações pendentes inválida."
            )

        return [
            operation
            for operation in operations
            if isinstance(
                operation,
                dict,
            )
        ]

    def _write_unlocked(
        self,
        operations: list[dict],
    ) -> None:
        self.state_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "version": STATE_VERSION,
            "updated_at": datetime.utcnow().isoformat(),
            "operations": operations,
        }

        temporary = self.state_file.with_suffix(
            ".json.tmp"
        )

        temporary.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        os.replace(
            temporary,
            self.state_file,
        )

    @staticmethod
    def _new_operation(
        *,
        kind: str,
        path: str,
    ) -> dict:
        return {
            "id": uuid.uuid4().hex,
            "kind": kind,
            "path": path,
            "queued_at": datetime.utcnow().isoformat(),
        }

    # ============================================================
    # OPERAÇÕES
    # ============================================================

    def queue_upsert_file(
        self,
        relative: str,
    ) -> None:
        relative = self._normalize_path(
            relative
        )

        with self._locked():
            operations = self._read_unlocked()

            # A versão mais recente do arquivo local é a única que
            # interessa. Removemos saves antigos e um delete anterior
            # do mesmo caminho caso o arquivo tenha sido recriado.
            operations = [
                operation
                for operation in operations
                if not (
                    operation.get("path") == relative
                    and operation.get("kind")
                    in {
                        "upsert_file",
                        "delete",
                    }
                )
            ]

            operations.append(
                self._new_operation(
                    kind="upsert_file",
                    path=relative,
                )
            )

            self._write_unlocked(
                operations
            )

    def queue_mkdir(
        self,
        relative: str,
    ) -> None:
        relative = self._normalize_path(
            relative
        )

        with self._locked():
            operations = self._read_unlocked()

            operations = [
                operation
                for operation in operations
                if not (
                    operation.get("path") == relative
                    and operation.get("kind")
                    in {
                        "mkdir",
                        "delete",
                    }
                )
            ]

            operations.append(
                self._new_operation(
                    kind="mkdir",
                    path=relative,
                )
            )

            self._write_unlocked(
                operations
            )

    def queue_delete(
        self,
        relative: str,
    ) -> None:
        relative = self._normalize_path(
            relative
        )

        prefix = f"{relative}/"

        with self._locked():
            operations = self._read_unlocked()

            # Se uma pasta/arquivo foi removido localmente, alterações
            # pendentes dentro desse mesmo caminho deixam de fazer sentido.
            operations = [
                operation
                for operation in operations
                if not (
                    operation.get("path") == relative
                    or str(
                        operation.get(
                            "path",
                            "",
                        )
                    ).startswith(
                        prefix
                    )
                )
            ]

            operations.append(
                self._new_operation(
                    kind="delete",
                    path=relative,
                )
            )

            self._write_unlocked(
                operations
            )

    def list_operations(
        self,
    ) -> list[dict]:
        with self._locked():
            return list(
                self._read_unlocked()
            )

    def remove(
        self,
        operation_id: str,
    ) -> None:
        with self._locked():
            operations = self._read_unlocked()

            operations = [
                operation
                for operation in operations
                if operation.get("id")
                != operation_id
            ]

            self._write_unlocked(
                operations
            )

    def count(
        self,
    ) -> int:
        with self._locked():
            return len(
                self._read_unlocked()
            )
