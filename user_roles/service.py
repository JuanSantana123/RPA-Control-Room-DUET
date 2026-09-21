# ============================================================
# SERVICE - USER ROLES
# ============================================================
#
# Responsabilidade:
#
#     Implementar as regras de negócio relacionadas à
#     associação entre usuários e Roles.
#
# Este módulo:
#
#     - valida existência do usuário;
#     - valida existência da Role;
#     - impede associação duplicada;
#     - lista Roles;
#     - cria associações;
#     - remove associações;
#     - controla commit das operações de escrita.
#
# A camada HTTP permanece em:
#
#     api/user_roles.py
#
# ============================================================

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# ============================================================
# SEGURANÇA RBAC
# ============================================================
#
# validar_delegacao_role impede que um usuário conceda
# uma Role que contenha permissões que ele próprio não possui.
# ============================================================

from auth.rbac_safety import (
    validar_admin_funcional_restante,
    validar_delegacao_role,
    validar_delegacao_roles,
)

from models import User
# Schema utilizado pela operação de substituição completa
# das Roles de um usuário.
from schemas.auth import UserRolesUpdate
from user_roles.repository import (
    buscar_relacionamento,
    buscar_role_por_id,
    buscar_roles_por_ids,
    buscar_usuario_por_id,
    criar_relacionamento,
    listar_relacionamentos_usuario,
    remover_relacionamento,
    remover_relacionamentos_usuario,
)


# ============================================================
# SERIALIZAÇÃO INTERNA DA ROLE
# ============================================================

def _serializar_role(
    role,
) -> dict:
    """
    Converte uma Role para o contrato atualmente devolvido
    pela API.

    Esta transformação é pequena e específica deste domínio,
    portanto ainda não justifica um módulo serializers.py.
    """

    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
    }


# ============================================================
# LISTAR ROLES DE UM USUÁRIO
# ============================================================

def listar_roles_usuario_service(
    user_id: int,
    db: Session,
) -> list[dict]:
    """
    Retorna todas as Roles associadas ao usuário informado.

    Mantém o contrato HTTP já utilizado pelo Control Room.
    """

    usuario_alvo = buscar_usuario_por_id(
        db=db,
        user_id=user_id,
    )

    if not usuario_alvo:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado.",
        )

    relacionamentos = listar_relacionamentos_usuario(
        db=db,
        user_id=user_id,
    )

    resultado = []

    for relacionamento in relacionamentos:

        role = buscar_role_por_id(
            db=db,
            role_id=relacionamento.role_id,
        )

        # Mantém o comportamento histórico da listagem:
        # associações inconsistentes são ignoradas.
        if not role:
            continue

        resultado.append(
            _serializar_role(
                role
            )
        )

    return resultado


# ============================================================
# ASSOCIAR ROLE AO USUÁRIO
# ============================================================
def associar_role_usuario_service(
    user_id: int,
    role_id: int,
    db: Session,
    usuario_executor: User,
) -> dict:
    """
    Associa uma Role existente a um usuário existente.

    Regras:

        - usuário precisa existir;
        - Role precisa existir;
        - associação não pode existir previamente;
        - criação é persistida em uma única transação.
    """

    usuario_alvo = buscar_usuario_por_id(
        db=db,
        user_id=user_id,
    )

    if not usuario_alvo:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado.",
        )

    role = buscar_role_por_id(
        db=db,
        role_id=role_id,
    )

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role não encontrada.",
        )

    relacionamento_existente = buscar_relacionamento(
        db=db,
        user_id=user_id,
        role_id=role_id,
    )

    if relacionamento_existente:
        raise HTTPException(
            status_code=409,
            detail="Essa Role já está associada ao usuário.",
        )

    # ========================================================
    # SEGURANÇA DE DELEGAÇÃO
    # ========================================================
    #
    # O executor somente pode conceder esta Role se possuir
    # todas as permissões que a própria Role concede.
    #
    # A validação acontece ANTES de qualquer alteração no banco.
    # ========================================================

    validar_delegacao_role(
        usuario_executor=usuario_executor,
        role=role,
        db=db,
    )

    relacionamento = criar_relacionamento(
        db=db,
        user_id=user_id,
        role_id=role_id,
    )

    try:

        # O commit efetiva a associação.
        #
        # A validação anterior continua sendo importante para
        # devolver HTTP 409 antes de chegar ao banco na situação
        # normal de associação duplicada.
        db.commit()

        db.refresh(
            relacionamento
        )

    except IntegrityError:

        # Uma IntegrityError pode ocorrer por violação de
        # integridade referencial ou, futuramente, pela constraint
        # UNIQUE de user_id + role_id.
        #
        # Sempre fazemos rollback antes de reutilizar a sessão.
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Não foi possível associar a Role ao usuário "
                "por conflito de integridade."
            ),
        )

    except Exception:

        # Falhas inesperadas continuam sendo propagadas para o
        # tratamento global da aplicação, mas somente depois de
        # restaurarmos o estado transacional da sessão.
        db.rollback()

        raise

    return {
        "message": "Role associada ao usuário com sucesso.",
        "user_id": user_id,
        "role": _serializar_role(
            role
        ),
    }

