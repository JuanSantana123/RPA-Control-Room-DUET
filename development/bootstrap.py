"""Bootstrap idempotente dos dados estruturais de Desenvolvimento."""

from database import SessionLocal
from models import DevelopmentStage


DEFAULT_DEVELOPMENT_STAGES = (
    ("BACKLOG", "Backlog", 1),
    ("IN_DEVELOPMENT", "Em desenvolvimento", 2),
    ("READY_FOR_TEST", "Pronto para testes", 3),
    ("IN_TEST", "Em testes", 4),
    ("HOMOLOGATION", "Homologação", 5),
    ("APPROVED", "Aprovado", 6),
    ("PUBLISHED", "Publicado", 7),
)


def criar_estagios_desenvolvimento_iniciais() -> None:
    """Cria somente os estágios ausentes, preservando dados existentes.

    A posição canônica é usada quando estiver livre. Em instalações com
    configuração parcial ou personalizada, um novo estágio recebe a próxima
    posição disponível para não alterar nem invalidar o workflow existente.
    """

    db = SessionLocal()

    try:
        existing_stages = db.query(DevelopmentStage).all()
        existing_codes = {stage.code for stage in existing_stages}
        used_positions = {stage.position for stage in existing_stages}
        next_position = max(used_positions, default=0) + 1

        for code, name, preferred_position in DEFAULT_DEVELOPMENT_STAGES:
            if code in existing_codes:
                continue

            position = preferred_position
            if position in used_positions:
                while next_position in used_positions:
                    next_position += 1
                position = next_position

            db.add(
                DevelopmentStage(
                    code=code,
                    name=name,
                    position=position,
                    is_active=1,
                )
            )
            existing_codes.add(code)
            used_positions.add(position)
            next_position = max(next_position, position + 1)

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
