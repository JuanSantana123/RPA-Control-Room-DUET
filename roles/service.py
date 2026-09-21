# ============================================================
# SERVICE - ROLES
# ============================================================
#
# Responsabilidade:
#
#     Concentrar as regras de negócio do domínio Roles e
#     controlar as transações das operações de escrita.
#
# A autorização RBAC da própria API permanece no router.
# ============================================================

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import User

# ============================================================
# SEGURANÇA RBAC
# ============================================================
#
# Estas validações impedem que alguém com Roles:edit conceda
# permissões que ele próprio não possui.
# ============================================================

from auth.rbac_safety import (
    obter_permission_ids_role,
    validar_admin_funcional_restante,
    validar_delegacao_permissao,
    validar_delegacao_permissoes,
)

from schemas.roles import (
    RoleCreate,
    RolePermissionCreate,
    RolePermissionsUpdate,
)

from roles.repository import (
    buscar_permissao_por_id,
    buscar_role_permission,
    buscar_role_por_id,
    buscar_role_por_nome,
    criar_role,
    criar_role_permission,
    excluir_role,
    listar_permissoes,
    listar_permissoes_por_ids,
    listar_permissoes_role,
    listar_roles,
    remover_permissoes_role,
    remover_usuarios_role,
)

from roles.serializers import (
    serializar_permissao,
    serializar_role,
)


# ============================================================
# CATÁLOGO DE PERMISSÕES
# ============================================================

def listar_permissoes_service(
    db: Session,
) -> list[dict]:
    """
    Retorna o catálogo de permissões do Control Room.
    """

    permissoes = listar_permissoes(
        db=db
    )

    return [
        serializar_permissao(permissao)
        for permissao in permissoes
    ]


# ============================================================
# LISTAR ROLES
# ============================================================

def listar_roles_service(
    db: Session,
) -> list[dict]:
    """
    Retorna todas as Roles cadastradas.
    """

    roles = listar_roles(
        db=db
    )

    return [
        serializar_role(role)
        for role in roles
    ]


# ============================================================
# CRIAR ROLE
# ============================================================

def criar_role_service(
    dados: RoleCreate,
    db: Session,
) -> dict:
    """
    Cria uma nova Role.

    Mantém as regras existentes de nome obrigatório e
    unicidade.
    """

    nome = dados.name.strip()

    if not nome:
        raise HTTPException(
            status_code=400,
            detail="O nome da Role é obrigatório.",
        )

    role_existente = buscar_role_por_nome(
        db=db,
        nome=nome,
    )

    if role_existente:
        raise HTTPException(
            status_code=409,
            detail="Já existe uma Role com esse nome.",
        )

    descricao = (
        dados.description.strip()
        if dados.description
        else None
    )

    nova_role = criar_role(
        db=db,
        nome=nome,
        descricao=descricao,
    )

    try:

        db.commit()
        db.refresh(nova_role)

    except Exception:

        db.rollback()
        raise

    return {
        "message": "Role criada com sucesso.",
        "role": serializar_role(
            nova_role
        ),
    }


# ============================================================
# LISTAR PERMISSÕES DA ROLE
# ============================================================

def listar_permissoes_role_service(
    role_id: int,
    db: Session,
) -> list[dict]:
    """
    Retorna as permissões associadas a uma Role.
    """

    role = buscar_role_por_id(
        db=db,
        role_id=role_id,
    )

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role não encontrada.",
        )

    permissoes = listar_permissoes_role(
        db=db,
        role_id=role_id,
    )

    return [
        serializar_permissao(permissao)
        for permissao in permissoes
    ]


# ============================================================
# ADICIONAR PERMISSÃO
# ============================================================

def adicionar_permissao_role_service(
    role_id: int,
    dados: RolePermissionCreate,
    db: Session,
    usuario_executor: User,
) -> dict:
    """
    Associa uma Permission existente a uma Role existente.
    """

    role = buscar_role_por_id(
        db=db,
        role_id=role_id,
    )

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role não encontrada.",
        )

    permissao = buscar_permissao_por_id(
        db=db,
        permission_id=dados.permission_id,
    )

    if not permissao:
        raise HTTPException(
            status_code=404,
            detail="Permissão não encontrada.",
        )

    associacao_existente = buscar_role_permission(
        db=db,
        role_id=role_id,
        permission_id=dados.permission_id,
    )

    if associacao_existente:
        raise HTTPException(
            status_code=409,
            detail="Essa permissão já está associada à Role.",
        )

    # ========================================================
    # SEGURANÇA DE DELEGAÇÃO
    # ========================================================
    #
    # Para adicionar uma Permission à Role, o executor precisa
    # possuir essa mesma Permission.
    # ========================================================

    validar_delegacao_permissao(
        usuario_executor=usuario_executor,
        permissao=permissao,
        db=db,
    )

    associacao = criar_role_permission(
        db=db,
        role_id=role_id,
        permission_id=dados.permission_id,
    )

    try:

        # Persiste a associação Role ↔ Permission.
        db.commit()

        db.refresh(
            associacao
        )

    except IntegrityError:

        # Deixa o service preparado para as constraints físicas
        # de integridade do relacionamento.
        #
        # Quando adicionarmos UNIQUE(role_id, permission_id),
        # uma tentativa concorrente de duplicação será convertida
        # em uma resposta controlada.
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Não foi possível associar a permissão à Role "
                "por conflito de integridade."
            ),
        )

    except Exception:

        db.rollback()

        raise

    return {
        "message": "Permissão adicionada à Role com sucesso.",
        "role": {
            "id": role.id,
            "name": role.name,
        },
        "permission": serializar_permissao(
            permissao
        ),
    }


