from __future__ import annotations

import logging
import shutil
import threading
from datetime import datetime
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler, FileSystemMovedEvent
from watchdog.observers import Observer

from developer_bridge.api_client import DuetApiClient, DuetApiError
from developer_bridge.pending_sync import PendingSyncStore


logger = logging.getLogger("duet.developer_bridge.sync")

IGNORED_PARTS = {
    ".duet",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "dist",
    "build",
}

IGNORED_SUFFIXES = {".pyc", ".pyo"}
DEBOUNCE_SECONDS = 0.45


def _flatten_tree(nodes: list[dict]) -> tuple[set[str], set[str]]:
    folders: set[str] = set()
    files: set[str] = set()

    def visit(items: list[dict]) -> None:
        for node in items:
            path = str(node.get("id", ""))
            node_type = node.get("type")

            if not path or node_type not in ("file", "folder"):
                continue

            if node_type == "folder":
                folders.add(path)
                visit(node.get("children") or [])
            else:
                files.add(path)

    visit(nodes)
    return folders, files


class WorkspaceSync:
    """Sincroniza automaticamente filesystem local -> Workspace DUET."""

    def __init__(self, api: DuetApiClient, workspace: Path):
        self.api = api
        self.workspace = workspace.resolve()
        self._observer: Observer | None = None
        self._timers: dict[str, threading.Timer] = {}
        self._timers_lock = threading.Lock()

        # Alterações locais que ainda não chegaram ao Control Room.
        # O estado é persistido em .duet/pending_changes.json.
        self._pending = PendingSyncStore(
            self.workspace
        )

        # Evita dois flushes concorrentes vindos do watcher e do
        # loop de reconexão do Bridge.
        self._flush_lock = threading.Lock()

    def _relative(self, path: str | Path) -> str:
        return (
            Path(path)
            .resolve()
            .relative_to(self.workspace)
            .as_posix()
        )

    def _ignored(self, path: str | Path) -> bool:
        try:
            relative = Path(path).resolve().relative_to(self.workspace)
        except ValueError:
            return True

        if any(part in IGNORED_PARTS for part in relative.parts):
            return True

        return relative.suffix.lower() in IGNORED_SUFFIXES

    def _backup_local_file(self, relative: str, local_file: Path) -> None:
        """Preserva conteúdo local divergente antes do pull sobrescrever."""

        recovery_root = (
            self.workspace
            / ".duet"
            / "recovery"
            / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        )
        destination = recovery_root / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_file, destination)
        logger.warning("Cópia local preservada em %s", destination)

    def _preserve_stale_local_path(
        self,
        *,
        relative: str,
        local_path: Path,
        recovery_root: Path,
    ) -> None:
        """
        Move para recovery um item local que deixou de existir no
        Workspace oficial.

        O Control Room continua sendo a fonte oficial, mas nenhum
        conteúdo local é apagado definitivamente durante a reconciliação.
        """

        if not local_path.exists():
            return

        destination = (
            recovery_root
            / Path(relative)
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.move(
            str(local_path),
            str(destination),
        )

        logger.warning(
            (
                "Item local removido por não existir no Control Room "
                "e preservado em recovery: %s"
            ),
            destination,
        )

    def _cleanup_stale_local_items(
        self,
        *,
        remote_folders: set[str],
        remote_files: set[str],
    ) -> None:
        """
        Remove da cópia local itens que não existem mais no Workspace
        oficial.

        Regras de segurança:
        - caminhos ignorados pelo Bridge nunca são removidos;
        - diretórios obsoletos são tratados pela raiz para evitar
          backups duplicados;
        - todo item removido é movido antes para .duet/recovery.
        """

        recovery_root = (
            self.workspace
            / ".duet"
            / "recovery"
            / datetime.now().strftime(
                "%Y%m%d-%H%M%S-%f"
            )
        )

        # --------------------------------------------------------
        # 1. DIRETÓRIOS QUE NÃO EXISTEM MAIS REMOTAMENTE
        # --------------------------------------------------------
        local_folders: set[str] = set()

        for local_path in self.workspace.rglob("*"):

            if (
                not local_path.exists()
                or not local_path.is_dir()
                or self._ignored(local_path)
            ):
                continue

            local_folders.add(
                self._relative(local_path)
            )

        stale_folders = (
            local_folders
            - remote_folders
        )

        # Mantém somente as raízes obsoletas. Se "a" já será removida,
        # não precisamos processar também "a/b" e "a/b/c".
        stale_roots: list[str] = []

        for relative in sorted(
            stale_folders,
            key=lambda value: (
                value.count("/"),
                value.lower(),
            ),
        ):
            parts = Path(relative).parts

            if any(
                parts[:len(Path(root).parts)]
                == Path(root).parts
                for root in stale_roots
            ):
                continue

            stale_roots.append(
                relative
            )

        for relative in stale_roots:

            local_path = (
                self.workspace
                / relative
            )

            self._preserve_stale_local_path(
                relative=relative,
                local_path=local_path,
                recovery_root=recovery_root,
            )

        # --------------------------------------------------------
        # 2. ARQUIVOS AVULSOS QUE NÃO EXISTEM MAIS REMOTAMENTE
        # --------------------------------------------------------
        #
        # Fazemos um novo scan depois dos diretórios porque arquivos
        # internos de uma pasta já movida para recovery não existem
        # mais no local original e não devem gerar backup duplicado.
        # --------------------------------------------------------
        for local_path in list(
            self.workspace.rglob("*")
        ):

            if (
                not local_path.exists()
                or not local_path.is_file()
                or self._ignored(local_path)
            ):
                continue

            relative = self._relative(
                local_path
            )

            if relative in remote_files:
                continue

            self._preserve_stale_local_path(
                relative=relative,
                local_path=local_path,
                recovery_root=recovery_root,
            )

    def initial_pull(self) -> None:
        """
        Materializa o Workspace oficial antes de iniciar o watcher.

        Por segurança, um pull remoto nunca começa enquanto existirem
        alterações locais pendentes. O chamador deve tentar flush_pending()
        primeiro. Isso evita sobrescrever código local que ainda não chegou
        ao Control Room.
        """

        pending = self.pending_count()

        if pending > 0:
            raise RuntimeError(
                (
                    "Pull remoto bloqueado: existem "
                    f"{pending} alteração(ões) local(is) pendente(s)."
                )
            )

        self.workspace.mkdir(parents=True, exist_ok=True)
        folders, files = _flatten_tree(self.api.get_tree())

        for relative in sorted(
            folders,
            key=lambda value: (value.count("/"), value.lower()),
        ):
            local_folder = self.workspace / relative
            if not self._ignored(local_folder):
                local_folder.mkdir(parents=True, exist_ok=True)

        for relative in sorted(files):
            local_file = self.workspace / relative

            if self._ignored(local_file):
                continue

            try:
                content = self.api.get_file(relative)
            except DuetApiError as error:
                if error.status_code == 415:
                    logger.info("Arquivo não textual ignorado: %s", relative)
                    continue
                raise

            local_file.parent.mkdir(parents=True, exist_ok=True)

            if local_file.exists():
                try:
                    current = local_file.read_text(encoding="utf-8")
                    if current != content:
                        self._backup_local_file(relative, local_file)
                except UnicodeDecodeError:
                    self._backup_local_file(relative, local_file)

            with local_file.open("w", encoding="utf-8", newline="") as file:
                file.write(content)

        # Depois de materializar o estado remoto atual, removemos da
        # cópia local tudo que deixou de existir no Control Room.
        #
        # Antes de remover, o conteúdo é movido para .duet/recovery.
        self._cleanup_stale_local_items(
            remote_folders=folders,
            remote_files=files,
        )

        logger.info("Workspace inicial sincronizado: %s", self.workspace)

    def _ensure_remote_parents(self, relative: str) -> None:
        parent = Path(relative).parent
        if str(parent) in ("", "."):
            return

        current = Path()
        for part in parent.parts:
            current = current / part
            remote_path = current.as_posix()
            try:
                self.api.create_folder(remote_path)
            except DuetApiError as error:
                if error.status_code != 409:
                    raise

    def _sync_file_remote(
        self,
        path: Path,
    ) -> None:
        """
        Envia um arquivo ao Control Room.

        Esta função não altera a fila persistente; ela é usada somente
        pelo flush de operações já registradas.
        """

        if not path.exists() or not path.is_file() or self._ignored(path):
            return

        relative = self._relative(path)

        try:
            content = path.read_text(
                encoding="utf-8"
            )
        except UnicodeDecodeError:
            logger.info(
                "Arquivo local não textual ignorado: %s",
                relative,
            )
            return

        try:
            self.api.save_file(
                relative,
                content,
            )
        except DuetApiError as error:
            if error.status_code != 404:
                raise

            self._ensure_remote_parents(
                relative
            )

            try:
                self.api.create_file(
                    relative
                )
            except DuetApiError as create_error:
                if create_error.status_code != 409:
                    raise

            self.api.save_file(
                relative,
                content,
            )

        logger.info(
            "Arquivo sincronizado: %s",
            relative,
        )

    def _schedule_file_sync(self, path: Path) -> None:
        if self._ignored(path):
            return

        key = str(path.resolve()).lower()

        with self._timers_lock:
            previous = self._timers.pop(key, None)
            if previous:
                previous.cancel()

            timer = threading.Timer(
                DEBOUNCE_SECONDS,
                self._run_scheduled_sync,
                args=(key, path),
            )
            timer.daemon = True
            self._timers[key] = timer
            timer.start()

    def _run_scheduled_sync(self, key: str, path: Path) -> None:
        try:
            if (
                path.exists()
                and path.is_file()
                and not self._ignored(path)
            ):
                self._pending.queue_upsert_file(
                    self._relative(path)
                )

                self.flush_pending()

        except Exception:
            logger.exception(
                "Falha ao registrar/sincronizar arquivo: %s",
                path,
            )
        finally:
            with self._timers_lock:
                self._timers.pop(key, None)

    def _create_folder_remote(
        self,
        relative: str,
    ) -> None:
        """Cria uma pasta remotamente de forma idempotente."""

        self._ensure_remote_parents(
            f"{relative}/placeholder"
        )

        try:
            self.api.create_folder(
                relative
            )
        except DuetApiError as error:
            if error.status_code != 409:
                raise

    def _delete_remote_relative(
        self,
        relative: str,
    ) -> None:
        """Remove um item remoto de forma idempotente."""

        if not relative:
            return

        try:
            self.api.delete_item(
                relative,
                recursive=True,
            )
        except DuetApiError as error:
            # O item pode já ter sido removido por uma operação anterior.
            if error.status_code != 404:
                raise

    def pending_count(
        self,
    ) -> int:
        """Quantidade de alterações locais ainda não confirmadas no DUET."""

        return self._pending.count()

    def flush_pending(
        self,
    ) -> bool:
        """
        Tenta enviar operações pendentes na ordem em que foram registradas.

        Retorna True somente quando a fila termina vazia.

        Se Control Room, rede, sessão ou autorização estiver indisponível,
        a operação permanece no JSON e será tentada novamente depois.
        """

        if not self._flush_lock.acquire(
            blocking=False
        ):
            return self.pending_count() == 0

        try:
            operations = (
                self._pending.list_operations()
            )

            for operation in operations:
                operation_id = str(
                    operation.get(
                        "id",
                        "",
                    )
                )

                kind = str(
                    operation.get(
                        "kind",
                        "",
                    )
                )

                relative = str(
                    operation.get(
                        "path",
                        "",
                    )
                )

                if (
                    not operation_id
                    or not kind
                    or not relative
                ):
                    # Estado inválido não é descartado silenciosamente.
                    raise RuntimeError(
                        "Operação pendente inválida."
                    )

                try:
                    if kind == "upsert_file":
                        local_path = (
                            self.workspace
                            / relative
                        )

                        # Se o arquivo deixou de existir, uma operação
                        # posterior de delete será responsável pelo remoto.
                        if not local_path.exists():
                            self._pending.remove(
                                operation_id
                            )
                            continue

                        self._sync_file_remote(
                            local_path
                        )

                    elif kind == "mkdir":
                        local_path = (
                            self.workspace
                            / relative
                        )

                        if not local_path.exists():
                            self._pending.remove(
                                operation_id
                            )
                            continue

                        self._create_folder_remote(
                            relative
                        )

                    elif kind == "delete":
                        self._delete_remote_relative(
                            relative
                        )

                    else:
                        raise RuntimeError(
                            (
                                "Tipo de operação pendente "
                                f"desconhecido: {kind}"
                            )
                        )

                except DuetApiError as error:
                    logger.warning(
                        (
                            "Sincronização pendente mantida | "
                            "path=%s | status=%s | erro=%s"
                        ),
                        relative,
                        error.status_code,
                        error,
                    )

                    # Mantém esta e todas as seguintes para retry.
                    break

                except Exception:
                    logger.exception(
                        (
                            "Falha ao processar sincronização pendente | "
                            "path=%s"
                        ),
                        relative,
                    )

                    break

                else:
                    self._pending.remove(
                        operation_id
                    )

            return (
                self.pending_count()
                == 0
            )

        finally:
            self._flush_lock.release()

    def _create_folder_now(
        self,
        path: Path,
    ) -> None:
        if self._ignored(path):
            return

        relative = self._relative(
            path
        )

        self._pending.queue_mkdir(
            relative
        )

        self.flush_pending()

    def _delete_remote_now(
        self,
        path: Path,
    ) -> None:
        if self._ignored(path):
            return

        relative = self._relative(
            path
        )

        if not relative:
            return

        # Primeiro persistimos a intenção de remoção. Se a rede cair
        # logo depois, a operação não desaparece.
        self._pending.queue_delete(
            relative
        )

        self.flush_pending()

    def _queue_upload_path(
        self,
        path: Path,
    ) -> None:
        """
        Registra criação/alteração de um arquivo ou árvore inteira sem
        depender de a rede estar disponível naquele momento.
        """

        if not path.exists() or self._ignored(path):
            return

        if path.is_file():
            self._pending.queue_upsert_file(
                self._relative(path)
            )
            return

        self._pending.queue_mkdir(
            self._relative(path)
        )

        for child in path.rglob("*"):
            if self._ignored(child):
                continue

            relative = self._relative(
                child
            )

            if child.is_dir():
                self._pending.queue_mkdir(
                    relative
                )
            elif child.is_file():
                self._pending.queue_upsert_file(
                    relative
                )

    def _handle_move(
        self,
        event: FileSystemMovedEvent,
    ) -> None:
        """
        Move/rename é persistido como:
            1. materialização do destino;
            2. remoção da origem.

        Essa ordem impede que uma falha de rede apague o remoto antigo
        antes de o novo conteúdo estar garantido.
        """

        source = Path(
            event.src_path
        )

        destination = Path(
            event.dest_path
        )

        if (
            self._ignored(source)
            and self._ignored(destination)
        ):
            return

        source_relative = self._relative(
            source
        )

        self._queue_upload_path(
            destination
        )

        self._pending.queue_delete(
            source_relative
        )

        self.flush_pending()

    def start(self) -> Observer:
        handler = _WorkspaceEventHandler(self)
        observer = Observer()
        observer.schedule(handler, str(self.workspace), recursive=True)
        observer.start()
        self._observer = observer
        logger.info("Watcher iniciado: %s", self.workspace)
        return observer

    def stop(self) -> None:
        with self._timers_lock:
            timers = list(self._timers.values())
            self._timers.clear()

        for timer in timers:
            timer.cancel()

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None


class _WorkspaceEventHandler(FileSystemEventHandler):
    def __init__(self, sync: WorkspaceSync):
        super().__init__()
        self.sync = sync

    def on_created(self, event: FileSystemEvent) -> None:
        path = Path(event.src_path)
        if self.sync._ignored(path):
            return

        try:
            if event.is_directory:
                self.sync._create_folder_now(path)
            else:
                self.sync._schedule_file_sync(path)
        except Exception:
            logger.exception("Falha ao tratar criação local: %s", path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self.sync._schedule_file_sync(Path(event.src_path))

    def on_deleted(self, event: FileSystemEvent) -> None:
        path = Path(event.src_path)
        try:
            self.sync._delete_remote_now(path)
        except Exception:
            logger.exception("Falha ao tratar exclusão local: %s", path)

    def on_moved(self, event: FileSystemMovedEvent) -> None:
        try:
            self.sync._handle_move(event)
        except Exception:
            logger.exception(
                "Falha ao tratar movimentação local: %s -> %s",
                event.src_path,
                event.dest_path,
            )
