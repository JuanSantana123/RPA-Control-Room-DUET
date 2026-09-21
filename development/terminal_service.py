# ============================================================
# DEVELOPMENT - TERMINAL SERVICE
# ============================================================
#
# Responsável pelo terminal interativo do DUET Studio.
#
# RESPONSABILIDADES:
#
# - validar o AutomationProject;
# - exigir Checkout do próprio usuário;
# - utilizar o Workspace oficial do projeto;
# - iniciar um shell persistente dentro do Workspace;
# - enviar comandos/dados para o shell;
# - transmitir stdout/stderr para o Studio;
# - encerrar o processo quando o terminal for fechado.
#
# IMPORTANTE:
#
# Este módulo NÃO registra endpoints FastAPI/WebSocket.
# A camada HTTP/WebSocket ficará em api/development.py.
#
# O processo é iniciado SEM shell=True.
# O executável chamado é explicitamente cmd.exe.
#
# Como o mesmo processo cmd.exe permanece vivo durante toda a
# sessão, comandos como:
#
#     .venv\Scripts\activate
#
# continuam valendo para os próximos comandos daquela sessão.
# ============================================================

import asyncio
import logging
import os
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import AutomationProject

from development.checkout_service import (
    exigir_checkout_workspace,
)

from development.repository import (
    garantir_workspace,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

# Limite defensivo para dados enviados pelo navegador ao terminal.
#
# Isso evita que uma única mensagem WebSocket tente despejar uma
# quantidade arbitrária de dados no stdin do processo.
MAX_TERMINAL_INPUT_BYTES = 64 * 1024


# ============================================================
# SESSÃO DE TERMINAL
# ============================================================
class DevelopmentTerminalSession:
    """
    Representa uma sessão de terminal interativo do DUET Studio.

    No Windows utiliza pywinpty/ConPTY para que cmd.exe seja
    executado dentro de um pseudoterminal real.
    """

    def __init__(
        self,
        *,
        project_id: int,
        user_id: int,
        workspace_path: Path,
    ):
        """
        Inicializa os metadados da sessão.

        O pseudoterminal ainda não é criado aqui.
        """

        self.project_id = project_id
        self.user_id = user_id

        self.workspace_path = (
            workspace_path.resolve()
        )

        # Processo controlado pelo pywinpty.
        self.process = None

        self._closed = False


    # ========================================================
    # START
    # ========================================================

    async def start(self) -> None:
        """
        Inicia cmd.exe dentro de um pseudoterminal Windows.

        Como PtyProcess é uma API síncrona, operações bloqueantes
        são deslocadas para threads através de asyncio.to_thread().
        """

        if self.process is not None:
            return

        if self._closed:

            raise RuntimeError(
                "A sessão de terminal já foi encerrada."
            )


        # ----------------------------------------------------
        # VALIDA WORKSPACE
        # ----------------------------------------------------

        if not self.workspace_path.exists():

            raise RuntimeError(
                "Workspace do projeto não existe."
            )

        if not self.workspace_path.is_dir():

            raise RuntimeError(
                "Workspace do projeto é inválido."
            )


        # ----------------------------------------------------
        # SHELL WINDOWS
        # ----------------------------------------------------

        shell_executable = (
            os.environ.get("COMSPEC")
            or "cmd.exe"
        )


        try:

            # pywinpty fornece a integração com o
            # pseudoterminal nativo do Windows (ConPTY).
            from winpty import PtyProcess


            def _spawn_terminal():
                """
                Cria o pseudoterminal fora do event loop.

                cwd garante que o prompt já seja iniciado dentro
                do Workspace oficial do AutomationProject.
                """

                return PtyProcess.spawn(
                    shell_executable,
                    cwd=str(
                        self.workspace_path
                    ),
                )


            self.process = (
                await asyncio.to_thread(
                    _spawn_terminal
                )
            )


        except ImportError as error:

            raise RuntimeError(
                "O suporte ao terminal Windows requer "
                "a dependência 'pywinpty'."
            ) from error


        except Exception:

            logger.exception(
                "Falha ao iniciar terminal do Development",
                extra={
                    "event":
                        "development_terminal_start_failed",

                    "user_id":
                        self.user_id,

                    "project_id":
                        self.project_id,

                    "status":
                        "error",
                },
            )

            raise


        logger.info(
            "Terminal do Development iniciado",
            extra={
                "event":
                    "development_terminal_started",

                "user_id":
                    self.user_id,

                "project_id":
                    self.project_id,

                # PtyProcess não possui obrigatoriamente a mesma
                # interface de asyncio.subprocess.Process.
                "pid":
                    getattr(
                        self.process,
                        "pid",
                        None,
                    ),

                "status":
                    "success",
            },
        )


    # ========================================================
    # WRITE
    # ========================================================

    async def write(
        self,
        data: str,
    ) -> None:
        """
        Envia exatamente os caracteres recebidos do xterm para
        o pseudoterminal Windows.

        Isso inclui caracteres normais, Enter, Backspace e
        sequências de controle.
        """

        if self._closed:

            raise RuntimeError(
                "A sessão de terminal está encerrada."
            )

        process = self.process

        if process is None:

            raise RuntimeError(
                "O terminal ainda não foi iniciado."
            )

        if not process.isalive():

            raise RuntimeError(
                "O processo do terminal já foi finalizado."
            )


        # ----------------------------------------------------
        # LIMITE DE ENTRADA
        # ----------------------------------------------------

        encoded = data.encode(
            "utf-8",
            errors="replace",
        )

        if len(encoded) > MAX_TERMINAL_INPUT_BYTES:

            raise ValueError(
                "Entrada enviada ao terminal excede "
                "o limite permitido."
            )


        # ----------------------------------------------------
        # CONPTY INPUT
        # ----------------------------------------------------
        #
        # PtyProcess trabalha com texto.
        #
        # Não adicionamos Enter automaticamente: o xterm já envia
        # \r quando o desenvolvedor pressiona Enter.
        # ----------------------------------------------------

        await asyncio.to_thread(
            process.write,
            data,
        )


    # ========================================================
    # READ
    # ========================================================

    async def read(
        self,
        size: int = 4096,
    ) -> bytes:
        """
        Lê a saída produzida pelo pseudoterminal.

        A interface externa continua retornando bytes para não
        exigir alteração imediata na camada WebSocket existente.
        """

        process = self.process

        if (
            process is None
            or self._closed
        ):

            return b""


        def _read_terminal():
            """
            Faz a leitura bloqueante fora do event loop.
            """

            try:

                return process.read(
                    size
                )

            except EOFError:

                return ""


        data = await asyncio.to_thread(
            _read_terminal
        )


        if not data:

            return b""


        # pywinpty devolve texto Unicode.
        # Convertemos para UTF-8 porque api/development.py já
        # espera bytes de terminal.
        return data.encode(
            "utf-8",
            errors="replace",
        )

    # ========================================================
    # RESIZE
    # ========================================================

    async def resize(
        self,
        *,
        rows: int,
        cols: int,
    ) -> None:
        """
        Sincroniza o tamanho do pseudoterminal Windows com o xterm
        exibido no navegador.

        pywinpty utiliza a ordem:
            rows, cols

        Isso mantém cursor, quebra de linha e prompt alinhados
        com a dimensão visual real do terminal do Studio.
        """

        if self._closed:
            return

        process = self.process

        if process is None:
            return


        # ----------------------------------------------------
        # VALIDAÇÃO DEFENSIVA
        # ----------------------------------------------------

        if (
            not isinstance(rows, int)
            or not isinstance(cols, int)
        ):
            raise ValueError(
                "Dimensões do terminal são inválidas."
            )

        # Impede dimensões zero/negativas ou valores absurdos
        # enviados pelo cliente.
        rows = max(
            1,
            min(rows, 500),
        )

        cols = max(
            1,
            min(cols, 1000),
        )


        # ----------------------------------------------------
        # CONPTY RESIZE
        # ----------------------------------------------------

        if not process.isalive():
            return

        await asyncio.to_thread(
            process.setwinsize,
            rows,
            cols,
        )
    # ========================================================
    # STATUS
    # ========================================================

    @property
    def running(self) -> bool:
        """
        Indica se o pseudoterminal continua ativo.
        """

        process = self.process

        if (
            self._closed
            or process is None
        ):

            return False


        try:

            return bool(
                process.isalive()
            )

        except Exception:

            return False


    # ========================================================
    # CLOSE
    # ========================================================

    async def close(self) -> None:
        """
        Encerra o pseudoterminal e libera seus recursos.

        A operação de encerramento também é executada fora do
        event loop porque pywinpty possui interface síncrona.
        """

        if self._closed:
            return

        self._closed = True

        process = self.process

        if process is None:
            return


        try:

            if process.isalive():

                await asyncio.to_thread(
                    process.terminate,
                    True,
                )


        except Exception:

            logger.exception(
                "Falha ao encerrar terminal do Development",
                extra={
                    "event":
                        "development_terminal_close_failed",

                    "user_id":
                        self.user_id,

                    "project_id":
                        self.project_id,

                    "pid":
                        getattr(
                            process,
                            "pid",
                            None,
                        ),

                    "status":
                        "error",
                },
            )


        finally:

            logger.info(
                "Terminal do Development encerrado",
                extra={
                    "event":
                        "development_terminal_closed",

                    "user_id":
                        self.user_id,

                    "project_id":
                        self.project_id,

                    "pid":
                        getattr(
                            process,
                            "pid",
                            None,
                        ),

                    "status":
                        "success",
                },
            )
# ============================================================
# PREPARAR TERMINAL
# ============================================================

def preparar_terminal_development(
    *,
    project_id: int,
    db: Session,
    usuario,
) -> DevelopmentTerminalSession:
    """
    Valida e prepara uma sessão de terminal para um projeto.

    Esta função NÃO inicia o processo ainda.

    Fluxo:

        projeto
            ↓
        Checkout
            ↓
        Workspace oficial
            ↓
        DevelopmentTerminalSession

    A abertura efetiva do cmd.exe ocorre posteriormente através
    de:

        await terminal.start()
    """

    # ========================================================
    # PROJETO
    # ========================================================

    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id == project_id,
            AutomationProject.is_active == 1,
        )
        .first()
    )

    if not projeto:

        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )


    # ========================================================
    # CHECKOUT
    # ========================================================
    #
    # O terminal permite modificar o Workspace livremente:
    #
    # - criar .venv;
    # - instalar pacotes;
    # - executar scripts;
    # - alterar requirements.txt;
    # - criar/remover arquivos via shell.
    #
    # Portanto ele só pode existir para quem possui o Checkout
    # exclusivo do projeto.
    # ========================================================

    exigir_checkout_workspace(
        project_id=project_id,
        user_id=usuario.id,
        db=db,
    )


    # ========================================================
    # WORKSPACE OFICIAL
    # ========================================================

    workspace_path = garantir_workspace(
        project_id
    )

    workspace_path = Path(
        workspace_path
    ).resolve()


    # ========================================================
    # SEGURANÇA BÁSICA DO WORKSPACE
    # ========================================================

    if not workspace_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Workspace físico do projeto "
                "não foi encontrado."
            ),
        )

    if not workspace_path.is_dir():

        raise HTTPException(
            status_code=500,
            detail=(
                "Workspace físico do projeto "
                "é inválido."
            ),
        )


    # ========================================================
    # CRIA SESSÃO
    # ========================================================

    return DevelopmentTerminalSession(
        project_id=project_id,
        user_id=usuario.id,
        workspace_path=workspace_path,
    )