# ============================================================
# SUBSTITUIR PERMISSÕES DA ROLE
# ============================================================

def atualizar_permissoes_role_service(
    role_id: int,
    dados: RolePermissionsUpdate,
    db: Session,
    usuario_executor: User,
) -> dict:
    """
    Substitui completamente as permissões atuais de uma Role.

    A lista vazia continua sendo aceita para preservar o
    contrato funcional atual.
    """

    role = buscar_role_por_id(
        db=db,
        role_id=role_id,
    )

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role não encontrada.",
        )

    # Mantém a semântica histórica de remover IDs duplicados.
    permission_ids = list(
        set(dados.permission_ids)
    )

    # Mantemos a coleção inicializada mesmo quando a requisição
    # deseja remover todas as permissões da Role.
    permissoes = []

    if permission_ids:

        permissoes = listar_permissoes_por_ids(
            db=db,
            permission_ids=permission_ids,
        )

        permissoes_encontradas = {
            permissao.id
            for permissao in permissoes
        }

        permissoes_inexistentes = [
            permission_id
            for permission_id in permission_ids
            if permission_id not in permissoes_encontradas
        ]

        if permissoes_inexistentes:
            raise HTTPException(
                status_code=400,
                detail={
                    "message":
                        "Uma ou mais permissões não existem.",
                    "permission_ids":
                        permissoes_inexistentes,
                },
            )



    # ========================================================
    # IDENTIFICAR SOMENTE NOVAS PERMISSÕES
    # ========================================================
    #
    # Remover uma Permission não exige que o executor possua
    # aquela Permission.
    #
    # Manter uma Permission já existente também não representa
    # uma nova delegação.
    #
    # Somente os IDs adicionados precisam passar pela proteção.
    # ========================================================

    permission_ids_atuais = obter_permission_ids_role(
        role_id=role_id,
        db=db,
    )

    permission_ids_novos = (
        set(permission_ids)
        - permission_ids_atuais
    )

    permissoes_novas = [
        permissao
        for permissao in permissoes
        if permissao.id in permission_ids_novos
    ]

    validar_delegacao_permissoes(
        usuario_executor=usuario_executor,
        permissoes=permissoes_novas,
        db=db,
    )

    # ========================================================
    # PROTEÇÃO CONTRA LOCKOUT ADMINISTRATIVO
    # ========================================================
    #
    # Antes de substituir as permissões da Role, simulamos
    # exatamente como ela ficará.
    #
    # Se esta mudança remover a última combinação capaz de
    # administrar Roles e usuários, a operação é bloqueada
    # antes de qualquer DELETE/INSERT.
    # ========================================================

    validar_admin_funcional_restante(
        db=db,
        role_id_removida=role_id,
        permission_ids_finais_role=set(
            permission_ids
        ),
    )

    try:

        remover_permissoes_role(
            db=db,
            role_id=role_id,
        )

        for permission_id in permission_ids:

            criar_role_permission(
                db=db,
                role_id=role_id,
                permission_id=permission_id,
            )

        db.commit()

    except Exception:

        db.rollback()
        raise

    return {
        "status": "success",
        "message": "Permissões da Role atualizadas com sucesso.",
        "role": {
            "id": role.id,
            "name": role.name,
        },
        "permission_ids": permission_ids,
    }


# ============================================================
# EXCLUIR ROLE
# ============================================================

def excluir_role_service(
    role_id: int,
    db: Session,
) -> dict:
    """
    Exclui uma Role e suas associações.

    RolePermission e UserRole são removidos na mesma
    transação da exclusão da Role.
    """

    role = buscar_role_por_id(
        db=db,
        role_id=role_id,
    )

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role não encontrada.",
        )

    # ========================================================
    # PROTEÇÃO CONTRA LOCKOUT ADMINISTRATIVO
    # ========================================================
    #
    # Simula a remoção completa desta Role antes de excluir
    # RolePermission, UserRole ou a própria Role.
    # ========================================================

    validar_admin_funcional_restante(
        db=db,
        role_id_removida=role_id,
    )

    try:

        remover_permissoes_role(
            db=db,
            role_id=role_id,
        )

        remover_usuarios_role(
            db=db,
            role_id=role_id,
        )

        excluir_role(
            db=db,
            role=role,
        )

        db.commit()

    except Exception:

        db.rollback()
        raise

    return {
        "status": "success",
        "message": "Role excluída com sucesso.",
    }