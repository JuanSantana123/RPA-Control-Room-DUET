# ============================================================
# SERVICE - USUÁRIOS
# ============================================================
#
# Responsabilidade:
#     Concentrar as regras de negócio relacionadas ao
#     gerenciamento dos usuários do Control Room.
#
# Este módulo NÃO registra endpoints FastAPI.
# A autorização RBAC continuará sendo responsabilidade
# do router api/auth.py.
# ============================================================

from sqlalchemy.orm import Session

from models import (
    User,
    UserRole,
    Role,
    UserSession,
)
from auth.security import (
    gerar_hash_senha,
    validar_politica_senha,
)

# ============================================================
# SEGURANÇA RBAC
# ============================================================
#
# Impede que operações sobre usuários deixem o DUET sem
# nenhum usuário ativo capaz de administrar o próprio RBAC.
# ============================================================

from auth.rbac_safety import (
    validar_admin_funcional_restante,
)

from schemas.auth import (
    UserCreate,
    UserStatusUpdate,
    UserPasswordUpdate,
)


# ============================================================
# ALTERAR STATUS
# ============================================================

def alterar_status_usuario_service(
    user_id: int,
    request: UserStatusUpdate,
    db: Session,
    usuario_executor: User,
):
    """
    Ativa ou desativa um usuário.

    Segurança:
        Um usuário autenticado não pode desativar a própria
        conta através desta operação administrativa.

    Mantém no banco:
        1 -> ativo
        0 -> inativo
    """

    # --------------------------------------------------------
    # IMPEDIR AUTODESATIVAÇÃO
    # --------------------------------------------------------
    #
    # Um usuário com Users:edit não deve conseguir invalidar
    # administrativamente a própria conta.
    #
    # A proteção é aplicada somente quando a operação solicitada
    # é de desativação. A ativação de outro usuário continua
    # seguindo normalmente.
    # --------------------------------------------------------

    if (
        user_id == usuario_executor.id
        and request.is_active is False
    ):
        return {
            "status": "error",
            "message": (
                "Não é permitido desativar o próprio usuário."
            ),
        }
    usuario_alvo = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not usuario_alvo:
        return {
            "status": "error",
            "message": "Usuário não encontrado.",
        }

    # --------------------------------------------------------
    # PROTEÇÃO CONTRA LOCKOUT ADMINISTRATIVO
    # --------------------------------------------------------
    #
    # Se a operação solicitada for uma desativação, simulamos
    # o usuário sem nenhuma Role efetiva.
    #
    # Como somente usuários ATIVOS são considerados pela
    # proteção, isso representa corretamente o estado final:
    # esse usuário deixa de participar da administração RBAC.
    #
    # A ativação de usuário não reduz privilégios e, portanto,
    # não precisa desta validação.
    # --------------------------------------------------------

    if request.is_active is False:

        validar_admin_funcional_restante(
            db=db,
            user_id_alvo=user_id,
            role_ids_finais_usuario=set(),
        )

    # --------------------------------------------------------
    # ATUALIZAR STATUS DO USUÁRIO
    # --------------------------------------------------------
    #
    # Mantemos no banco:
    #
    #     1 -> usuário ativo
    #     0 -> usuário inativo
    # --------------------------------------------------------

    usuario_alvo.is_active = (
        1 if request.is_active else 0
    )

    # --------------------------------------------------------
    # REVOGAR CREDENCIAIS AO DESATIVAR
    # --------------------------------------------------------
    #
    # Quando o usuário é desativado, todas as sessões ainda
    # válidas são explicitamente revogadas.
    #
    # Isso inclui:
    #
    #     - sessões do Frontend (session_id);
    #     - Bearer Tokens da API (access_token).
    #
    # IMPORTANTE:
    # Ao reativar o usuário, essas credenciais NÃO são
    # restauradas. O usuário deverá autenticar novamente.
    # --------------------------------------------------------

    if usuario_alvo.is_active == 0:

        db.query(UserSession).filter(
            UserSession.user_id == usuario_alvo.id,
            UserSession.revoked == 0,
        ).update(
            {
                UserSession.revoked: 1,
            },
            synchronize_session=False,
        )

    # --------------------------------------------------------
    # CONFIRMAR TRANSAÇÃO
    # --------------------------------------------------------
    #
    # A alteração do status e, quando aplicável, a revogação
    # das credenciais são confirmadas juntas.
    # --------------------------------------------------------

    db.commit()
    db.refresh(usuario_alvo)

    return {
        "status": "success",
        "message": (
            "Usuário ativado com sucesso."
            if usuario_alvo.is_active == 1
            else "Usuário desativado com sucesso."
        ),
        "user": {
            "id": usuario_alvo.id,
            "username": usuario_alvo.username,
            "name": usuario_alvo.name,
            "is_active": usuario_alvo.is_active,
        },
    }


