# ============================================================
# LIBRARIES - IMPORT SERVICE
# ============================================================
#
# Regra de negócio responsável por importar uma Library Python
# já existente diretamente para o catálogo global do DUET.
#
# RESPONSABILIDADES:
#
# - validar os metadados da nova Library;
# - validar o ZIP recebido;
# - criar a identidade da Library;
# - criar a primeira LibraryVersion;
# - persistir o snapshot imutável em storage/libraries;
# - promover a primeira versão para Produção;
# - garantir rollback lógico/físico se qualquer etapa falhar.
#
# IMPORTANTE:
#
# Este módulo NÃO registra endpoints FastAPI.
# Depends(), RBAC, Form() e File() permanecem em api/libraries.py.
#
# A operação inteira é atômica do ponto de vista do catálogo:
# a Library não deve ficar criada pela metade caso a publicação
# da primeira versão falhe.
# ============================================================


import logging
import os
import shutil
import tempfile

from pathlib import Path

from fastapi import (
    HTTPException,
    UploadFile,
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from models import (
    Library,
    LibraryVersion,
    ProjectLibraryDependency,
    ProjectLibraryDraft,
)
from libraries.identity_service import (
    buscar_library_por_import_name,
    validar_identidade_library_unica,
)
from libraries.repository import (
    BASE_DIRECTORY,
    LIBRARIES_REPOSITORY,
    MAX_LIBRARY_ZIP_SIZE,
    TEMP_REPOSITORY,
    UPLOAD_CHUNK_SIZE,
)

from libraries.serializers import (
    serializar_library,
    serializar_library_version,
)

from libraries.validators import (
    calcular_sha256,
    validar_destino_pasta,
    validar_import_name,
    validar_versao,
    validar_zip_biblioteca,
)

from development.workspace_core import (
    draft_has_changes,
)
# Mesmo logger estruturado utilizado pelo restante do Control Room.
logger = logging.getLogger(
    "control_room"
)


# ============================================================
# IMPORTAR LIBRARY STANDALONE
# ============================================================

async def importar_biblioteca_standalone_service(
    name: str,
    import_name: str,
    version: str,
    description: str | None,
    folder_id: int | None,
    file: UploadFile,
    db: Session,
    usuario,
) -> dict:
    """
    Importa uma biblioteca Python existente diretamente para o
    catálogo global do DUET, sem depender de AutomationProject.

    Fluxo:

    1. valida metadados;
    2. valida namespace Python e Semantic Version;
    3. valida a pasta de destino do catálogo;
    4. recebe o ZIP em arquivo temporário com limite de tamanho;
    5. valida a estrutura e a segurança do ZIP;
    6. cria Library e LibraryVersion sem commit intermediário;
    7. move o snapshot para storage/libraries;
    8. promove a primeira versão para Produção;
    9. confirma tudo em um único commit.

    Estrutura esperada para import_name="logging_core":

        logging_core/
            __init__.py
            logging.py

    Se qualquer etapa falhar depois da movimentação do artefato,
    o banco sofre rollback e o diretório físico criado é removido.
    """

    # ========================================================
    # 1. METADADOS
    # ========================================================

    nome = name.strip()

    if not nome:

        raise HTTPException(
            status_code=400,
            detail=(
                "O nome da biblioteca não pode ficar vazio."
            ),
        )

    if len(nome) > 255:

        raise HTTPException(
            status_code=400,
            detail=(
                "O nome da biblioteca não pode ultrapassar 255 caracteres."
            ),
        )

    # O validator garante que o namespace seja um identificador
    # Python válido e que não utilize uma palavra reservada.
    namespace = validar_import_name(
        import_name
    )

    if len(namespace) > 255:

        raise HTTPException(
            status_code=400,
            detail=(
                "O import_name não pode ultrapassar 255 caracteres."
            ),
        )

    # Mantemos a mesma validação SemVer utilizada na publicação
    # standalone de novas versões das Libraries existentes.
    versao = validar_versao(
        version
    )

    descricao = (
        description.strip()
        if description
        else None
    )

    if (
        descricao is not None
        and len(descricao) > 5000
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "A descrição não pode ultrapassar 5000 caracteres."
            ),
        )

    # None representa a raiz do catálogo. Quando um ID é recebido,
    # o validator confirma que a pasta existe e pode ser utilizada.
    validar_destino_pasta(
        db,
        folder_id,
    )
    # ========================================================
    # 2. RESOLVER IDENTIDADE GLOBAL DA LIBRARY
    # ========================================================
    #
    # Existem quatro cenários:
    #
    # A) import_name não existe:
    #       -> cria nova identidade.
    #
    # B) import_name existe, mas nunca houve publicação:
    #       -> reutiliza a MESMA identidade.
    #
    #       Esse caso cobre:
    #       - Library criada no Development;
    #       - Library criada manualmente no catálogo e ainda
    #         sem LibraryVersion.
    #
    # C) import_name pertence a Library publicada e ATIVA:
    #       -> não é primeira importação;
    #       -> deve utilizar publicação de nova versão.
    #
    # D) import_name pertence a Library publicada e ARQUIVADA:
    #       -> não cria outra;
    #       -> usuário precisa reativar a identidade existente.
    #
    # Em todos os casos o NAME também precisa permanecer único.
    # ========================================================

    import_existente = (
        buscar_library_por_import_name(
            db=db,
            import_name=namespace,
        )
    )

    reutilizando_identidade = False

    if import_existente is not None:

        total_versoes_existentes = (
            db.query(LibraryVersion)
            .filter(
                LibraryVersion.library_id
                == import_existente.id
            )
            .count()
        )

        possui_historico_publicado = (
            import_existente.production_version_id
            is not None
            or total_versoes_existentes > 0
        )

        # ----------------------------------------------------
        # JÁ FOI PUBLICADA
        # ----------------------------------------------------

        if possui_historico_publicado:

            # A identidade continua reservada mesmo arquivada.
            if not import_existente.is_active:

                raise HTTPException(
                    status_code=409,
                    detail={
                        "code":
                            "LIBRARY_ARCHIVED_REACTIVATE",

                        "message": (
                            f'A biblioteca "{import_existente.name}" '
                            f'está desativada. Reative a biblioteca '
                            f'existente para continuar utilizando '
                            f'o namespace "{namespace}".'
                        ),

                        "library_id":
                            import_existente.id,

                        "library_name":
                            import_existente.name,

                        "import_name":
                            import_existente.import_name,
                    },
                )

            # Publicada e ativa: primeira importação não é mais
            # o fluxo correto.
            raise HTTPException(
                status_code=409,
                detail={
                    "code":
                        "LIBRARY_ALREADY_PUBLISHED",

                    "message": (
                        f'A biblioteca "{import_existente.name}" '
                        "já possui publicação no catálogo. "
                        "Utilize o fluxo de publicação de nova versão."
                    ),

                    "library_id":
                        import_existente.id,

                    "library_name":
                        import_existente.name,

                    "import_name":
                        import_existente.import_name,
                },
            )

        # ----------------------------------------------------
        # IDENTIDADE AINDA NÃO PUBLICADA
        # ----------------------------------------------------
        #
        # Podemos reutilizar a identidade, mas NÃO podemos permitir
        # que o nome informado colida com outra Library.
        # ----------------------------------------------------

        validar_identidade_library_unica(
            db=db,
            nome=nome,
            import_name=namespace,
            ignorar_library_id=import_existente.id,
        )

        library = import_existente

        reutilizando_identidade = True

    else:

        # ----------------------------------------------------
        # IDENTIDADE COMPLETAMENTE NOVA
        # ----------------------------------------------------

        validar_identidade_library_unica(
            db=db,
            nome=nome,
            import_name=namespace,
        )

        library = None

    # ========================================================
    # 3. ARQUIVO RECEBIDO
    # ========================================================

    filename = (
        file.filename or ""
    ).strip()

    if not filename.lower().endswith(
        ".zip"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "A biblioteca precisa ser enviada em um arquivo ZIP."
            ),
        )

    # O upload é escrito primeiro no repositório temporário oficial
    # das Libraries. Nenhum registro é criado antes da validação
    # completa do ZIP.
    temp_fd, temp_name = tempfile.mkstemp(
        prefix="library_import_",
        suffix=".zip",
        dir=TEMP_REPOSITORY,
    )

    os.close(
        temp_fd
    )

    temp_path = Path(
        temp_name
    )

    total_bytes = 0

    # Só recebem valor depois que o banco fornece o ID da Library.
    # São mantidos fora do try para permitir limpeza segura em todos
    # os caminhos de erro.
    destino_diretorio: Path | None = None
    artefato_movido = False

    try:

        # ====================================================
        # 4. SALVAR UPLOAD TEMPORARIAMENTE
        # ====================================================

        with temp_path.open(
            "wb"
        ) as temp_file:

            while True:

                chunk = await file.read(
                    UPLOAD_CHUNK_SIZE
                )

                if not chunk:
                    break

                total_bytes += len(
                    chunk
                )

                if (
                    total_bytes
                    > MAX_LIBRARY_ZIP_SIZE
                ):

                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "O ZIP da biblioteca ultrapassa o limite "
                            "de 50 MB."
                        ),
                    )

                temp_file.write(
                    chunk
                )

        if total_bytes == 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "O arquivo enviado está vazio."
                ),
            )

        # ====================================================
        # 5. VALIDAR SNAPSHOT ANTES DE PERSISTIR
        # ====================================================

        # A validação existente no domínio de Libraries protege
        # contra caminhos inválidos, conteúdo fora do namespace,
        # ausência de __init__.py e ZIPs estruturalmente inválidos.
        validar_zip_biblioteca(
            temp_path,
            namespace,
        )

        file_hash = calcular_sha256(
            temp_path
        )

        # ====================================================
        # 6. CRIAR OU REUTILIZAR IDENTIDADE DA LIBRARY
        # ====================================================
        #
        # Se o namespace nasceu no Development, a identidade já
        # existe no banco e NÃO deve ser duplicada.
        #
        # Nesse caso apenas promovemos essa mesma identidade para
        # sua primeira publicação.
        # ====================================================

        if library is None:

            library = Library(
                name=nome,
                import_name=namespace,
                description=descricao,
                folder_id=folder_id,
                created_by=usuario.id,
                is_active=1,
            )

            db.add(
                library
            )

        else:

            # A primeira publicação standalone também pode definir
            # os metadados finais com que a Library aparecerá no
            # catálogo global.
            library.name = nome
            library.description = descricao
            library.folder_id = folder_id

            # Uma Library criada dentro do Development normalmente
            # permanece inativa até sua primeira publicação.
            library.is_active = 1

        # Necessário tanto para obter o ID de uma nova Library
        # quanto para persistir as alterações da identidade
        # reutilizada dentro da mesma transação.
        db.flush()

        # ====================================================
        # 7. REPOSITÓRIO FÍSICO IMUTÁVEL
        # ====================================================
        #
        # storage/
        # └── libraries/
        #     └── <library_id>/
        #         └── <version>/
        #             └── library.zip
        # ====================================================

        destino_diretorio = (
            LIBRARIES_REPOSITORY
            / str(library.id)
            / versao
        )

        destino_arquivo = (
            destino_diretorio
            / "library.zip"
        )

        # Snapshot publicado nunca deve ser sobrescrito.
        if destino_diretorio.exists():

            raise HTTPException(
                status_code=409,
                detail=(
                    "Já existe um artefato físico para esta versão."
                ),
            )

        destino_diretorio.mkdir(
            parents=True,
            exist_ok=False,
        )

        os.replace(
            temp_path,
            destino_arquivo,
        )

        artefato_movido = True

        relative_artifact_path = (
            destino_arquivo
            .relative_to(
                BASE_DIRECTORY
            )
            .as_posix()
        )

        # ====================================================
        # 8. PRIMEIRA LIBRARY VERSION
        # ====================================================

        library_version = LibraryVersion(
            library_id=library.id,
            version=versao,
            source_type="standalone",
            source_robot_id=None,
            source_robot_version=None,
            source_path=None,
            artifact_path=relative_artifact_path,
            file_hash=file_hash,
            published_by=usuario.id,
            is_active=1,
        )

        db.add(
            library_version
        )

        # Obtém o ID da versão ainda dentro da mesma transação.
        db.flush()

        # Uma Library importada já nasce com sua primeira versão
        # como versão vigente em Produção.
        library.production_version_id = (
            library_version.id
        )


        # ====================================================
        # 9. SINCRONIZAR DRAFTS DO DEVELOPMENT
        # ====================================================
        #
        # Uma identidade criada/importada no Development pode possuir
        # ProjectLibraryDraft com:
        #
        #     base_library_version_id = NULL
        #
        # Agora que a primeira LibraryVersion existe, esses projetos
        # precisam passar a conhecer essa versão como base publicada.
        #
        # Também criamos/atualizamos ProjectLibraryDependency para que
        # o projeto passe a apontar explicitamente para a versão exata.
        # ====================================================

        drafts = (
            db.query(ProjectLibraryDraft)
            .filter(
                ProjectLibraryDraft.library_id
                == library.id
            )
            .all()
        )

        projetos_sincronizados = 0

        for draft in drafts:

            dependency = (
                db.query(ProjectLibraryDependency)
                .filter(
                    ProjectLibraryDependency.project_id
                    == draft.project_id,

                    ProjectLibraryDependency.library_id
                    == library.id,
                )
                .first()
            )

            # ------------------------------------------------
            # Cria o vínculo publicado caso o projeto ainda
            # possua somente a Working Copy.
            # ------------------------------------------------

            if dependency is None:

                dependency = ProjectLibraryDependency(
                    project_id=draft.project_id,
                    library_id=library.id,
                    library_version_id=library_version.id,
                    added_by=usuario.id,
                )

                db.add(
                    dependency
                )

            else:

                dependency.library_version_id = (
                    library_version.id
                )

                dependency.added_by = (
                    usuario.id
                )

            # ------------------------------------------------
            # O draft agora possui uma versão-base real.
            # ------------------------------------------------

            draft.base_library_version_id = (
                library_version.id
            )

            # ------------------------------------------------
            # Não assumimos que o ZIP enviado é necessariamente
            # idêntico à Working Copy existente.
            #
            # Se forem iguais:
            #     is_modified = 0
            #
            # Se o projeto possuir diferenças:
            #     is_modified = 1
            # ------------------------------------------------

            draft.is_modified = (
                1
                if draft_has_changes(
                    project_id=draft.project_id,
                    library=library,
                    version=library_version,
                )
                else 0
            )

            draft.updated_by = (
                usuario.id
            )

            projetos_sincronizados += 1

        db.flush()
        # ====================================================
        # ====================================================
        # 10. PREPARAR RESPOSTA ANTES DO COMMIT
        # ====================================================
        #
        # Não executamos db.refresh() depois do commit.
        #
        # Assim, depois que a transação for confirmada, não existe
        # nenhuma operação de banco necessária que possa lançar uma
        # exceção e provocar uma tentativa incorreta de compensação
        # física do artefato já publicado.
        # ====================================================

        resposta = {
            "status": "success",
            "message": (
                "Biblioteca importada com sucesso."
            ),
            "library": serializar_library(
                library
            ),
            "version": serializar_library_version(
                library_version,
                library.production_version_id,
            ),
            "reused_identity": (
                reutilizando_identidade
            ),
            "synchronized_projects": (
                projetos_sincronizados
            ),
        }

        library_id = (
            library.id
        )

        library_version_id = (
            library_version.id
        )

        # ====================================================
        # 11. COMMIT ATÔMICO
        # ====================================================

        db.commit()

        logger.info(
            "Biblioteca standalone importada",
            extra={
                "event": "library_imported",
                "user_id": usuario.id,
                "library_id": library_id,
                "library_version_id":
                    library_version_id,
                "reused_identity":
                    reutilizando_identidade,
                "synchronized_projects":
                    projetos_sincronizados,
                "status": "success",
            },
        )

        return resposta

    # ========================================================
    # CONFLITO DE INTEGRIDADE
    # ========================================================

    except IntegrityError as error:

        db.rollback()

        if (
            artefato_movido
            and destino_diretorio is not None
            and destino_diretorio.exists()
        ):

            shutil.rmtree(
                destino_diretorio,
                ignore_errors=True,
            )

        # ====================================================
        # LOG DO ERRO REAL DE INTEGRIDADE
        # ====================================================
        #
        # Não podemos assumir que todo IntegrityError significa
        # duplicidade de import_name.
        #
        # Aqui registramos no backend a constraint/motivo real
        # retornado pelo PostgreSQL.
        # ====================================================

        logger.exception(
            "Falha de integridade ao importar biblioteca standalone",
            extra={
                "event": "library_import_integrity_error",
                "user_id": usuario.id,
                "import_name": namespace,
                "error_type": type(error).__name__,
                "database_error": str(
                    getattr(
                        error,
                        "orig",
                        error,
                    )
                ),
                "status": "error",
            },
        )

        raise HTTPException(
            status_code=409,
            detail=(
                "Não foi possível concluir a publicação da biblioteca "
                "por um conflito de integridade."
            ),
        ) from error

    # ========================================================
    # ERRO DE NEGÓCIO / VALIDAÇÃO
    # ========================================================

    except HTTPException:

        db.rollback()

        if (
            artefato_movido
            and destino_diretorio is not None
            and destino_diretorio.exists()
        ):

            shutil.rmtree(
                destino_diretorio,
                ignore_errors=True,
            )

        raise

    # ========================================================
    # ERRO INESPERADO
    # ========================================================

    except Exception as error:

        db.rollback()

        if (
            artefato_movido
            and destino_diretorio is not None
            and destino_diretorio.exists()
        ):

            shutil.rmtree(
                destino_diretorio,
                ignore_errors=True,
            )

        logger.exception(
            "Falha ao importar biblioteca standalone",
            extra={
                "event": "library_import_failed",
                "user_id": usuario.id,
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível importar a biblioteca."
            ),
        ) from error

    # ========================================================
    # LIMPEZA DO UPLOAD TEMPORÁRIO
    # ========================================================

    finally:

        try:
            await file.close()
        except Exception:
            # Fechamento do UploadFile é best-effort e não deve
            # esconder o resultado principal da operação.
            pass

        if temp_path.exists():

            try:
                temp_path.unlink()
            except Exception:
                # O arquivo temporário já não participa do estado
                # transacional; falha de limpeza não deve mascarar
                # a exceção original.
                pass
