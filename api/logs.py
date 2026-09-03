from fastapi import APIRouter, Query
from pathlib import Path


router = APIRouter(
    tags=["Logs"]
)


LOG_FILE = Path("logs") / "control_room.log"


@router.get("/logs")
def listar_logs(
    limit: int = Query(
        default=200,
        ge=1,
        le=1000
    ),
    level: str | None = None
):
    """
    Retorna os logs do sistema registrados pelo Control Room.
    """

    if not LOG_FILE.exists():
        return {
            "status": "success",
            "logs": []
        }

    try:
        with open(
            LOG_FILE,
            "r",
            encoding="utf-8"
        ) as arquivo:
            linhas = arquivo.readlines()

        # Mantém somente as últimas linhas solicitadas.
        linhas = linhas[-limit:]

        logs = []

        for linha in linhas:
            linha = linha.strip()

            if not linha:
                continue

            partes = linha.split(
                " | ",
                2
            )

            if len(partes) != 3:
                continue

            timestamp, nivel, mensagem = partes

            # Permite filtrar por nível:
            # INFO, WARNING, ERROR etc.
            if level and nivel.upper() != level.upper():
                continue

            logs.append({
                "timestamp": timestamp,
                "level": nivel,
                "message": mensagem
            })

        # Mais recentes primeiro na tela.
        logs.reverse()

        return {
            "status": "success",
            "logs": logs
        }

    except Exception as error:
        return {
            "status": "error",
            "message": "Não foi possível carregar os logs.",
            "error": str(error)
        }