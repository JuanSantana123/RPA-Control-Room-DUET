from __future__ import annotations

import logging
import sys
import time
from pathlib import Path


# ============================================================
# PERMITE EXECUÇÃO DIRETA PELO PROTOCOLO WINDOWS
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


if str(
    PROJECT_ROOT
) not in sys.path:

    sys.path.insert(
        0,
        str(
            PROJECT_ROOT
        ),
    )


# ============================================================
# IMPORTS DO DEVELOPER BRIDGE
# ============================================================

from developer_bridge.api_client import (
    DuetApiClient,
    DuetApiError,
)

from developer_bridge.config import (
    workspace_root,
)

from developer_bridge.environment_manager import (
    ProjectEnvironment,
    prepare_project_environment,
)

from developer_bridge.ide_project_config import (
    build_ide_process_environment,
    prepare_ide_workspace,
)

from developer_bridge.ide_registry import (
    choose_and_launch_ide,
)

from developer_bridge.logging_setup import (
    configure_logging,
)

from developer_bridge.project_lock import (
    ProjectBridgeLock,
)

from developer_bridge.protocol import (
    parse_open_project_uri,
)

from developer_bridge.workspace_sync import (
    WorkspaceSync,
)


logger = logging.getLogger(
    "duet.developer_bridge"
)


# ============================================================
# CICLO DE VIDA DO BRIDGE
# ============================================================

# A sessão do backend possui TTL de horas, mas o Bridge renova
# preventivamente em intervalo curto. Isso evita que um desenvolvimento
# longo seja interrompido apenas por tempo.
SESSION_RENEW_INTERVAL_SECONDS = 15 * 60

# Pendências locais são tentadas novamente independentemente de novos
# eventos do filesystem. Assim uma queda temporária de rede se recupera
# sem exigir novo Ctrl+S.
PENDING_RETRY_INTERVAL_SECONDS = 10

# Loop leve do processo residente por projeto nesta fase.
BRIDGE_LOOP_SLEEP_SECONDS = 5


# ============================================================
# PREPARAR AMBIENTE LOCAL DE DESENVOLVIMENTO
# ============================================================

def _prepare_local_development(
    *,
    project_id: int,
    workspace: Path,
) -> ProjectEnvironment:
    """
    Prepara tudo que pertence SOMENTE à IDE externa.

    Fluxo:

    1. detecta Python instalado;
    2. cria/reutiliza venv do projeto;
    3. sincroniza requirements.txt;
    4. configura Python da IDE;
    5. configura _libraries;
    6. prepara Run/Debug do VS Code/Cursor.

    Nenhuma dessas etapas altera:
    - Agent;
    - Scheduler;
    - Studio;
    - runtime oficial de execução.
    """

    environment = (
        prepare_project_environment(
            project_id=project_id,
            workspace=workspace,
        )
    )


    prepare_ide_workspace(
        workspace=workspace,
        environment=environment,
    )


    logger.info(
        (
            "Ambiente local preparado | "
            "project_id=%s | "
            "python=%s | "
            "created=%s | "
            "requirements_installed=%s"
        ),
        project_id,
        environment.python_executable,
        environment.created,
        environment.requirements_installed,
    )


    return environment


# ============================================================
# ABRIR IDE COM AMBIENTE DUET
# ============================================================

def _open_ide(
    *,
    workspace: Path,
    project_name: str,
    environment: ProjectEnvironment,
) -> None:
    """
    Abre a IDE propagando o ambiente Python do projeto.
    """

    process_environment = (
        build_ide_process_environment(
            workspace=workspace,
            environment=environment,
        )
    )


    choose_and_launch_ide(
        workspace,
        project_name,
        process_environment=
            process_environment,
    )


# ============================================================
# ATUALIZAR WORKSPACE QUANDO JÁ EXISTE BRIDGE ATIVO
# ============================================================

