# ============================================================
# LOGS - SERVICE
# ============================================================
#
# Responsável pela regra de negócio relacionada à consulta dos
# logs estruturados do Control Room.
#
# Este módulo:
#
# - localiza o arquivo de log;
# - lê somente a quantidade solicitada de linhas;
# - interpreta cada linha como JSON;
# - ignora registros antigos ou inválidos;
# - permite filtrar os registros por nível;
# - retorna os registros mais recentes primeiro.
#
# A camada HTTP permanece em:
#
#     api/logs.py
#
# Dessa forma, o service não conhece FastAPI, Query, Depends
# ou autenticação de usuário.
# ============================================================

from collections import deque
import logging
from pathlib import Path
import json


# ============================================================
# ARQUIVO DE LOG
# ============================================================
#
# Mantemos exatamente o mesmo caminho utilizado pelo router
# original para não alterar o comportamento existente.
# ============================================================

LOG_FILE = Path("logs") / "control_room.log"
logger = logging.getLogger("control_room")


def _texto_seguro(valor, *, padrao: str = "", limite: int = 4000) -> str:
    if not isinstance(valor, str) or not valor:
        return padrao

    return valor[:limite]


def _serializar_log(log_data: dict) -> dict:
    """Expõe somente metadados operacionais aprovados para a interface."""

    return {
        "timestamp": _texto_seguro(log_data.get("timestamp"), limite=80),
        "level": _texto_seguro(log_data.get("level"), padrao="INFO", limite=20),
        "message": _texto_seguro(log_data.get("message"), limite=4000),
        "event": _texto_seguro(log_data.get("event"), limite=120) or None,
        "request_id": _texto_seguro(log_data.get("request_id"), limite=128) or None,
        "service": _texto_seguro(log_data.get("service"), limite=120) or None,
    }


# ============================================================
# LISTAR LOGS
# ============================================================

def listar_logs_service(
    limit: int = 200,
    level: str | None = None,
):
    """
    Consulta os logs estruturados registrados pelo Control Room.

    Parâmetros
    ----------
    limit:
        Quantidade máxima de linhas mais recentes do arquivo
        que serão consideradas.

    level:
        Filtro opcional pelo nível do log, por exemplo:
        INFO, WARNING ou ERROR.

    Retorno
    -------
    dict
        Estrutura utilizada pela API contendo o status da
        operação e a lista de logs encontrados.

    Observação
    ----------
    Linhas que não possam ser interpretadas como JSON são
    ignoradas, preservando o comportamento do router original.
    """

    # ========================================================
    # ARQUIVO AINDA NÃO EXISTE
    # ========================================================

    if not LOG_FILE.exists():

        return {
            "status": "success",
            "logs": [],
            "total": 0,
            "truncated": False,
        }

    try:

        # ====================================================
        # LEITURA DO ARQUIVO
        # ====================================================

        logs = deque(maxlen=limit)
        total = 0

        with open(
            LOG_FILE,
            "r",
            encoding="utf-8",
        ) as arquivo:

            # O arquivo é percorrido em streaming: a memória permanece
            # limitada à página solicitada mesmo quando o log cresce.
            for linha in arquivo:

                linha = linha.strip()

                if not linha:
                    continue

                try:

                    log_data = json.loads(linha)

                except (json.JSONDecodeError, TypeError):
                    continue

                if not isinstance(log_data, dict):
                    continue

                nivel = _texto_seguro(
                    log_data.get("level"),
                    padrao="INFO",
                    limite=20,
                ).upper()

                if level and nivel != level.upper():
                    continue

                log_data["level"] = nivel
                total += 1
                logs.append(_serializar_log(log_data))

        registros = list(reversed(logs))

        return {
            "status": "success",
            "logs": registros,
            "total": total,
            "truncated": total > len(registros),
        }

    except Exception as error:

        logger.exception(
            "Falha ao consultar arquivo de logs",
            extra={
                "event": "system_logs_read_failed",
                "error_type": type(error).__name__,
            },
        )

        return {
            "status": "error",
            "message": "Não foi possível carregar os logs.",
        }
