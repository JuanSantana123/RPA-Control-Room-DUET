# ============================================================
# DEVELOPMENT - FOLDERS SERVICE
# ============================================================
#
# Responsável pelas regras de negócio relacionadas às pastas
# da área de Desenvolvimento do DUET CORE.
#
# Este módulo concentra:
#
# - listagem das pastas ativas;
# - criação de pastas;
# - criação de subpastas;
# - validação da pasta pai;
# - prevenção de nomes duplicados no mesmo nível;
# - persistência e auditoria dessas operações.
#
# IMPORTANTE:
#
# Este módulo NÃO:
#
# - registra endpoints FastAPI;
# - utiliza Depends;
# - realiza autenticação;
# - aplica RBAC.
#
# Essas responsabilidades continuam pertencendo ao router:
#
#     api/development.py
#
# O service recebe explicitamente:
#
# - a sessão SQLAlchemy;
# - o usuário autenticado;
# - os dados já validados pelo schema.
# ============================================================


import logging

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import DevelopmentFolder

from development.serializers import (
    serializar_pasta,
)

from schemas.development import (
    DevelopmentFolderCreate,
)


# ============================================================
# LOGGER
# ============================================================
#
# Mantém o mesmo logger estruturado utilizado atualmente
# pelo Control Room.
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# LISTAR PASTAS
# ============================================================

def listar_pastas_service(
    db: Session,
) -> dict:
    """
    Retorna todas as pastas ativas da área de Desenvolvimento.

    Parâmetros:
        db:
            Sessão SQLAlchemy fornecida pela camada HTTP.

    Retorno:
        Mesmo contrato atualmente retornado por:

            GET /development/folders

    A estrutura pai/filho continua sendo representada pelo
    campo parent_id.

    O frontend é responsável por montar visualmente a árvore.
    """

    pastas = (
        db.query(DevelopmentFolder)
        .filter(
            DevelopmentFolder.is_active == 1
        )
        .order_by(
            DevelopmentFolder.name.asc(),
            DevelopmentFolder.id.asc(),
        )
        .all()
    )

    resultado = [
        serializar_pasta(
            pasta
        )
        for pasta in pastas
    ]

    return {
        "status": "success",
        "total": len(resultado),
        "folders": resultado,
    }


# ============================================================
# CRIAR PASTA
# ============================================================

def criar_pasta_service(
    request: DevelopmentFolderCreate,
    db: Session,
    usuario,
) -> dict:
    """
    Cria uma pasta ou subpasta na área de Desenvolvimento.

    Parâmetros:
        request:
            Dados validados pelo schema
            DevelopmentFolderCreate.

        db:
            Sessão SQLAlchemy da requisição.

        usuario:
            Usuário autenticado recebido pelo router.

            O service utiliza usuario.id para registrar
            propriedade e auditoria.

    Regras preservadas:

        1. O nome não pode ficar vazio.

        2. Quando parent_id for informado, a pasta pai
           precisa existir e estar ativa.

        3. Não pode existir outra pasta ativa com o mesmo
           nome no mesmo nível da árvore.

        4. O mesmo nome continua permitido quando as pastas
           estão em locais diferentes da árvore.
    """

    # Remove espaços extras nas extremidades.
    nome = request.name.strip()

    if not nome:

        raise HTTPException(
            status_code=400,
            detail=(
                "O nome da pasta não pode ficar vazio."
            ),
        )

    # ========================================================
    # VALIDA PASTA PAI
    # ========================================================

    if request.parent_id is not None:

        pasta_pai = (
            db.query(DevelopmentFolder)
            .filter(
                DevelopmentFolder.id ==
                    request.parent_id,

                DevelopmentFolder.is_active == 1,
            )
            .first()
        )

        if not pasta_pai:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Pasta pai não encontrada."
                ),
            )

    # ========================================================
    # EVITA NOME DUPLICADO NO MESMO NÍVEL
    # ========================================================
    #
    # Exemplo permitido:
    #
    #     Financeiro/
    #         Utils/
    #
    #     Comercial/
    #         Utils/
    #
    # Exemplo bloqueado:
    #
    #     Financeiro/
    #         Utils/
    #         Utils/
    #
    # A comparação continua case-insensitive.
    # ========================================================

    consulta_duplicada = (
        db.query(DevelopmentFolder)
        .filter(
            DevelopmentFolder.is_active == 1,

            func.lower(
                DevelopmentFolder.name
            ) == nome.lower(),
        )
    )

    # --------------------------------------------------------
    # PASTA NA RAIZ
    # --------------------------------------------------------

    if request.parent_id is None:

        consulta_duplicada = (
            consulta_duplicada
            .filter(
                DevelopmentFolder
                .parent_id
                .is_(None)
            )
        )

    # --------------------------------------------------------
    # SUBPASTA
    # --------------------------------------------------------

    else:

        consulta_duplicada = (
            consulta_duplicada
            .filter(
                DevelopmentFolder.parent_id ==
                    request.parent_id
            )
        )

    pasta_existente = (
        consulta_duplicada.first()
    )

    if pasta_existente:

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe uma pasta ativa com esse nome "
                "neste local."
            ),
        )

    # ========================================================
    # CRIA REGISTRO
    # ========================================================

    pasta = DevelopmentFolder(
        name=nome,
        parent_id=request.parent_id,
        created_by=usuario.id,
        is_active=1,
    )

    try:

        db.add(
            pasta
        )

        db.commit()

        db.refresh(
            pasta
        )

        # ====================================================
        # AUDITORIA
        # ====================================================

        logger.info(
            "Pasta de desenvolvimento criada",
            extra={
                "event":
                    "development_folder_created",

                "user_id":
                    usuario.id,

                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Pasta criada com sucesso."
            ),
            "folder":
                serializar_pasta(
                    pasta
                ),
        }

    # HTTPException é propagada sem transformar o erro
    # funcional em erro HTTP 500.
    except HTTPException:
        raise

    except Exception as error:

        # Qualquer falha de persistência precisa devolver
        # a transação para um estado consistente.
        db.rollback()

        logger.exception(
            "Falha ao criar pasta de desenvolvimento",
            extra={
                "event":
                    "development_folder_create_failed",

                "user_id":
                    usuario.id,

                "status":
                    "error",

                "error_type":
                    type(error).__name__,

                "error_message":
                    str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível criar a pasta."
            ),
        )