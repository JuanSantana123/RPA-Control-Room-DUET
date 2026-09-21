# ============================================================
# DUET CORE - ROBOTS - SERVIÇO DE EXCLUSÃO
# ============================================================
#
# Preserva integralmente as regras atuais de hard delete:
# Libraries atuais, Schedules, projetos ativos, proveniência de
# LibraryVersion, histórico de Execution, snapshots e limpeza
# física somente após commit.
#
# NÃO registra endpoint FastAPI.
# ============================================================

from pathlib import Path

from fastapi import HTTPException

from database import SessionLocal
from models import (
    Robot,
    RobotVersion,
    Execution,
    Schedule,
    AutomationProject,
    Library,
    LibraryVersion,
    RobotVersionLibraryDependency,
)
from releases.service import lock_publication
from robots.repository import BASE_DIRECTORY


def delete_robot_service(
    robot_id: int
):

    db = SessionLocal()

    try:

        # Serializa operações de publicação/exclusão relacionadas
        # ao catálogo de Produção.
        lock_publication(
            db
        )


        # ========================================================
        # 1. LOCALIZA O ROBOT
        # ========================================================

        robot = (
            db.query(Robot)
            .filter(
                Robot.id ==
                    robot_id
            )
            .first()
        )


        if not robot:

            raise HTTPException(
                status_code=404,
                detail={
                    "code":
                        "ROBOT_NOT_FOUND",

                    "message":
                        "Não foi possível excluir o Robot porque ele não existe.",

                    "robot_id":
                        robot_id,
                }
            )


        nome_robot = robot.name


        # ========================================================
        # ARTEFATOS FÍSICOS DE TODAS AS ROBOTVERSIONS
        # ========================================================
        #
        # O Robot possui apenas o ponteiro para a versão vigente,
        # porém o hard delete precisa conhecer também os artefatos
        # históricos:
        #
        #     v1
        #     v2
        #     v3
        #     ...
        #
        # IMPORTANTE:
        #
        # Aqui apenas COLETAMOS os caminhos.
        #
        # Nenhum arquivo é removido antes do db.commit().
        # ========================================================

        robot_versions = (
            db.query(RobotVersion)
            .filter(
                RobotVersion.robot_id ==
                    robot.id
            )
            .order_by(
                RobotVersion.version
            )
            .all()
        )


        artifact_paths = []


        for robot_version in robot_versions:

            caminho = Path(
                robot_version.artifact_path
            )


            # RobotVersion normalmente utiliza caminho relativo
            # à raiz do Control Room.
            if not caminho.is_absolute():

                caminho = (
                    BASE_DIRECTORY /
                    caminho
                )


            artifact_paths.append(
                (
                    robot_version.version,
                    caminho
                )
            )


        # ========================================================
        # FALLBACK PARA ROBOT LEGADO
        # ========================================================
        #
        # Se existir algum Robot antigo cujo file_path ainda não
        # esteja representado em RobotVersion, preservamos também
        # esse caminho na lista de limpeza.
        # ========================================================

        if robot.file_path:

            current_path = Path(
                robot.file_path
            )


            if not current_path.is_absolute():

                current_path = (
                    BASE_DIRECTORY /
                    current_path
                )


            caminhos_ja_registrados = {
                caminho.resolve()
                for _, caminho in artifact_paths
            }


            if (
                current_path.resolve()
                not in caminhos_ja_registrados
            ):

                artifact_paths.append(
                    (
                        robot.version,
                        current_path
                    )
                )


        # ========================================================
        # 2. BIBLIOTECAS DA VERSÃO ATUAL
        # ========================================================
        #
        # Esta é a principal regra que combinamos:
        #
        # Um Robot não pode ser excluído enquanto sua versão
        # ATUAL possuir Libraries vinculadas.
        #
        # A remoção deve acontecer através de:
        #
        #     Nova versão
        #         ↓
        #     Desenvolvimento
        #         ↓
        #     remover Libraries
        #         ↓
        #     publicar
        #
        # Depois disso o Robot poderá ser excluído.
        # ========================================================

        bibliotecas_atuais = (
            db.query(
                RobotVersionLibraryDependency,
                Library,
                LibraryVersion
            )
            .join(
                Library,
                Library.id ==
                    RobotVersionLibraryDependency.library_id
            )
            .join(
                LibraryVersion,
                LibraryVersion.id ==
                    RobotVersionLibraryDependency.library_version_id
            )
            .filter(
                RobotVersionLibraryDependency.robot_id ==
                    robot.id,

                RobotVersionLibraryDependency.robot_version ==
                    robot.version,

                LibraryVersion.library_id ==
                    RobotVersionLibraryDependency.library_id
            )
            .order_by(
                Library.name
            )
            .all()
        )


        if bibliotecas_atuais:

            descricao_bibliotecas = ", ".join(
                (
                    f"{library.name} "
                    f"{library_version.version}"
                )
                for (
                    dependency,
                    library,
                    library_version
                )
                in bibliotecas_atuais
            )


            raise HTTPException(
                status_code=409,
                detail={
                    "code":
                        "ROBOT_HAS_LIBRARIES",

                    "message": (
                        f'Não foi possível excluir o Robot '
                        f'"{nome_robot}". '
                        f'A versão atual v{robot.version} utiliza '
                        f'{len(bibliotecas_atuais)} biblioteca(s): '
                        f'{descricao_bibliotecas}. '
                        f'Crie uma nova versão do Robot, remova essas '
                        f'dependências no Desenvolvimento e publique '
                        f'antes de tentar excluir novamente.'
                    ),

                    "robot_id":
                        robot.id,

                    "robot_name":
                        robot.name,

                    "robot_version":
                        robot.version,

                    "total_libraries":
                        len(bibliotecas_atuais),

                    "libraries": [
                        {
                            "library_id":
                                library.id,

                            "library_name":
                                library.name,

                            "library_version_id":
                                library_version.id,

                            "library_version":
                                library_version.version,
                        }

                        for (
                            dependency,
                            library,
                            library_version
                        )
                        in bibliotecas_atuais
                    ],
                }
            )


        # ========================================================
        # 3. AGENDAMENTOS
        # ========================================================
        #
        # Não excluímos Schedule automaticamente.
        #
        # Isso poderia alterar silenciosamente uma configuração
        # operacional criada pelo usuário.
        # ========================================================

        schedules = (
            db.query(Schedule)
            .filter(
                Schedule.robot_id ==
                    robot.id
            )
            .all()
        )


        if schedules:

            raise HTTPException(
                status_code=409,
                detail={
                    "code":
                        "ROBOT_HAS_SCHEDULES",

                    "message": (
                        f'Não foi possível excluir o Robot '
                        f'"{nome_robot}". '
                        f'Existem {len(schedules)} agendamento(s) '
                        f'vinculado(s) a ele. '
                        f'Remova esses agendamentos antes de excluir o Robot.'
                    ),

                    "robot_id":
                        robot.id,

                    "total_schedules":
                        len(schedules),

                    "schedule_ids": [
                        schedule.id
                        for schedule in schedules
                    ],
                }
            )


        # ========================================================
        # ========================================================
        # 4. PROJETOS DE DESENVOLVIMENTO BASEADOS NO ROBOT
        # ========================================================
        #
        # Somente projetos AINDA EDITÁVEIS bloqueiam a exclusão.
        #
        # Projetos já publicados permanecem no banco apenas como
        # histórico e não devem impedir a remoção do Robot.
        # ========================================================

        projetos_ativos = (
            db.query(AutomationProject)
            .filter(
                AutomationProject.base_robot_id ==
                    robot.id,

                # Projeto já publicado não é mais um workspace
                # ativo de alteração do Robot.
                AutomationProject.status !=
                    "published"
            )
            .all()
        )


        if projetos_ativos:

            raise HTTPException(
                status_code=409,
                detail={
                    "code":
                        "ROBOT_HAS_DEVELOPMENT_PROJECTS",

                    "message": (
                        f'Não foi possível excluir o Robot '
                        f'"{nome_robot}". '
                        f'Existem {len(projetos_ativos)} projeto(s) '
                        f'ativo(s) de Desenvolvimento vinculados a ele. '
                        f'Finalize ou exclua esses projetos antes '
                        f'de tentar novamente.'
                    ),

                    "robot_id":
                        robot.id,

                    "total_projects":
                        len(projetos_ativos),

                    "projects": [
                        {
                            "project_id":
                                projeto.id,

                            "project_name":
                                projeto.name,

                            "status":
                                projeto.status,
                        }

                        for projeto in projetos_ativos
                    ],
                }
            )


        # --------------------------------------------------------
        # PROJETOS JÁ PUBLICADOS
        # --------------------------------------------------------
        #
        # O histórico do projeto permanece.
        #
        # Apenas removemos a FK base_robot_id para que um projeto
        # já encerrado não impeça o hard delete do Robot.
        #
        # base_version continua preservado no projeto.
        # --------------------------------------------------------

        projetos_publicados_desvinculados = (
            db.query(AutomationProject)
            .filter(
                AutomationProject.base_robot_id ==
                    robot.id,

                AutomationProject.status ==
                    "published"
            )
            .update(
                {
                    AutomationProject.base_robot_id:
                        None
                },
                synchronize_session=False
            )
        )
        # 5. PRESERVA LIBRARYVERSIONS ORIGINADAS DO ROBOT
        # ========================================================
        #
        # source_robot_id representa apenas a PROVENIÊNCIA da
        # LibraryVersion.
        #
        # Não apagamos a LibraryVersion e também não usamos essa
        # referência histórica para impedir a exclusão do Robot.
        #
        # Como source_robot_id é nullable, removemos somente a FK.
        # A LibraryVersion, versão, artefato e demais metadados
        # continuam preservados normalmente.
        # ========================================================

        library_versions_desvinculadas = (
            db.query(LibraryVersion)
            .filter(
                LibraryVersion.source_robot_id ==
                    robot.id
            )
            .update(
                {
                    LibraryVersion.source_robot_id:
                        None
                },
                synchronize_session=False
            )
        )
        # ========================================================
        # 6. PRESERVA HISTÓRICO DE EXECUÇÕES
        # ========================================================
        #
        # O código antigo APAGAVA as Execution.
        #
        # Agora preservamos:
        #
        #     robot_name
        #     robot_filename
        #     status
        #     datas
        #     Agent
        #     logs / histórico
        #
        # e apenas removemos robot_id.
        # ========================================================

        total_execucoes = (
            db.query(Execution)
            .filter(
                Execution.robot_id ==
                    robot.id
            )
            .count()
        )


        if total_execucoes:

            (
                db.query(Execution)
                .filter(
                    Execution.robot_id ==
                        robot.id
                )
                .update(
                    {
                        Execution.robot_id:
                            None
                    },
                    synchronize_session=False
                )
            )


        # ========================================================
        # 7. REMOVE SNAPSHOTS HISTÓRICOS ROBOT -> LIBRARY
        # ========================================================
        #
        # Neste ponto já garantimos que a versão ATUAL não possui
        # bibliotecas.
        #
        # Como esta operação é HARD DELETE do próprio Robot,
        # seus snapshots históricos precisam ser removidos para
        # não manter FKs apontando para um Robot inexistente.
        # ========================================================

        snapshots_removidos = (
            db.query(
                RobotVersionLibraryDependency
            )
            .filter(
                RobotVersionLibraryDependency.robot_id ==
                    robot.id
            )
            .delete(
                synchronize_session=False
            )
        )


        # ========================================================
        # 8. REMOVE O REGISTRO DO ROBOT
        # ========================================================

        db.delete(
            robot
        )


        # O banco é confirmado ANTES de remover o arquivo físico.
        #
        # Isso evita o problema antigo:
        #
        #     arquivo removido
        #         ↓
        #     FK impede DELETE
        #         ↓
        #     banco faz rollback
        #         ↓
        #     Robot fica cadastrado sem arquivo
        db.commit()


        # ========================================================
        
        # ========================================================
        # 9. REMOVE TODOS OS ARTEFATOS FÍSICOS
        # ========================================================
        #
        # IMPORTANTE:
        #
        # O banco já confirmou o hard delete através do
        # db.commit().
        #
        # Portanto, daqui para baixo fazemos somente a limpeza
        # dos arquivos físicos das RobotVersions que pertenciam
        # ao Robot.
        #
        # Uma falha na remoção de um arquivo NÃO desfaz o delete
        # do banco e também não deve transformar uma exclusão já
        # confirmada em erro HTTP 500.
        # ========================================================

        arquivos_removidos = 0
        arquivos_ausentes = 0
        falhas_arquivos = []


        # Evita processar o mesmo arquivo duas vezes.
        #
        # Isso também protege o fallback de Robot.file_path caso
        # ele aponte para o mesmo artefato da RobotVersion atual.
        caminhos_processados = set()


        for (
            artifact_version,
            caminho
        ) in artifact_paths:

            try:

                # resolve(strict=False) normaliza o caminho mesmo
                # quando o arquivo já não existe.
                caminho_resolvido = caminho.resolve(
                    strict=False
                )


                if caminho_resolvido in caminhos_processados:

                    continue


                caminhos_processados.add(
                    caminho_resolvido
                )


                if caminho.is_file():

                    caminho.unlink()

                    arquivos_removidos += 1


                else:

                    arquivos_ausentes += 1


            except Exception as file_error:

                # O DELETE no banco já foi confirmado.
                #
                # Por isso armazenamos a falha de filesystem para
                # informar ao Frontend, mas não levantamos uma nova
                # exceção que produziria um falso HTTP 500.
                falhas_arquivos.append({
                    "version":
                        artifact_version,

                    "path":
                        str(caminho),

                    "error":
                        str(file_error),
                })


        # ========================================================
        # AVISO DE LIMPEZA FÍSICA
        # ========================================================

        aviso_arquivo = None


        if falhas_arquivos:

            aviso_arquivo = (
                f'O Robot foi excluído do Control Room, '
                f'mas {len(falhas_arquivos)} artefato(s) físico(s) '
                f'não puderam ser removidos.'
            )


        elif arquivos_ausentes:

            aviso_arquivo = (
                f'O Robot foi excluído do Control Room. '
                f'{arquivos_ausentes} artefato(s) físico(s) '
                f'já não existiam no momento da limpeza.'
            )
        # ========================================================
        # 10. SUCESSO
        # ========================================================

        return {
            "status":
                "success",

            "message": (
                f'Robô "{nome_robot}" excluído com sucesso.'
            ),

            "robot_id":
                robot_id,

            "name":
                nome_robot,

            "executions_preserved":
                total_execucoes,

            # Projetos históricos publicados que deixaram de
            # apontar para o Robot removido.
            "published_projects_detached":
                projetos_publicados_desvinculados,

            # LibraryVersions preservadas cuja referência histórica
            # source_robot_id foi removida.
            "library_versions_detached":
                library_versions_desvinculadas,

            "library_snapshots_deleted":
                snapshots_removidos,

            # Mantido para compatibilidade com o Frontend atual.
            "file_deleted":
                arquivos_removidos > 0,

            # Quantidade de RobotVersions existentes no momento
            # em que o hard delete foi iniciado.
            "robot_versions_deleted":
                len(robot_versions),

            # Resultado da limpeza física dos artefatos.
            "files_deleted":
                arquivos_removidos,

            "files_missing":
                arquivos_ausentes,

            "file_cleanup_failures":
                falhas_arquivos,

            "warning":
                aviso_arquivo,
        }


    # ============================================================
    # ERROS DE REGRA DE NEGÓCIO
    # ============================================================
    #
    # Não transforme 404/409 em erro 500.
    # ============================================================

    except HTTPException:

        db.rollback()

        raise


    # ============================================================
    # ERRO INESPERADO
    # ============================================================

    except Exception as error:

        db.rollback()

        print()
        print("=" * 80)
        print("ERRO AO EXCLUIR ROBÔ")
        print(f"Robot ID : {robot_id}")
        print(f"Tipo     : {type(error).__name__}")
        print(f"Erro     : {error}")
        print("=" * 80)
        print()


        raise HTTPException(
            status_code=500,
            detail={
                "code":
                    "ROBOT_DELETE_FAILED",

                "message": (
                    "Não foi possível excluir o Robot devido "
                    "a uma falha interna."
                ),

                "robot_id":
                    robot_id,

                # Mantemos o erro técnico disponível para diagnóstico.
                "error":
                    str(error),
            }
        )


    finally:

        db.close()
