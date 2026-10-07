"""
SDK oficial do DUET RPA.

Este pacote expõe funcionalidades da plataforma DUET para
as automações executadas pelo RPA Agent.

Exemplo:

    from rpa import vault
"""

# Disponibiliza o módulo Vault através da interface pública:
#
#     from rpa import vault
#
# Novos recursos da plataforma poderão ser adicionados aqui
# futuramente, como queue, logs e assets.
from . import vault


__all__ = [
    "vault",
]