# ============================================================
# CRIAR USUÁRIO
# ============================================================

def criar_usuario_service(
    request: UserCreate,
    db: Session,
):
    """
    Cria um usuário e, opcionalmente, associa uma Role.

    A criação do usuário e da associação UserRole ocorre
    dentro da mesma transação.
    """

    usuario_existente = (
        db.query(User)
        .filter(
            User.username == request.username
        )
        .first()
    )

    if usuario_existente:
        return {
            "status": "error",
            "message": "Username já cadastrado.",
        }

    senha_hash = gerar_hash_senha(
        request.password
    )


    # --------------------------------------------------------
    # VALIDAR POLÍTICA DE SENHA
    # --------------------------------------------------------
    #
    # A mesma política é utilizada tanto na criação quanto
    # na alteração da senha de um usuário.
    #
    # A senha somente será transformada em hash depois de
    # passar por todas as validações.
    # --------------------------------------------------------

    senha_valida, mensagem_erro = validar_politica_senha(
        request.password
    )

    if not senha_valida:
        return {
            "status": "error",
            "message": mensagem_erro,
        }

    usuario = User(
        username=request.username,
        password_hash=senha_hash,
        name=request.name,
        is_active=1,
    )

    db.add(usuario)

    # Precisamos do ID antes de criar UserRole,
    # mas ainda não confirmamos a transação.
    db.flush()

    if request.role_id is not None:

        role = (
            db.query(Role)
            .filter(Role.id == request.role_id)
            .first()
        )

        if not role:
            db.rollback()

            return {
                "status": "error",
                "message": "Role não encontrada.",
            }

        usuario_role = UserRole(
            user_id=usuario.id,
            role_id=role.id,
        )

        db.add(usuario_role)

    db.commit()
    db.refresh(usuario)

    return {
        "status": "success",
        "message": "Usuário criado com sucesso.",
        "user": {
            "id": usuario.id,
            "username": usuario.username,
            "name": usuario.name,
            "is_active": usuario.is_active,
        },
    }


# ============================================================
# ALTERAR SENHA
# ============================================================

def alterar_senha_usuario_service(
    user_id: int,
    request: UserPasswordUpdate,
    db: Session,
):
    """
    Altera a senha de um usuário.

    O campo recebido pelo contrato é "new_password".
    A senha é transformada em hash antes de ser persistida
    no banco de dados.
    """

    usuario_alvo = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not usuario_alvo:
        return {
            "status": "error",
            "message": "Usuário não encontrado.",
        }

    # --------------------------------------------------------
    # --------------------------------------------------------
    # --------------------------------------------------------
    # VALIDAR POLÍTICA DA NOVA SENHA
    # --------------------------------------------------------
    #
    # O contrato UserPasswordUpdate utiliza "new_password".
    #
    # A mesma política utilizada na criação de usuários é
    # aplicada aqui antes da geração do novo hash.
    # --------------------------------------------------------

    senha_valida, mensagem_erro = validar_politica_senha(
        request.new_password
    )

    if not senha_valida:
        return {
            "status": "error",
            "message": mensagem_erro,
        }

    # A senha original nunca é armazenada diretamente.
    # Somente o hash gerado é persistido no usuário.
    nova_senha_hash = gerar_hash_senha(
        request.new_password
    )




    # --------------------------------------------------------
    # ATUALIZAR SENHA
    # --------------------------------------------------------
    #
    # A nova senha já foi transformada em hash.
    # A alteração ainda não é confirmada neste ponto para que
    # a troca da senha e a revogação das credenciais façam
    # parte da mesma transação.
    # --------------------------------------------------------

    usuario_alvo.password_hash = nova_senha_hash

    # --------------------------------------------------------
    # REVOGAR SESSÕES E TOKENS EXISTENTES
    # --------------------------------------------------------
    #
    # Uma alteração de senha é uma mudança de credencial.
    #
    # Todas as UserSession ainda válidas do usuário são
    # revogadas, independentemente de representarem:
    #
    #     - sessão do Frontend (session_id);
    #     - Bearer Token da API (access_token).
    #
    # Dessa forma, uma credencial obtida antes da alteração
    # da senha não continua dando acesso ao Control Room.
    # --------------------------------------------------------

    db.query(UserSession).filter(
        UserSession.user_id == usuario_alvo.id,
        UserSession.revoked == 0,
    ).update(
        {
            UserSession.revoked: 1,
        },
        synchronize_session=False,
    )

    # --------------------------------------------------------
    # CONFIRMAR TRANSAÇÃO
    # --------------------------------------------------------
    #
    # A nova senha e a revogação das sessões são persistidas
    # juntas. Assim evitamos confirmar uma operação sem a
    # outra.
    # --------------------------------------------------------

    db.commit()

    return {
        "status": "success",
        "message": "Senha do usuário alterada com sucesso.",
    }


