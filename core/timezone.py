import os
from datetime import UTC, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_CONTROL_ROOM_TIMEZONE = "America/Sao_Paulo"


@lru_cache(maxsize=16)
def _load_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as error:
        raise RuntimeError(
            f"DUET_TIMEZONE inválido: '{name}'. Use um identificador IANA, "
            "por exemplo America/Sao_Paulo."
        ) from error


def get_control_room_timezone_name() -> str:
    name = os.getenv("DUET_TIMEZONE", DEFAULT_CONTROL_ROOM_TIMEZONE).strip()
    if not name:
        name = DEFAULT_CONTROL_ROOM_TIMEZONE

    _load_timezone(name)
    return name


def get_control_room_timezone() -> ZoneInfo:
    return _load_timezone(get_control_room_timezone_name())


def local_now_naive() -> datetime:
    """Retorna o horário civil do Control Room no formato legado do banco."""

    return datetime.now(get_control_room_timezone()).replace(tzinfo=None)


def validate_local_wall_time(value: datetime, timezone_name: str | None = None) -> None:
    """Rejeita horários inexistentes ou ambíguos em transições de DST."""

    if value.tzinfo is not None:
        raise ValueError("O horário local deve ser informado sem offset explícito.")

    timezone = _load_timezone(timezone_name or get_control_room_timezone_name())
    fold_zero = value.replace(tzinfo=timezone, fold=0)
    fold_one = value.replace(tzinfo=timezone, fold=1)

    def round_trips(candidate: datetime) -> bool:
        return (
            candidate.astimezone(UTC)
            .astimezone(timezone)
            .replace(tzinfo=None) == value
        )

    fold_zero_valid = round_trips(fold_zero)
    fold_one_valid = round_trips(fold_one)

    if not fold_zero_valid and not fold_one_valid:
        raise ValueError(
            "O horário informado não existe no fuso configurado devido à mudança de horário civil."
        )

    if (
        fold_zero_valid
        and fold_one_valid
        and fold_zero.utcoffset() != fold_one.utcoffset()
    ):
        raise ValueError(
            "O horário informado é ambíguo no fuso configurado devido à mudança de horário civil."
        )
