# ============================================================
# SEGURANÇA DE ORIGEM
# ============================================================
#
# Responsabilidade deste módulo:
#
#     - carregar os Origins confiáveis do Control Room;
#     - fornecer a mesma configuração para o CORS;
#     - proteger requisições autenticadas por cookie contra
#       requisições cross-site não autorizadas.
#
# A lista de Origins pode ser configurada através de:
#
#     CONTROL_ROOM_ALLOWED_ORIGINS
#
# Exemplo:
#
#     http://localhost:5173,https://duet.empresa.com.br
#
# Em desenvolvimento, quando a variável não existir, o
# Frontend local permanece permitido.
# ============================================================

import os

from fastapi import HTTPException, Request


# ============================================================
# CONFIGURAÇÃO PADRÃO
# ============================================================

DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:5173",
)


# ============================================================
# CARREGAR ORIGINS PERMITIDOS
# ============================================================

def obter_origins_permitidos() -> list[str]:
    """
    Retorna os Origins confiáveis utilizados pelo Control Room.

    A variável CONTROL_ROOM_ALLOWED_ORIGINS aceita múltiplos
    valores separados por vírgula.

    Exemplo:

        CONTROL_ROOM_ALLOWED_ORIGINS=
        https://duet.empresa.com.br,https://admin.empresa.com.br

    Quando a variável não está configurada, utiliza somente
    o Frontend local de desenvolvimento.
    """

    valor = os.getenv(
        "CONTROL_ROOM_ALLOWED_ORIGINS",
        "",
    ).strip()

    if not valor:
        return list(DEFAULT_ALLOWED_ORIGINS)

    origins = []

    for origin in valor.split(","):

        origin_normalizado = origin.strip().rstrip("/")

        if origin_normalizado:
            origins.append(
                origin_normalizado
            )

    # Uma variável configurada mas vazia/inválida não deve
    # ampliar silenciosamente a superfície permitida.
    if not origins:
        return list(DEFAULT_ALLOWED_ORIGINS)

    return origins


# ============================================================
# VALIDAR ORIGIN DE REQUISIÇÃO AUTENTICADA POR COOKIE
# ============================================================

def validar_origin_cookie(
    request: Request,
) -> None:
    """
    Protege operações mutáveis autenticadas através do cookie
    session_id.

    A validação somente é necessária quando:

        - existe session_id;
        - NÃO existe Authorization Bearer;
        - o método HTTP pode alterar estado.

    Clientes autenticados explicitamente por Bearer não
    dependem de credenciais anexadas automaticamente pelo
    navegador e, portanto, não entram nesta validação.

    GET, HEAD e OPTIONS não modificam estado e são ignorados.
    """

    if request.method.upper() in {
        "GET",
        "HEAD",
        "OPTIONS",
    }:
        return

    # Sem cookie de autenticação não existe autenticação
    # automática do navegador para proteger neste ponto.
    session_id = request.cookies.get(
        "session_id"
    )

    if not session_id:
        return

    # Quando um Bearer foi explicitamente enviado, a própria
    # autenticação do Control Room dá prioridade ao Bearer.
    authorization = request.headers.get(
        "authorization",
        ""
    )

    if authorization.lower().startswith(
        "bearer "
    ):
        return

    # O header Origin é enviado pelos navegadores nas
    # requisições CORS e nas principais requisições mutáveis.
    origin = request.headers.get(
        "origin"
    )

    if not origin:
        raise HTTPException(
            status_code=403,
            detail="Origin não informado.",
        )

    origin_normalizado = (
        origin.strip().rstrip("/")
    )

    if origin_normalizado not in obter_origins_permitidos():
        raise HTTPException(
            status_code=403,
            detail="Origin não permitido.",
        )