# ============================================================
# SUBSTITUIR TODAS AS ROLES DO USUÁRIO
# ============================================================

def substituir_roles_usuario_service(
    user_id: int,
    request: UserRolesUpdate,
    db: Session,
    usuario_executor: User,
) -> dict:
    """
    Substitui completamente as Roles associadas ao usuário.

    Esta é a implementação canônica da operação User -> Role.

    Regras:

        - o usuário alvo precisa existir;
        - IDs duplicados são removidos;
        - todas as Roles solicitadas precisam existir;
        - somente Roles NOVAS passam pela validação de
          delegação;
        - Roles existentes podem ser mantidas;
        - Roles podem ser removidas mesmo que o executor não
          possua todas as permissões delas;
        - remoção e inclusão acontecem na mesma transação.

    O formato de retorno preserva o contrato atualmente usado
    pelo endpoint:

        PUT /auth/users/{user_id}/roles
    """

    # --------------------------------------------------------
    # VALIDAR USUÁRIO
    # --------------------------------------------------------

    usuario_alvo = buscar_usuario_por_id(
        db=db,
        user_id=user_id,
    )

    if not usuario_alvo:
        return {
            "status": "error",
            "message": "Usuário não encontrado.",
        }

    # --------------------------------------------------------
    # NORMALIZAR IDs
    # --------------------------------------------------------
    #
    # dict.fromkeys preserva a ordem recebida enquanto remove
    # IDs duplicados, mantendo o comportamento histórico.
    # --------------------------------------------------------

    role_ids = list(
        dict.fromkeys(
            request.role_ids
        )
    )

    # --------------------------------------------------------
    # BUSCAR E VALIDAR ROLES
    # --------------------------------------------------------

    roles = buscar_roles_por_ids(
        db=db,
        role_ids=role_ids,
    )

    if len(roles) != len(role_ids):
        return {
            "status": "error",
            "message": (
                "Uma ou mais Roles não foram encontradas."
            ),
        }

    # --------------------------------------------------------
    # IDENTIFICAR ROLES ATUAIS
    # --------------------------------------------------------

    relacionamentos_atuais = listar_relacionamentos_usuario(
        db=db,
        user_id=user_id,
    )

    role_ids_atuais = {
        relacionamento.role_id
        for relacionamento in relacionamentos_atuais
    }

    # --------------------------------------------------------
    # IDENTIFICAR SOMENTE NOVAS CONCESSÕES
    # --------------------------------------------------------
    #
    # Manter uma Role existente não é uma nova concessão.
    # Remover uma Role também não é uma concessão.
    #
    # Portanto somente Roles adicionadas precisam passar pela
    # proteção contra escalada de privilégios.
    # --------------------------------------------------------

    role_ids_novos = (
        set(role_ids)
        - role_ids_atuais
    )

    roles_novas = [
        role
        for role in roles
        if role.id in role_ids_novos
    ]

    validar_delegacao_roles(
        usuario_executor=usuario_executor,
        roles=roles_novas,
        db=db,
    )

    # --------------------------------------------------------
    # PROTEÇÃO CONTRA LOCKOUT ADMINISTRATIVO
    # --------------------------------------------------------
    #
    # Simula exatamente as Roles que o usuário terá depois da
    # operação. Se ele for o último administrador funcional e
    # perder essa capacidade, a alteração é recusada.
    # --------------------------------------------------------

    validar_admin_funcional_restante(
        db=db,
        user_id_alvo=user_id,
        role_ids_finais_usuario=set(
            role_ids
        ),
    )

    # --------------------------------------------------------
    # SUBSTITUIÇÃO TRANSACIONAL
    # --------------------------------------------------------

    try:

        # Remove todas as associações atuais.
        remover_relacionamentos_usuario(
            db=db,
            user_id=user_id,
        )

        # Cria exatamente as associações solicitadas.
        for role_id in role_ids:

            criar_relacionamento(
                db=db,
                user_id=user_id,
                role_id=role_id,
            )

        # A operação inteira é persistida em um único commit.
        db.commit()

    except IntegrityError:

        # Protege também contra conflitos de integridade que
        # possam ocorrer por concorrência.
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Não foi possível atualizar as Roles do usuário "
                "por conflito de integridade."
            ),
        )

    except Exception:

        # Nenhuma substituição parcial deve permanecer caso
        # ocorra uma falha inesperada.
        db.rollback()

        raise

    # --------------------------------------------------------
    # RESPOSTA
    # --------------------------------------------------------
    #
    # Mantém deliberadamente o contrato histórico consumido
    # pelo frontend.
    # --------------------------------------------------------

    return {
        "status": "success",
        "message": "Roles do usuário atualizadas com sucesso.",
        "user": {
            "id": usuario_alvo.id,
            "username": usuario_alvo.username,
            "name": usuario_alvo.name,
        },
        "roles": [
            {
                "id": role.id,
                "name": role.name,
            }
            for role in roles
        ],
    }
