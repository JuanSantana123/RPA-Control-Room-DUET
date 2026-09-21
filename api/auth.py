# ============================================================
# API - AUTENTICAÇÃO
# ============================================================
#
# Responsabilidade deste módulo:
#
#     - registrar os endpoints HTTP de autenticação;
#     - declarar as permissões RBAC necessárias;
#     - receber parâmetros HTTP;
#     - abrir/fechar sessões do banco;
#     - delegar regras de negócio aos services.
#
# As regras de negócio foram separadas em:
#
#     auth/users_service.py
#     auth/user_roles_service.py
#     auth/authentication_service.py
#
# Os contratos Pydantic ficam em:
#
#     schemas/auth.py
#
# ============================================================
from fastapi import (
    APIRouter,
    Request,
    Response,
    Cookie,
    Depends,
)

from database import SessionLocal

from auth.dependencies import (
    get_usuario_atual,
    bearer_scheme,
)
# Dependency responsável pela autorização RBAC das rotas.
from auth.permissions import require_permission

# Consulta a política de segurança utilizada pelo cookie
# de autenticação do Frontend.
from auth.security import cookie_secure_habilitado

from schemas.auth import (
    UserCreate,
    UserStatusUpdate,
    UserPasswordUpdate,
    UserRolesUpdate,
    UserLogin,
)

from auth.users_service import (
    alterar_status_usuario_service,
    criar_usuario_service,
    alterar_senha_usuario_service,
    listar_usuarios_service,
    excluir_usuario_service,
)

# ============================================================
# USER ROLES
# ============================================================
#
# A relação User -> Role possui um único domínio de negócio.
# O router /auth apenas preserva seu contrato HTTP histórico.
# ============================================================

from user_roles.service import (
    substituir_roles_usuario_service,
)

from auth.authentication_service import (
    gerar_token_api_service,
    fazer_login_service,
    usuario_atual_service,
    fazer_logout_service,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"],
)


# ============================================================
# CONEXÃO COM O BANCO
# ============================================================