# ============================================================
# LISTAR USUÁRIOS
# ============================================================

def listar_usuarios_service(
    db: Session,
):
    """
    Lista os usuários e suas respectivas Roles.

    Mantém a estratégia de consulta existente no código
    original para preservar comportamento nesta etapa.
    """

    usuarios = (
        db.query(User)
        .order_by(User.id)
        .all()
    )

    resultado = []

    for user in usuarios:

        user_roles = (
            db.query(UserRole)
            .filter(
                UserRole.user_id == user.id
            )
            .all()
        )

        roles = []

        for user_role in user_roles:

            role = (
                db.query(Role)
                .filter(
                    Role.id == user_role.role_id
                )
                .first()
            )

            if role:
                roles.append(
                    {
                        "id": role.id,
                        "name": role.name,
                    }
                )

        resultado.append(
            {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "is_active": user.is_active,
                "roles": roles,
            }
        )

    return resultado


# ============================================================
# EXCLUIR USUÁRIO
# ============================================================


def excluir_usuario_service(
    user_id: int,
    db: Session,
    usuario_executor: User,
):
    """
    Remove operacionalmente um usuário do Control Room.

    O registro de User NÃO é apagado fisicamente.

    Isso preserva referências históricas existentes em
    projetos, execuções, schedules, comentários, releases,
    bibliotecas e demais entidades que registram o usuário
    responsável por uma operação.

    A exclusão operacional executa três ações na mesma
    transação:

        1. desativa o usuário;
        2. revoga todas as sessões e Bearer Tokens;
        3. remove suas associações atuais com Roles.
    """

    # --------------------------------------------------------
    # IMPEDIR AUTOEXCLUSÃO
    # --------------------------------------------------------
    #
    # A exclusão operacional desativa o usuário, revoga suas
    # credenciais e remove suas Roles.
    #
    # Portanto, um usuário autenticado não pode executar essa
    # operação administrativa contra a própria conta.
    # --------------------------------------------------------

    if user_id == usuario_executor.id:
        return {
            "status": "error",
            "message": (
                "Não é permitido excluir o próprio usuário."
            ),
        }
    # --------------------------------------------------------
    # BUSCAR USUÁRIO
    # --------------------------------------------------------

    usuario_alvo = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not usuario_alvo:
        return {
            "status": "error",
            "message": "Usuário não encontrado.",
        }


    # --------------------------------------------------------
    # PROTEÇÃO CONTRA LOCKOUT ADMINISTRATIVO
    # --------------------------------------------------------
    #
    # A exclusão do DUET é operacional:
    #
    #     - desativa o usuário;
    #     - revoga suas credenciais;
    #     - remove suas Roles.
    #
    # Portanto simulamos o usuário sem Roles antes de executar
    # qualquer uma dessas alterações.
    # --------------------------------------------------------

    validar_admin_funcional_restante(
        db=db,
        user_id_alvo=user_id,
        role_ids_finais_usuario=set(),
    )

    # --------------------------------------------------------
    # DESATIVAR USUÁRIO
    # --------------------------------------------------------
    #
    # Não fazemos hard delete do registro de User.
    #
    # O ID precisa continuar existindo porque outras tabelas
    # utilizam esse usuário como referência histórica.
    # --------------------------------------------------------

    usuario_alvo.is_active = 0

    # --------------------------------------------------------
    # REVOGAR CREDENCIAIS
    # --------------------------------------------------------
    #
    # Revoga tanto:
    #
    #     - sessões do Frontend;
    #     - Bearer Tokens da API.
    #
    # Credenciais antigas não poderão voltar a ser utilizadas
    # caso o registro seja manipulado posteriormente.
    # --------------------------------------------------------

    db.query(UserSession).filter(
        UserSession.user_id == usuario_alvo.id,
        UserSession.revoked == 0,
    ).update(
        {
            UserSession.revoked: 1,
        },
        synchronize_session=False,
    )

    # --------------------------------------------------------
    # REMOVER ROLES ATUAIS
    # --------------------------------------------------------
    #
    # UserRole representa autorização atual, e não histórico.
    #
    # Ao remover operacionalmente o usuário, retiramos também
    # todas as permissões que ele recebe através das Roles.
    # --------------------------------------------------------

    db.query(UserRole).filter(
        UserRole.user_id == usuario_alvo.id
    ).delete(
        synchronize_session=False
    )

    # --------------------------------------------------------
    # CONFIRMAR TRANSAÇÃO
    # --------------------------------------------------------
    #
    # Desativação, revogação das credenciais e remoção das
    # Roles são persistidas juntas.
    # --------------------------------------------------------

    db.commit()

    return {
        "status": "success",
        "message": "Usuário excluído com sucesso.",
    }