def _refresh_existing_bridge_workspace(
    *,
    server: str,
    launch_code: str,
    workspace: Path,
    project_id: int,
) -> None:
    """
    Atualiza a cópia local antes de reabrir a IDE quando já existe
    um processo do Developer Bridge observando o projeto.

    Motivo:
        fechar o VS Code não encerra o processo pythonw.exe do Bridge.
        Nesse cenário o lock continua ocupado e, anteriormente, o fluxo
        apenas reabria a IDE sem executar um novo initial_pull().

    Estratégia:
        1. usa o NOVO launch_code gerado pelo Control Room;
        2. cria uma sessão curta e independente;
        3. materializa novamente o Workspace oficial;
        4. revoga somente essa sessão curta;
        5. mantém intacta a sessão/watchdog do Bridge já ativo.

    O WorkspaceSync.initial_pull() já preserva uma cópia de recuperação
    quando encontra conteúdo local divergente antes de sobrescrever.
    """

    refresh_api = DuetApiClient(
        server
    )

    try:

        # O launch_code continua de uso único. Mesmo com outro Bridge
        # ativo, esta nova abertura da IDE recebe sua própria sessão
        # temporária apenas para atualizar a cópia local.
        refresh_api.redeem(
            launch_code
        )

        refresh_sync = WorkspaceSync(
            api=refresh_api,
            workspace=workspace,
        )

        # Antes de qualquer pull remoto verificamos se o Workspace
        # possui alterações locais que ainda não chegaram ao DUET.
        #
        # Como esta abertura recebeu um launch_code novo, podemos usar
        # a sessão temporária para recuperar pendências inclusive quando
        # o token do Bridge principal ficou inválido após uma longa queda.
        if refresh_sync.pending_count() > 0:
            logger.warning(
                (
                    "Alterações locais pendentes encontradas ao "
                    "reabrir IDE | project_id=%s | pending=%s"
                ),
                project_id,
                refresh_sync.pending_count(),
            )

            refresh_sync.flush_pending()


        # O pull remoto só é permitido depois que toda alteração local
        # pendente foi confirmada no Control Room.
        if refresh_sync.pending_count() == 0:
            # Busca novamente a árvore oficial, incluindo _libraries.
            refresh_sync.initial_pull()

            logger.info(
                (
                    "Workspace local atualizado antes de reabrir IDE | "
                    "project_id=%s"
                ),
                project_id,
            )
        else:
            logger.warning(
                (
                    "Pull remoto adiado para preservar código local | "
                    "project_id=%s | pending=%s"
                ),
                project_id,
                refresh_sync.pending_count(),
            )

    finally:

        # A revogação atua somente sobre o token temporário criado acima.
        # O Bridge principal, que mantém o watcher local -> Control Room,
        # continua ativo normalmente.
        try:

            refresh_api.revoke()

        except Exception:

            logger.exception(
                (
                    "Não foi possível revogar a sessão temporária "
                    "de atualização do Workspace | project_id=%s"
                ),
                project_id,
            )


# ============================================================
# EXECUÇÃO PRINCIPAL DO PROTOCOLO DUET://
# ============================================================

