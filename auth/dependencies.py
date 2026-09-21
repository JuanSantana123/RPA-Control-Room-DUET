# ============================================================
# DEPENDÊNCIAS DE AUTENTICAÇÃO
# ============================================================

# Importa o Cookie para receber o session_id
# enviado automaticamente pelo navegador.
from fastapi import (
    Cookie,
    HTTPException,
    Depends,
    Request,
)
from fastapi.security import HTTPBearer


from auth.session import obter_usuario_da_sessao
# Protege operações autenticadas automaticamente pelo
# cookie session_id contra Origins não confiáveis.
from auth.origin_security import validar_origin_cookie
from database import SessionLocal
from models import UserSession, User

from datetime import datetime

# ============================================================
# AUTENTICAÇÃO BEARER
# ============================================================

# Define o esquema HTTP Bearer utilizado pelo Swagger
# e pelos clientes que autenticam através da API.
#
# O esquema extrai opcionalmente o header:
#
#     Authorization: Bearer <access_token>
#
# A validação efetiva do token é centralizada na função
# validar_usuario_bearer().
bearer_scheme = HTTPBearer(
    auto_error=False
)


# ============================================================
# VALIDAR USUÁRIO POR BEARER TOKEN
# ============================================================

def validar_usuario_bearer(
    access_token: str,
):
    """
    Valida um Bearer Token e retorna o usuário autenticado.

    Esta função centraliza as regras compartilhadas por:

        - get_usuario_atual();
        - get_usuario_bearer().

    Regras:

        - o token precisa existir;
        - não pode estar revogado;
        - não pode estar expirado;
        - o usuário precisa existir;
        - o usuário precisa estar ativo.

    A função abre e fecha sua própria sessão de banco.

    Tokens expirados são rejeitados, mas não são modificados
    aqui. A limpeza física/lógica de credenciais expiradas
    será tratada posteriormente como política de manutenção
    das sessões, evitando commits ocultos nesta dependency.
    """

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # LOCALIZAR TOKEN ATIVO
        # ----------------------------------------------------

        sessao = (
            db.query(UserSession)
            .filter(
                UserSession.access_token == access_token,
                UserSession.revoked == 0,
            )
            .first()
        )

        if not sessao:
            raise HTTPException(
                status_code=401,
                detail="Token de acesso inválido.",
            )

        # ----------------------------------------------------
        # VALIDAR EXPIRAÇÃO
        # ----------------------------------------------------

        if sessao.expires_at <= datetime.utcnow():
            raise HTTPException(
                status_code=401,
                detail="Token de acesso expirado.",
            )

        # ----------------------------------------------------
        # VALIDAR USUÁRIO
        # ----------------------------------------------------

        usuario = (
            db.query(User)
            .filter(
                User.id == sessao.user_id,
                User.is_active == 1,
            )
            .first()
        )

        if not usuario:
            raise HTTPException(
                status_code=401,
                detail="Usuário não autenticado.",
            )

        return usuario

    finally:
        db.close()

# ============================================================
# USUÁRIO AUTENTICADO
# ============================================================

def get_usuario_atual(
    request: Request,
    session_id: str | None = Cookie(default=None),
    credentials=Depends(bearer_scheme),
):
    """
    Retorna o usuário autenticado.

    A autenticação pode ocorrer de duas formas:

    1. Cookie session_id
       - utilizado pelo Frontend.

    2. Authorization: Bearer <access_token>
       - utilizado pelo Swagger e clientes de API.

    Os dois mecanismos utilizam credenciais diferentes.
    """

    # ========================================================
    # PROTEÇÃO DE ORIGEM PARA AUTENTICAÇÃO POR COOKIE
    # ========================================================
    #
    # A validação somente interfere em operações mutáveis
    # autenticadas automaticamente pelo session_id.
    #
    # Bearer, GET, HEAD e OPTIONS são tratados pela própria
    # função de validação e não são bloqueados por esta regra.
    # ========================================================

    validar_origin_cookie(
        request=request,
    )
    # ========================================================
    # AUTENTICAÇÃO VIA BEARER
    # ========================================================

    if credentials:

        # Bearer possui prioridade quando foi explicitamente
        # enviado na requisição.
        #
        # Um Bearer inválido não deve cair silenciosamente para
        # uma sessão válida existente no cookie.
        return validar_usuario_bearer(
            access_token=credentials.credentials,
        )

    # ========================================================
    # AUTENTICAÇÃO VIA COOKIE
    # ========================================================

    # Se não existe Bearer, utiliza o session_id
    # enviado automaticamente pelo navegador.
    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Usuário não autenticado."
        )

    # Valida a sessão tradicional do Frontend.
    usuario = obter_usuario_da_sessao(
        session_id
    )

    # Sessão inválida, expirada ou inexistente.
    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Usuário não autenticado."
        )

    return usuario


def get_usuario_bearer(
    credentials=Depends(bearer_scheme)
):
    """
    Autentica exclusivamente através do Authorization Bearer.

    Esta dependência é destinada às APIs utilizadas pelo
    Swagger/API.

    Importante:
    - NÃO aceita session_id por cookie;
    - NÃO utiliza a sessão do navegador;
    - exige Authorization: Bearer <access_token>;
    - o token é validado na tabela UserSession.
    """

    # ============================================================
    # VERIFICAR SE O HEADER AUTHORIZATION FOI ENVIADO
    # ============================================================

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization Bearer não informado."
        )

    # ============================================================
    # VALIDAR TOKEN BEARER
    # ============================================================
    #
    # A regra de validação foi centralizada em
    # validar_usuario_bearer().
    #
    # Isso evita manter duas implementações diferentes para:
    #
    #   - get_usuario_atual();
    #   - get_usuario_bearer().
    #
    # Esta função continua sendo exclusivamente Bearer:
    # ela apenas delega a validação do token.
    # ============================================================

    return validar_usuario_bearer(
        access_token=credentials.credentials,
    )