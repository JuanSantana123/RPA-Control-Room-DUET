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
        }

    try:

        # ====================================================
        # LEITURA DO ARQUIVO
        # ====================================================

        with open(
            LOG_FILE,
            "r",
            encoding="utf-8",
        ) as arquivo:

            linhas = arquivo.readlines()

        # Mantém somente as últimas linhas solicitadas.
        linhas = linhas[-limit:]

        logs = []

        # ====================================================
        # PROCESSAMENTO DOS REGISTROS
        # ====================================================

        for linha in linhas:

            linha = linha.strip()

            # Ignora linhas vazias.
            if not linha:
                continue

            try:

                # Cada linha válida do arquivo deve representar
                # um objeto JSON estruturado.
                log_data = json.loads(linha)

            except json.JSONDecodeError:

                # Preserva a compatibilidade com arquivos que
                # ainda possam possuir registros antigos ou
                # linhas inválidas.
                continue

            timestamp = log_data.get(
                "timestamp",
                "",
            )

            nivel = log_data.get(
                "level",
                "INFO",
            )

            mensagem = log_data.get(
                "message",
                "",
            )

            # =================================================
            # FILTRO POR NÍVEL
            # =================================================
            #
            # A comparação continua case-insensitive,
            # exatamente como no comportamento original.
            # =================================================

            if (
                level
                and nivel.upper() != level.upper()
            ):
                continue

            logs.append({
                "timestamp": timestamp,
                "level": nivel,
                "message": mensagem,
            })

        # ====================================================
        # ORDENAÇÃO
        # ====================================================
        #
        # O arquivo é lido em ordem cronológica.
        # Invertemos para apresentar os registros mais recentes
        # primeiro, preservando o comportamento atual.
        # ====================================================

        logs.reverse()

        return {
            "status": "success",
            "logs": logs,
        }

    except Exception as error:

        return {
            "status": "error",
            "message": "Não foi possível carregar os logs.",
            "error": str(error),
        }