def get_db():
    """
    Cria uma sessão SQLAlchemy para a requisição atual.

    O fechamento ocorre automaticamente quando a dependency
    termina, inclusive em caso de erro.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# CADASTRAR USUÁRIO
# ============================================================

@router.post(
    "/users",
    summary="Criar usuário",
    description=(
        "Cria um novo usuário no Control Room. "
        "O usuário pode ser associado a uma Role durante o cadastro. "
        "O username deve ser único. "
        "Requer a permissão 'Users:create'."
    ),
)
def criar_usuario(
    request: UserCreate,
    usuario=Depends(
        require_permission(
            "Users",
            "create",
        )
    ),
):
    """
    Cria um usuário e opcionalmente associa uma Role.
    """

    db = SessionLocal()

    try:
        return criar_usuario_service(
            request=request,
            db=db,
        )

    finally:
        db.close()


# ============================================================
# ALTERAR SENHA DE USUÁRIO
# ============================================================

@router.put(
    "/users/{user_id}/password",
    summary="Alterar senha de usuário",
    description=(
        "Altera a senha de um usuário específico. "
        "A nova senha é transformada em hash antes de ser armazenada. "
        "Requer a permissão 'Users:edit'."
    ),
)
def alterar_senha_usuario(
    user_id: int,
    request: UserPasswordUpdate,
    usuario=Depends(
        require_permission(
            "Users",
            "edit",
        )
    ),
):
    
    """
        Altera a senha de um usuário.

        A nova senha é recebida através de new_password,
        transformada em hash pelo service e, após a alteração,
        as credenciais existentes do usuário são revogadas.
    """

    db = SessionLocal()

    try:
        return alterar_senha_usuario_service(
            user_id=user_id,
            request=request,
            db=db,
        )

    finally:
        db.close()


# ============================================================
# LISTAR USUÁRIOS
# ============================================================

@router.get(
    "/users",
    summary="Listar usuários",
    description=(
        "Retorna todos os usuários cadastrados no Control Room, "
        "incluindo as Roles associadas a cada usuário. "
        "Senhas e password_hash nunca são retornados. "
        "Não é necessário informar parâmetros. "
        "Requer a permissão 'Users:view'."
    ),
)
def listar_usuarios(
    usuario=Depends(
        require_permission(
            "Users",
            "view",
        )
    ),
):
    """
    Lista os usuários e suas respectivas Roles.
    """

    db = SessionLocal()

    try:
        return listar_usuarios_service(
            db=db,
        )

    finally:
        db.close()


# ============================================================
# ALTERAR STATUS DO USUÁRIO
# ============================================================
#
# Segunda ocorrência existente no arquivo original.
#
# Não remover ainda.
# ============================================================

@router.patch(
    "/users/{user_id}/status",
    summary="Ativar ou desativar usuário",
    description=(
        "Altera o status de ativação de um usuário. "
        "Usuários desativados não conseguem realizar login. "
        "Requer a permissão 'Users:edit'."
    ),
)
def alterar_status_usuario(
    user_id: int,
    request: UserStatusUpdate,
    usuario=Depends(
        require_permission(
            "Users",
            "edit",
        )
    ),
):
    """
    Ativa ou desativa um usuário do Control Room.

    Ao desativar, as sessões e os tokens existentes do
    usuário também são revogados pelo service.
    """

    db = SessionLocal()

    try:
        return alterar_status_usuario_service(
            user_id=user_id,
            request=request,
            db=db,

            # Usuário autenticado que está executando
            # a operação administrativa.
            usuario_executor=usuario,
        )

    finally:
        db.close()


# ============================================================
# CONSULTAR ROLES DE UM USUÁRIO
# ============================================================

@router.get(
    "/users/{user_id}/roles",
    summary="Listar Roles do usuário",
    description=(
        "Retorna todas as Roles associadas a um usuário específico. "
        "É necessário informar o ID do usuário. "
        "Requer a permissão 'Users:view'."
    ),
)
def listar_roles_usuario(
    user_id: int,
    usuario=Depends(
        require_permission(
            "Users",
            "view",
        )
    ),
):
    """
    Lista as Roles associadas ao usuário informado.
    """

    db = SessionLocal()

    try:
        return listar_roles_usuario_service(
            user_id=user_id,
            db=db,
        )

    finally:
        db.close()


# ============================================================
# ATUALIZAR ROLES DO USUÁRIO
# ============================================================

@router.put(
    "/users/{user_id}/roles",
    summary="Atualizar Roles do usuário",
    description=(
        "Substitui as Roles atuais de um usuário pela lista "
        "de Roles informada. "
        "É possível adicionar, trocar ou remover Roles. "
        "Para remover todas as Roles, envie 'role_ids' como []. "
        "Requer a permissão 'Users:edit'."
    ),
)
def atualizar_roles_usuario(
    user_id: int,
    request: UserRolesUpdate,
    usuario=Depends(
        require_permission(
            "Users",
            "edit",
        )
    ),
):
    """
    Substitui as Roles atuais do usuário.
    """

    db = SessionLocal()

    try:
        return substituir_roles_usuario_service(
            user_id=user_id,
            request=request,
            db=db,

            # Identidade do usuário responsável pela alteração.
            # O domínio User Roles utiliza essa identidade para
            # impedir delegação de privilégios superiores.
            usuario_executor=usuario,
        )

    finally:
        db.close()


# ============================================================
# EXCLUIR USUÁRIO
# ============================================================

@router.delete(
    "/users/{user_id}",
    summary="Excluir usuário",
    description=(
        "Exclui um usuário do Control Room. "
        "As associações do usuário com suas Roles também são removidas. "
        "É necessário informar o ID do usuário. "
        "Requer a permissão 'Users:delete'."
    ),
)
def excluir_usuario(
    user_id: int,
    usuario=Depends(
        require_permission(
            "Users",
            "delete",
        )
    ),
):
    """
    Exclui o usuário e suas associações UserRole.
    """

    db = SessionLocal()

    try:
        return excluir_usuario_service(
            user_id=user_id,
            db=db,

            # Usuário autenticado responsável pela operação.
            usuario_executor=usuario,
        )

    finally:
        db.close()


# ============================================================
# GERAR TOKEN DA API
# ============================================================

@router.post(
    "/token",
    summary="Gerar Token API",
    description=(
        "Gera um access_token para autenticação da API "
        "por meio de Bearer Token. "
        "Utilize username e password de um usuário válido. "
        "O token gerado é utilizado para chamadas da API/Swagger "
        "que exigem autenticação Bearer. "
        "Este endpoint não cria uma sessão de navegador "
        "nem utiliza o cookie session_id."
    ),
)
def gerar_token_api(
    request: UserLogin,
    http_request: Request,
):
    """
    Gera um Bearer Token para utilização da API.
    """

    db = SessionLocal()

    try:
        # O IP utilizado pelo rate limit é o endereço da
        # conexão observado pelo servidor.
        #
        # Não confiamos diretamente em X-Forwarded-For.
        ip_origem = (
            http_request.client.host
            if http_request.client
            else None
        )

        return gerar_token_api_service(
            request=request,
            db=db,
            ip_origem=ip_origem,
        )

    finally:
        db.close()


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    summary="Fazer login",
    description=(
        "Autentica um usuário no Control Room e cria uma sessão "
        "para utilização pelo Frontend. "
        "Em caso de sucesso, o Control Room cria uma sessão "
        "e envia o cookie 'session_id' ao navegador."
    ),
)
def fazer_login(
    request: UserLogin,
    response: Response,
    http_request: Request,
):
    """
    Realiza o login do Frontend.

    O service cria a sessão no banco.
    O router grava o session_id no cookie HttpOnly.
    """

    db = SessionLocal()

    try:

        # O endereço utilizado pelo rate limit vem da conexão
        # observada pelo servidor.
        #
        # Não utilizamos X-Forwarded-For diretamente porque
        # esse header somente deve ser confiado quando a
        # infraestrutura de proxy estiver explicitamente
        # configurada como confiável.
        ip_origem = (
            http_request.client.host
            if http_request.client
            else None
        )

        resultado = fazer_login_service(
            request=request,
            db=db,
            ip_origem=ip_origem,
        )

        # ----------------------------------------------------
        # LOGIN RECUSADO
        # ----------------------------------------------------
        #
        # O comportamento HTTP/JSON original é preservado.
        # Se não houve sucesso, simplesmente devolvemos o
        # resultado produzido pelo service.
        # ----------------------------------------------------

        if resultado.get("status") != "success":
            return resultado

        # O session_id é informação interna necessária apenas
        # para criar o cookie.
        session_id = resultado.pop(
            "session_id"
        )

        # ----------------------------------------------------
        # ----------------------------------------------------
        # COOKIE DE AUTENTICAÇÃO
        # ----------------------------------------------------
        #
        # O cookie permanece HttpOnly para impedir acesso por
        # JavaScript executado no navegador.
        #
        # SameSite=Lax reduz o envio do cookie em requisições
        # cross-site.
        #
        # A flag Secure é controlada pelo ambiente:
        #
        #     CONTROL_ROOM_COOKIE_SECURE=false
        #         Desenvolvimento local via HTTP.
        #
        #     CONTROL_ROOM_COOKIE_SECURE=true
        #         Produção utilizando HTTPS.
        #
        # Dessa forma não quebramos o desenvolvimento local e
        # não precisamos alterar código para ativar a proteção
        # em produção.
        # ----------------------------------------------------

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            samesite="lax",
            secure=cookie_secure_habilitado(),
        )

        return resultado

    finally:
        db.close()


# ============================================================
# USUÁRIO ATUAL
# ============================================================

@router.get(
    "/me",
    summary="Obter usuário atual",
    description=(
        "Retorna os dados do usuário atualmente autenticado. "
        "Além dos dados básicos, retorna as permissões efetivas "
        "obtidas através das Roles do usuário."
    ),
)
def usuario_atual(
    usuario=Depends(
        get_usuario_atual
    ),
):
    """
    Retorna o usuário autenticado e suas permissões efetivas.
    """

    db = SessionLocal()

    try:
        return usuario_atual_service(
            usuario=usuario,
            db=db,
        )

    finally:
        db.close()


# ============================================================
# LOGOUT
# ============================================================

@router.post(
    "/logout",
    summary="Fazer logout",
    description=(
        "Encerra a autenticação atual do usuário. "
        "Pode ser utilizado pelo Frontend através do cookie "
        "'session_id' ou pela API/Swagger através de "
        "Authorization: Bearer <access_token>. "
        "A credencial correspondente é revogada no Control Room."
    ),
)
def fazer_logout(
    response: Response,

    # Cookie utilizado pela autenticação do Frontend.
    session_id: str | None = Cookie(
        default=None
    ),

    # Bearer opcional utilizado por Swagger/clientes da API.
    credentials=Depends(
        bearer_scheme
    ),

    # A requisição somente prossegue quando existe uma
    # autenticação válida.
    usuario=Depends(
        get_usuario_atual
    ),
):
    """
    Revoga a credencial utilizada e remove o cookie
    session_id do navegador.
    """

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # EXTRAIR BEARER TOKEN
        # ----------------------------------------------------

        access_token = None

        if credentials:
            access_token = (
                credentials.credentials
            )

        resultado = fazer_logout_service(
            usuario=usuario,
            db=db,
            session_id=session_id,
            access_token=access_token,
        )

        # A remoção do cookie é responsabilidade da camada
        # HTTP e permanece no router.
        response.delete_cookie(
            key="session_id"
        )

        return resultado

    finally:
        db.close()