def run(
    protocol_uri: str,
) -> None:

    request = (
        parse_open_project_uri(
            protocol_uri
        )
    )


    workspace = (
        workspace_root(
            request.project_id
        )
    )


    workspace.mkdir(
        parents=True,
        exist_ok=True,
    )


    project_lock = (
        ProjectBridgeLock(
            workspace
        )
    )


    # ========================================================
    # BRIDGE JÁ ATIVO
    # ========================================================
    #
    # Já existe um processo observando este projeto.
    #
    # Não iniciamos outro watcher.
    #
    # Entretanto, reaplicamos a preparação do ambiente porque:
    #
    # - requirements.txt pode ter mudado;
    # - o Python instalado pode ter mudado;
    # - configurações locais da IDE podem precisar ser atualizadas.
    # ========================================================

    if not project_lock.acquire():

        logger.info(
            "Bridge já ativo para projeto %s.",
            request.project_id,
        )


        # ----------------------------------------------------
        # ATUALIZA A CÓPIA LOCAL ANTES DE REABRIR A IDE
        # ----------------------------------------------------
        #
        # Fechar o VS Code não encerra o processo do Bridge.
        #
        # Portanto, quando o usuário adiciona uma Library no
        # Studio e depois clica novamente em "Abrir em IDE",
        # precisamos consultar novamente o Workspace oficial.
        #
        # Sem esta etapa, a IDE reabre a cópia local antiga.
        # ----------------------------------------------------

        _refresh_existing_bridge_workspace(
            server=
                request.server,

            launch_code=
                request.launch_code,

            workspace=
                workspace,

            project_id=
                request.project_id,
        )


        environment = (
            _prepare_local_development(
                project_id=
                    request.project_id,

                workspace=
                    workspace,
            )
        )


        _open_ide(
            workspace=
                workspace,

            project_name=
                request.project_name,

            environment=
                environment,
        )


        return


    # ========================================================
    # NOVA SESSÃO DO BRIDGE
    # ========================================================

    api = DuetApiClient(
        request.server
    )


    sync: (
        WorkspaceSync | None
    ) = None


    try:

        # ----------------------------------------------------
        # TROCA LAUNCH CODE POR SESSÃO DE BRIDGE
        # ----------------------------------------------------

        session = api.redeem(
            request.launch_code
        )


        # ----------------------------------------------------
        # WORKSPACE LOCAL
        # ----------------------------------------------------

        sync = WorkspaceSync(
            api=api,
            workspace=workspace,
        )


        # ----------------------------------------------------
        # RECUPERAR ALTERAÇÕES LOCAIS PENDENTES
        # ----------------------------------------------------
        #
        # Se uma sessão anterior perdeu conexão, o JSON em .duet
        # sobreviveu ao processo. Com a nova sessão autenticada,
        # tentamos enviar essas alterações ANTES de qualquer pull.
        #
        # Isso impede que código local ainda não sincronizado seja
        # sobrescrito por uma versão remota antiga.
        # ----------------------------------------------------

        if sync.pending_count() > 0:
            logger.warning(
                (
                    "Alterações locais pendentes encontradas | "
                    "project_id=%s | pending=%s"
                ),
                request.project_id,
                sync.pending_count(),
            )

            sync.flush_pending()


        # Primeiro materializamos o Workspace oficial somente quando
        # não restam alterações locais pendentes.
        #
        # Isso garante requirements.txt e _libraries atualizados sem
        # sacrificar código local que ainda precisa ser enviado.
        if sync.pending_count() == 0:
            sync.initial_pull()
        else:
            logger.warning(
                (
                    "Pull inicial adiado para preservar código local | "
                    "project_id=%s | pending=%s"
                ),
                request.project_id,
                sync.pending_count(),
            )


        # ----------------------------------------------------
        # AMBIENTE PYTHON DA IDE
        # ----------------------------------------------------

        environment = (
            _prepare_local_development(
                project_id=
                    request.project_id,

                workspace=
                    workspace,
            )
        )


        # ----------------------------------------------------
        # ABRIR IDE
        # ----------------------------------------------------

        _open_ide(
            workspace=
                workspace,

            project_name=
                request.project_name,

            environment=
                environment,
        )


        # ----------------------------------------------------
        # WATCHER LOCAL -> CONTROL ROOM
        # ----------------------------------------------------

        sync.start()


        # ----------------------------------------------------
        # MANTER BRIDGE ATIVO / RENOVAR / REENVIAR PENDÊNCIAS
        # ----------------------------------------------------
        #
        # Importante:
        #
        # - NÃO encerramos mais o watcher somente porque o relógio da
        #   sessão chegou ao expires_at inicial;
        # - enquanto o Control Room estiver acessível, a sessão é
        #   renovada preventivamente;
        # - se rede/servidor cair, o watcher continua protegendo o
        #   Workspace local e registrando alterações em .duet;
        # - pendências são tentadas novamente periodicamente.
        # ----------------------------------------------------

        next_renew = (
            time.monotonic()
            + SESSION_RENEW_INTERVAL_SECONDS
        )

        next_pending_retry = (
            time.monotonic()
            + PENDING_RETRY_INTERVAL_SECONDS
        )


        while True:
            time.sleep(
                BRIDGE_LOOP_SLEEP_SECONDS
            )

            now = time.monotonic()


            # ------------------------------------------------
            # RETRY DAS ALTERAÇÕES LOCAIS PENDENTES
            # ------------------------------------------------

            if now >= next_pending_retry:
                if sync.pending_count() > 0:
                    sync.flush_pending()

                next_pending_retry = (
                    now
                    + PENDING_RETRY_INTERVAL_SECONDS
                )


            # ------------------------------------------------
            # RENOVAÇÃO DA SESSÃO
            # ------------------------------------------------

            if now >= next_renew:
                try:
                    renewed = (
                        api.renew_session()
                    )

                    logger.info(
                        (
                            "Sessão do Developer Bridge renovada | "
                            "project_id=%s | expires_at=%s"
                        ),
                        request.project_id,
                        renewed.get(
                            "expires_at"
                        ),
                    )

                except DuetApiError as error:
                    # Não encerramos o watcher. O código continua sendo
                    # salvo localmente e as operações ficam pendentes.
                    logger.warning(
                        (
                            "Não foi possível renovar sessão do Bridge | "
                            "project_id=%s | status=%s | erro=%s | "
                            "alterações locais continuarão protegidas"
                        ),
                        request.project_id,
                        error.status_code,
                        error,
                    )

                except Exception:
                    logger.exception(
                        (
                            "Falha inesperada ao renovar sessão do Bridge | "
                            "project_id=%s | alterações locais continuarão "
                            "protegidas"
                        ),
                        request.project_id,
                    )

                finally:
                    next_renew = (
                        now
                        + SESSION_RENEW_INTERVAL_SECONDS
                    )


    finally:

        # ----------------------------------------------------
        # ENCERRAR WATCHER
        # ----------------------------------------------------

        if sync:

            sync.stop()


        # ----------------------------------------------------
        # REVOGAR SESSÃO DO BRIDGE
        # ----------------------------------------------------

        try:

            api.revoke()

        except Exception:

            logger.exception(
                (
                    "Não foi possível revogar "
                    "a sessão do Bridge."
                )
            )


        # ----------------------------------------------------
        # LIBERAR LOCK LOCAL
        # ----------------------------------------------------

        project_lock.release()


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> int:

    configure_logging()


    if len(
        sys.argv
    ) != 2:

        logger.error(
            "Uso inválido do Developer Bridge."
        )

        return 2


    try:

        run(
            sys.argv[1]
        )


        return 0


    except Exception:

        logger.exception(
            "Falha no DUET Developer Bridge."
        )


        return 1


if __name__ == "__main__":

    raise SystemExit(
        main()
    )