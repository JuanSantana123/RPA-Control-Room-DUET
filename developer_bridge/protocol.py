from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True)
class OpenProjectRequest:
    server: str
    project_id: int
    project_name: str
    launch_code: str


def parse_open_project_uri(uri: str) -> OpenProjectRequest:
    """Interpreta duet://open?server=...&project_id=...&project_name=...&code=..."""

    parsed = urlparse(uri)

    if parsed.scheme.lower() != "duet":
        raise ValueError("Protocolo inválido.")

    if parsed.netloc.lower() != "open":
        raise ValueError("Ação do protocolo DUET não suportada.")

    params = parse_qs(parsed.query)

    def required(name: str) -> str:
        values = params.get(name)

        if not values or not values[0]:
            raise ValueError(f"Parâmetro obrigatório ausente: {name}")

        return values[0]

    server = required("server").rstrip("/")
    project_id = int(required("project_id"))
    project_name = required("project_name")
    launch_code = required("code")

    if not server.lower().startswith(("http://", "https://")):
        raise ValueError("URL do Control Room inválida.")

    return OpenProjectRequest(
        server=server,
        project_id=project_id,
        project_name=project_name,
        launch_code=launch_code,
    )
