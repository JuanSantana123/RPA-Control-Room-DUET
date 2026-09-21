# ============================================================
# ROUTER DO DASHBOARD
# ============================================================
#
# Camada HTTP do Dashboard do Control Room.
#
# Responsabilidades:
#
# - registrar os endpoints do Dashboard;
# - aplicar autenticação;
# - receber as requisições HTTP;
# - delegar regras de negócio aos services.
#
# As consultas e regras dos indicadores estão em:
#
#     dashboard/service.py
#
# ============================================================

from fastapi import APIRouter, Depends

from auth.dependencies import get_usuario_atual
# Dependência responsável pela autorização RBAC.
# A autenticação identifica o usuário; esta dependência valida
# se ele possui acesso à visão funcional do Dashboard.
from auth.permissions import require_permission
from dashboard.service import (
    consultar_dashboard_stats_service,
)


# ============================================================
# ROUTER
# ============================================================
#
# Todas as rotas deste router exigem autenticação através
# da sessão/cookie existente do Control Room.
#
# Mantemos esta dependência exatamente como no router original.
# ============================================================

router = APIRouter(
    tags=["Dashboard"],
    dependencies=[
        Depends(get_usuario_atual)
    ]
)


# ============================================================
# HEALTH CHECK DO CONTROL ROOM
# ============================================================
#
# Este endpoint permanece diretamente no router porque não
# possui regra de negócio ou acesso ao banco para extrair.
#
# Ele somente confirma que o Control Room está respondendo.
# ============================================================

@router.get(
    "/health",
    summary="Verificar saúde do Control Room",
    description=(
        "Verifica se o Control Room está online e respondendo. "
        "Quando a requisição é processada com sucesso, retorna "
        "o status 'online'. "
        "O endpoint utiliza a autenticação padrão do Control Room "
        "através da sessão/cookie."
    )
)
def health(
    usuario=Depends(get_usuario_atual)
):
    """
    Verifica se o Control Room está online.

    A dependência get_usuario_atual também permanece na função
    para preservar exatamente a estrutura de autenticação
    existente antes da modularização.
    """

    return {
        "status": "online"
    }


# ============================================================
# API ESTATÍSTICAS DO DASHBOARD
# ============================================================
#
# A camada HTTP somente recebe a requisição autenticada.
#
# A consulta dos indicadores foi movida para:
#
#     dashboard/service.py
#
# ============================================================

@router.get(
    "/dashboard/stats",
    summary="Consultar estatísticas do Dashboard",
    description=(
        "Retorna os principais indicadores utilizados pelo Dashboard "
        "do Control Room. "
        "São retornados o total de Agents cadastrados, a quantidade "
        "de Agents online e o total de robôs cadastrados."
    )
)
def dashboard_stats(
    # Além de estar autenticado, o usuário precisa possuir
    # acesso explícito à visão funcional do Dashboard.
    usuario=Depends(
        require_permission("Dashboard", "view")
    )
):
    """
    Retorna as principais estatísticas do Dashboard.

    O usuário autenticado continua sendo resolvido nesta camada,
    preservando a dependência HTTP existente.

    A consulta ao banco é delegada ao service.
    """

    return consultar_dashboard_stats_service()