# ============================================================
# REMOVER ROLE DO USUÁRIO
# ============================================================

def remover_role_usuario_service(
    user_id: int,
    role_id: int,
    db: Session,
) -> dict:
    """
    Remove uma associação existente entre usuário e Role.

    A Role é validada antes da remoção para evitar que uma
    associação inconsistente provoque AttributeError durante
    a montagem da resposta HTTP.
    """

    relacionamento = buscar_relacionamento(
        db=db,
        user_id=user_id,
        role_id=role_id,
    )

    if not relacionamento:
        raise HTTPException(
            status_code=404,
            detail=(
                "Essa Role não está associada ao usuário."
            ),
        )

    role = buscar_role_por_id(
        db=db,
        role_id=role_id,
    )

    # O relacionamento deveria sempre apontar para uma Role
    # válida. Se o banco estiver inconsistente, devolvemos uma
    # falha controlada em vez de gerar AttributeError.
    if not role:
        raise HTTPException(
            status_code=409,
            detail=(
                "A associação do usuário referencia "
                "uma Role inexistente."
            ),
        )

    # ========================================================
    # PROTEÇÃO CONTRA LOCKOUT ADMINISTRATIVO
    # ========================================================
    #
    # Calcula as Roles que permanecerão com o usuário depois
    # desta remoção e valida o estado futuro antes de alterar
    # o relacionamento.
    # ========================================================

    relacionamentos_atuais = listar_relacionamentos_usuario(
        db=db,
        user_id=user_id,
    )

    role_ids_finais = {
        item.role_id
        for item in relacionamentos_atuais
        if item.role_id != role_id
    }

    validar_admin_funcional_restante(
        db=db,
        user_id_alvo=user_id,
        role_ids_finais_usuario=role_ids_finais,
    )

    remover_relacionamento(
        db=db,
        relacionamento=relacionamento,
    )

    try:

        db.commit()

    except Exception:

        db.rollback()

        raise

    return {
        "message": "Role removida do usuário com sucesso.",
        "user_id": user_id,
        "role": _serializar_role(
            role
        ),
    }