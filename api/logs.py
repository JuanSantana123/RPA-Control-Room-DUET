# ============================================================
# API - LOGS
# ============================================================
#
# Camada HTTP responsável por disponibilizar os logs do
# Control Room.
#
# RESPONSABILIDADES DESTE ARQUIVO:
#
# - registrar as rotas HTTP;
# - validar a sessão do usuário;
# - validar parâmetros recebidos pela API;
# - delegar o processamento para logs/service.py.
#
# A leitura e o processamento do arquivo control_room.log
# não pertencem mais ao router.
# ============================================================

from fastapi import APIRouter, Query, Depends

# Dependência responsável por validar
# a sessão do usuário autenticado.
from auth.dependencies import get_usuario_atual
# Dependência responsável pela autorização RBAC.
# A autenticação identifica o usuário; esta dependência valida
# se ele possui acesso à visão funcional de Logs.
from auth.permissions import require_permission
# Service responsável pela leitura, filtro e processamento
# dos registros do arquivo de log.
from logs.service import listar_logs_service


# ============================================================
# ROUTER
# ============================================================
#
# Preserva exatamente a autenticação global existente no
# router original.
# ============================================================

router = APIRouter(
    tags=["Logs"],
    dependencies=[
        Depends(get_usuario_atual)
    ]
)


# ============================================================
# LISTAR LOGS
# ============================================================

@router.get("/logs")
def listar_logs(
    limit: int = Query(
        default=200,
        ge=1,
        le=1000
    ),
    level: str | None = None,

    # O usuário precisa possuir permissão explícita para
    # visualizar os Logs do Control Room.
    usuario=Depends(
        require_permission("Logs", "view")
    )
):
    """
    Retorna os logs do sistema registrados pelo Control Room.

    Parâmetros
    ----------
    limit:
        Quantidade máxima de linhas recentes que serão
        consideradas. O FastAPI mantém a validação entre
        1 e 1000 registros.

    level:
        Filtro opcional pelo nível do log, como INFO,
        WARNING ou ERROR.

    Retorno
    -------
    dict
        Resultado produzido pelo service de logs.
    """

    # A camada HTTP apenas encaminha os parâmetros já
    # validados pelo FastAPI para a regra de negócio.
    return listar_logs_service(
        limit=limit,
        level=level,
    )