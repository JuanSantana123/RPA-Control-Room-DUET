# ============================================================
# LIBRARIES - CATALOG OBSERVABILITY
# ============================================================
#
# Eventos técnicos relacionados à consistência do catálogo
# publicado de Libraries.
#
# Este módulo NÃO possui regra de negócio nem acesso ao banco.
# ============================================================

import logging


logger = logging.getLogger("control_room")


def registrar_library_producao_inconsistente(
    *,
    library_id: int,
    production_version_id: int | None,
) -> None:
    """
    Registra inconsistência quando uma Library publicada aponta
    para uma versão de Produção que não pode ser utilizada pelo
    catálogo.

    O fluxo de listagem continua normalmente e a Library
    inconsistente não é oferecida ao projeto.
    """

    logger.warning(
        "Library publicada sem versão de Produção utilizável",
        extra={
            "event": "library.catalog.production.invalid",
            "category": "SYSTEM",
            "component": "library_catalog",
            "ui_visible": True,
            "status": "warning",
            "action": "resolve_production_version",
            "reason": "production_version_unavailable",

            "resource_type": "library",
            "resource_id": library_id,

            "library_id": library_id,
            "production_version_id": production_version_id,
        },
    )