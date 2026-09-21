# ============================================================
# DEVELOPMENT - SERIALIZERS
# ============================================================
#
# Responsável por converter os models SQLAlchemy utilizados
# pela área de Desenvolvimento em estruturas seguras para
# retorno pela API.
#
# Este módulo centraliza a serialização de:
#
# - DevelopmentFolder;
# - AutomationProject;
# - DevelopmentStage;
# - ProjectCheckout;
# - ProjectComment.
#
# IMPORTANTE:
#
# Este módulo NÃO:
#
# - registra endpoints FastAPI;
# - abre sessões de banco;
# - executa commit/rollback;
# - realiza autenticação;
# - aplica RBAC;
# - altera registros;
# - acessa o filesystem.
#
# Os objetos recebidos já devem ter sido obtidos pela camada
# de serviço responsável pela operação.
# ============================================================


from models import (
    AutomationProject,
    DevelopmentFolder,
    DevelopmentStage,
    ProjectCheckout,
    ProjectComment,
)


# ============================================================
# SERIALIZAÇÃO - PASTA
# ============================================================

def serializar_pasta(
    pasta: DevelopmentFolder,
) -> dict:
    """
    Converte um DevelopmentFolder em um dicionário seguro
    para retorno pela API.

    Parâmetros:
        pasta:
            Instância SQLAlchemy de DevelopmentFolder.

    Retorno:
        Dicionário contendo os campos atualmente expostos
        pela API de Development.
    """

    return {
        "id": pasta.id,
        "name": pasta.name,
        "parent_id": pasta.parent_id,
        "created_by": pasta.created_by,

        "created_at": (
            pasta.created_at.isoformat()
            if pasta.created_at
            else None
        ),

        "updated_at": (
            pasta.updated_at.isoformat()
            if pasta.updated_at
            else None
        ),

        "is_active": bool(
            pasta.is_active
        ),
    }


# ============================================================
# SERIALIZAÇÃO - PROJETO
# ============================================================
def serializar_projeto(
    projeto: AutomationProject,
) -> dict:
    """
    Converte um AutomationProject em um dicionário seguro
    para retorno pela API.

    Parâmetros:
        projeto:
            Instância SQLAlchemy de AutomationProject.

        base_robot_name:
            Nome amigável do Robot que originou o projeto.

            Quando None, o projeto foi criado do zero ou o
            Robot de origem não está mais disponível.

    Mantém os campos utilizados pelo frontend do DUET CORE
    e acrescenta a identificação amigável do Robot de origem.
    """

    return {
        "id": projeto.id,
        "name": projeto.name,
        "description": projeto.description,
        "folder_id": projeto.folder_id,
        "status": projeto.status,
        "current_stage_id": projeto.current_stage_id,

        # ====================================================
        # ORIGEM DO PROJETO
        # ====================================================
        #
        # base_robot_id:
        #     Identificador técnico do Robot de origem.
        #
        # base_robot_name:
        #     Nome amigável apresentado no frontend.
        #
        # base_version:
        #     Versão do Robot utilizada como base no momento
        #     da criação do projeto.
        # ====================================================

        "base_robot_id":
            projeto.base_robot_id,

        # Snapshot histórico do nome do Robot de origem.
        "base_robot_name":
            projeto.base_robot_name,

        "base_version":
            projeto.base_version,

        "created_by":
            projeto.created_by,

        # ====================================================
        # DETALHES INDIVIDUAIS DO CARD
        # ====================================================

        "functional_responsible_id":
            projeto.functional_responsible_id,

        "technical_responsible_id":
            projeto.technical_responsible_id,

        "start_date": (
            projeto.start_date.isoformat()
            if projeto.start_date
            else None
        ),

        "due_date": (
            projeto.due_date.isoformat()
            if projeto.due_date
            else None
        ),

        # Numeric do PostgreSQL normalmente é representado
        # pelo Python como Decimal.
        #
        # A conversão para float ocorre somente na resposta
        # destinada ao frontend.
        "effort_hours": (
            float(projeto.effort_hours)
            if projeto.effort_hours is not None
            else None
        ),

        "created_at": (
            projeto.created_at.isoformat()
            if projeto.created_at
            else None
        ),

        "updated_at": (
            projeto.updated_at.isoformat()
            if projeto.updated_at
            else None
        ),

        # ====================================================
        # LIXEIRA
        # ====================================================

        "deleted_at": (
            projeto.deleted_at.isoformat()
            if projeto.deleted_at
            else None
        ),

        "deleted_by":
            projeto.deleted_by,

        "is_active": bool(
            projeto.is_active
        ),
    }
# ============================================================
# SERIALIZAÇÃO - ESTÁGIO DO WORKFLOW
# ============================================================

def serializar_estagio(
    estagio: DevelopmentStage,
) -> dict:
    """
    Converte um DevelopmentStage em um dicionário seguro
    para retorno pela API.
    """

    return {
        "id": estagio.id,
        "code": estagio.code,
        "name": estagio.name,
        "position": estagio.position,
        "is_active": bool(
            estagio.is_active
        ),
    }


# ============================================================
# SERIALIZAÇÃO - CHECKOUT
# ============================================================

def serializar_checkout(
    checkout: ProjectCheckout,
    user_name: str | None = None,
) -> dict:
    """
    Converte o Checkout ativo de um projeto em um dicionário
    seguro para retorno pela API.

    Parâmetros:
        checkout:
            Registro ProjectCheckout.

        user_name:
            Nome amigável do usuário proprietário do Checkout.

            O relacionamento real continua sendo identificado
            pelo campo user_id.
    """

    return {
        "id": checkout.id,
        "project_id": checkout.project_id,
        "user_id": checkout.user_id,

        "user_name": user_name,

        "checked_out_at": (
            checkout.checked_out_at.isoformat()
            if checkout.checked_out_at
            else None
        ),
    }


# ============================================================
# SERIALIZAÇÃO - COMENTÁRIO
# ============================================================

def serializar_comentario(
    comentario: ProjectComment,
    user_name: str | None = None,
) -> dict:
    """
    Converte um comentário do Kanban em um dicionário seguro
    para retorno pelo frontend.

    Parâmetros:
        comentario:
            Registro ProjectComment.

        user_name:
            Nome amigável do autor.

            O vínculo persistido continua sendo realizado
            através de user_id.
    """

    return {
        "id": comentario.id,
        "project_id": comentario.project_id,

        "user_id": comentario.user_id,
        "user_name": user_name,

        "content": comentario.content,

        "created_at": (
            comentario.created_at.isoformat()
            if comentario.created_at
            else None
        ),

        "updated_at": (
            comentario.updated_at.isoformat()
            if comentario.updated_at
            else None
        ),
    }