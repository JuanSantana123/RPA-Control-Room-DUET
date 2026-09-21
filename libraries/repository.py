# ============================================================
# LIBRARIES - REPOSITORY
# ============================================================
#
# Infraestrutura física utilizada pelo domínio global de
# Libraries do DUET.
#
# RESPONSABILIDADES:
#
# - localizar a raiz do RPA-Control-Room;
# - definir o repositório oficial dos artefatos publicados;
# - definir o diretório temporário utilizado durante uploads;
# - centralizar limites relacionados aos arquivos de Libraries.
#
# IMPORTANTE:
#
# Este módulo NÃO contém endpoints FastAPI.
# Este módulo NÃO acessa o banco de dados.
# Este módulo NÃO realiza commit/rollback.
# Este módulo NÃO contém regras de RBAC.
#
# Os services utilizarão estas constantes para trabalhar com
# os snapshots físicos das LibraryVersions.
# ============================================================


import os

from pathlib import Path


# ============================================================
# DIRETÓRIO BASE DO CONTROL ROOM
# ============================================================
#
# __file__:
#
#     RPA-Control-Room/libraries/repository.py
#
# parent.parent:
#
#     RPA-Control-Room/
#
# Dessa forma, mesmo após mover a infraestrutura para dentro
# do pacote libraries/, BASE_DIRECTORY continua apontando para
# exatamente a mesma raiz utilizada pelo api/libraries.py antigo.
# ============================================================

BASE_DIRECTORY = Path(
    os.path.abspath(__file__)
).parent.parent


# ============================================================
# REPOSITÓRIO OFICIAL DAS LIBRARIES
# ============================================================
#
# Estrutura física:
#
# storage/
# └── libraries/
#     └── {library_id}/
#         └── {version}/
#             └── library.zip
#
# Cada library.zip representa o snapshot imutável de uma
# LibraryVersion publicada.
# ============================================================

LIBRARIES_REPOSITORY = (
    BASE_DIRECTORY
    / "storage"
    / "libraries"
)


# Garante que o repositório exista quando o módulo for carregado.
#
# exist_ok=True:
#     não gera erro caso o diretório já exista.
#
# parents=True:
#     cria também os diretórios pais que eventualmente estiverem
#     ausentes.
LIBRARIES_REPOSITORY.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# REPOSITÓRIO TEMPORÁRIO
# ============================================================
#
# Uploads de novas versões são inicialmente processados em:
#
#     storage/libraries/.tmp/
#
# O artefato somente deve chegar ao diretório definitivo depois
# das validações realizadas pelo fluxo de publicação.
# ============================================================

TEMP_REPOSITORY = (
    LIBRARIES_REPOSITORY
    / ".tmp"
)


TEMP_REPOSITORY.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# LIMITE DO ZIP DA LIBRARY
# ============================================================
#
# Limite atual:
#
#     50 MB
#
# Mantemos exatamente o mesmo valor existente antes da
# modularização.
# ============================================================

MAX_LIBRARY_ZIP_SIZE = (
    50
    * 1024
    * 1024
)


# ============================================================
# TAMANHO DOS BLOCOS DE LEITURA
# ============================================================
#
# Arquivos são processados em blocos de 1 MB para evitar que
# operações como cálculo de SHA-256 dependam de carregar o ZIP
# inteiro em memória.
# ============================================================

UPLOAD_CHUNK_SIZE = (
    1024
    * 1024
)


# ============================================================
# LIMITE PARA VISUALIZAÇÃO DE ARQUIVO
# ============================================================
#
# O catálogo permite visualizar arquivos textuais existentes
# dentro de uma LibraryVersion publicada.
#
# Para essa visualização, o limite atual é:
#
#     2 MB por arquivo.
#
# Isso evita carregar arquivos excessivamente grandes apenas
# para exibição no frontend.
# ============================================================

MAX_LIBRARY_VIEW_FILE_SIZE = (
    2
    * 1024
    * 1024
)