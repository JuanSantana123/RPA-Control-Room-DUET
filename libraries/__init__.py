# ============================================================
# LIBRARIES DOMAIN
# ============================================================
#
# Pacote responsável pelas regras de negócio do domínio global
# de bibliotecas reutilizáveis do DUET.
#
# A arquitetura separa:
#
# api/libraries.py
#     Responsável somente pela camada HTTP:
#     - rotas;
#     - parâmetros;
#     - Depends;
#     - RBAC;
#     - delegação para services.
#
# libraries/
#     Responsável pelo domínio:
#     - catálogo;
#     - pastas;
#     - versões;
#     - snapshots;
#     - dependências de projetos;
#     - validações;
#     - persistência física dos artefatos.
#
# Este __init__.py permanece propositalmente sem imports.
#
# Isso reduz acoplamento entre os módulos internos e ajuda a
# evitar imports circulares durante a modularização.
# ============================================================