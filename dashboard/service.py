# ============================================================
# DASHBOARD SERVICE
# ============================================================
#
# Regras de negócio responsáveis pelos indicadores exibidos
# no Dashboard do Control Room.
#
# Responsabilidades:
#
# - consultar quantidade de Agents ativos;
# - consultar quantidade de Agents ativos e online;
# - consultar quantidade total de robôs;
# - controlar a sessão de banco utilizada pelas consultas;
# - preservar o tratamento de erro atual do Dashboard.
#
# Este módulo NÃO:
#
# - registra endpoints FastAPI;
# - autentica usuários;
# - declara Depends();
# - conhece detalhes da camada HTTP.
#
# ============================================================

from database import SessionLocal
from models import Agent, Robot


# ============================================================
# CONSULTAR ESTATÍSTICAS DO DASHBOARD
# ============================================================

def consultar_dashboard_stats_service():
    """
    Consulta os principais indicadores operacionais exibidos
    no Dashboard do Control Room.

    Indicadores retornados
    ----------------------
    total_agents:
        Quantidade de Agents ativos cadastrados.

    agents_online:
        Quantidade de Agents ativos cujo status atual é online.

    total_robots:
        Quantidade total de robôs cadastrados.

    Observação
    ----------
    Agents removidos logicamente permanecem no banco, mas não
    participam dos indicadores operacionais.

    O comportamento de erro também é preservado: uma falha na
    consulta retorna um dicionário com status="error" em vez de
    propagar uma HTTPException.
    """

    # ========================================================
    # SESSÃO DO BANCO
    # ========================================================

    db = SessionLocal()

    try:

        # ====================================================
        # TOTAL DE AGENTS
        # ====================================================
        #
        # Conta somente Agents ativos.
        #
        # Agents removidos logicamente permanecem armazenados
        # para preservação do histórico, mas não entram neste
        # indicador.
        # ====================================================

        total_agents = (
            db.query(Agent)
            .filter(
                Agent.is_active == 1
            )
            .count()
        )


        # ====================================================
        # AGENTS ONLINE
        # ====================================================
        #
        # Para participar deste indicador o Agent precisa:
        #
        # 1. estar ativo;
        # 2. possuir status "online".
        # ====================================================

        agents_online = (
            db.query(Agent)
            .filter(
                Agent.status == "online",
                Agent.is_active == 1,
            )
            .count()
        )


        # ====================================================
        # TOTAL DE ROBÔS
        # ====================================================
        #
        # Preservamos exatamente a regra atual:
        #
        #     db.query(Robot).count()
        #
        # Portanto não adicionamos filtros de status, pasta,
        # versão ou qualquer outro critério.
        # ====================================================

        total_robots = (
            db.query(Robot)
            .count()
        )


        # ====================================================
        # RETORNO
        # ====================================================

        return {
            "status": "success",
            "total_agents": total_agents,
            "agents_online": agents_online,
            "total_robots": total_robots,
        }


    except Exception as error:

        # ====================================================
        # TRATAMENTO DE ERRO
        # ====================================================
        #
        # Não transformamos este comportamento em HTTPException.
        #
        # O endpoint atual retorna status="error" no próprio
        # payload e isso será mantido durante a modularização.
        # ====================================================

        return {
            "status": "error",
            "message": (
                "Não foi possível carregar as estatísticas "
                "do Dashboard"
            ),
            "error": str(error),
        }


    finally:

        # ====================================================
        # ENCERRAMENTO DA SESSÃO
        # ====================================================

        db.close()