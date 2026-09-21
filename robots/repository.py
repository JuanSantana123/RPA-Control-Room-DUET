# ============================================================
# DUET CORE - ROBOTS - REPOSITÓRIO E INTEGRIDADE
# ============================================================
#
# Centraliza somente a localização física do repositório de
# Robots e o cálculo SHA-256 já utilizados pelo router atual.
#
# NÃO acessa banco, NÃO cria RobotVersion e NÃO registra rotas.
# ============================================================

import os
from hashlib import sha256
from pathlib import Path


BASE_DIRECTORY = Path(
    os.path.abspath(__file__)
).parent.parent


ROBOT_REPOSITORY = (
    BASE_DIRECTORY / "repository"
)


ROBOT_REPOSITORY.mkdir(
    parents=True,
    exist_ok=True
)


def calcular_hash_arquivo(
    arquivo: bytes
):
    """
    Calcula o SHA-256 do arquivo.

    O hash é utilizado para descobrir se o robô enviado
    é exatamente igual ao que já está cadastrado.
    """

    return sha256(
        arquivo
    ).hexdigest()
